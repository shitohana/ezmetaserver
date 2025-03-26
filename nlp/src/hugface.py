from __future__ import annotations
import os
import sys

sys.path.insert(0, os.environ.get('APP_DIR', ''))


import itertools
from pathlib import Path
import re
from enum import Enum
from collections import defaultdict, namedtuple

import numpy as np
import stanza
import tensorflow as tf
from transformers import TFAutoModel # type: ignore
from transformers.models.auto.tokenization_auto import AutoTokenizer
from tensorflow.keras.layers import Input, TimeDistributed, Dropout, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers.schedules import LearningRateSchedule
from tensorflow.keras.preprocessing.sequence import pad_sequences

from tf_crf2 import CRF


def extract_lemma(word):
    try:
        if word.lemma is not None and len(str(word.lemma)) > 0:
            return str(word.lemma)
        else:
            raise KeyError
    except:
        return str(word.text)


class ModelType(Enum):
    SOFTMAX = 1
    CRF     = 2


class AioLabel(Enum):
    UNDEFINED  =  0
    CELLLINE_O =  1
    SPECIES_O  =  2
    VARIANT_O  =  3
    CHEMICAL_O =  4
    GENE_O     =  5
    DISEASE_O  =  6
    CELLLINE_B =  7
    CELLLINE_I =  8
    SPECIES_B  =  9
    SPECIES_I  = 10
    VARIANT_B  = 11
    VARIANT_I  = 12
    CHEMICAL_B = 13
    CHEMICAL_I = 14
    GENE_B     = 15
    GENE_I     = 16
    DISEASE_B  = 17
    DISEASE_I  = 18

    @property
    def label_name(self):
        if self != AioLabel.UNDEFINED:
            return self.name[:-2]
        else:
            return ""
    @property
    def label_type(self):
        if self != AioLabel.UNDEFINED:
            return self.name[-1]
        else:
            return ""


WordMap = namedtuple("WordMap", ["token", "index"])


class LRSchedule_LINEAR(LearningRateSchedule):
    def __init__(
        self,
        init_lr=5e-5,
        init_warmup_lr=0.0,
        final_lr=5e-7,
        warmup_steps=0,
        decay_steps=0,
    ):
        super().__init__()
        self.init_lr = init_lr
        self.init_warmup_lr=init_warmup_lr
        self.final_lr = final_lr
        self.warmup_steps = warmup_steps
        self.decay_steps = decay_steps

    def __call__(self, step):
        if self.warmup_steps>0:
            warmup_lr = (self.init_lr - self.init_warmup_lr)/self.warmup_steps * step+self.init_warmup_lr
        else:
            warmup_lr = 1000.0
        decay_lr = tf.math.maximum(
            self.final_lr,
            self.init_lr - (step - self.warmup_steps)/self.decay_steps*(self.init_lr - self.final_lr)
        )
        return tf.math.minimum(warmup_lr,decay_lr)


class HugFace_Model():
    def __init__(
        self,
        checkpoint_path: str | Path,
        lowercase: bool,
        model_type: ModelType = ModelType.SOFTMAX
    ):
        self.checkpoint_path = checkpoint_path

        self.tokenizer = AutoTokenizer.from_pretrained(
            checkpoint_path,
            use_fast=True,
            do_lower_case=lowercase
            )
        self.tokenizer.add_tokens(["<Chemical>","</Chemical>","<Disease>","</Disease>","<CellLine>","</CellLine>","<Gene>","</Gene>","<Species>","</Species>","<Variant>","</Variant>","<ALL>","</ALL>"])

        self.maxlen = 256
        self.nlp = stanza.Pipeline(lang='en', processors={'tokenize': 'spacy'}, package='None')

        self.encoder = self.init_encoder()
        self.model_type = model_type
        self.model = self.init_model(model_type)

    def init_encoder(self):
        plm_model = TFAutoModel.from_pretrained(self.checkpoint_path, from_pt=True) # type: ignore
        plm_model.resize_token_embeddings(len(self.tokenizer))

        input_ids      = Input(shape=(self.maxlen,), dtype=tf.int32, name='input_ids')
        token_type_ids = Input(shape=(self.maxlen,), dtype=tf.int32, name='token_type_ids')
        attention_mask = Input(shape=(self.maxlen,), dtype=tf.int32, name='attention_mask')

        output = plm_model(
            input_ids,
            token_type_ids=token_type_ids,
            attention_mask=attention_mask
            )[0]

        encoder = Model(
            inputs=[input_ids, token_type_ids, attention_mask],
            outputs=output,
            name='hugface_encoder'
            )
        encoder.summary()

        return encoder

    def init_model(self, model_type: ModelType):
        x1_in = Input(shape=(self.maxlen,),dtype=tf.int32)
        x2_in = Input(shape=(self.maxlen,),dtype=tf.int32)
        x3_in = Input(shape=(self.maxlen,),dtype=tf.int32)
        features = self.encoder([x1_in,x2_in,x3_in])
        features = TimeDistributed(Dense(128, activation='relu'), name='dense2')(features)
        features= Dropout(0.1)(features)

        if model_type == ModelType.SOFTMAX:
            output = TimeDistributed(
                Dense(
                    len(AioLabel),
                    activation='softmax'
                    ),
                name='softmax')(features)

            lr_schedule = LRSchedule_LINEAR(
                init_lr=2e-5,
                init_warmup_lr=1e-7,
                final_lr=5e-6,
                warmup_steps=0,
                decay_steps=400
                )
            optimizer = Adam(learning_rate=lr_schedule) # type: ignore

            model = Model(
                inputs=[x1_in, x2_in, x3_in],
                outputs=output,
                name="hugface_softmax"
                )
            model.compile(
                optimizer=optimizer, # type: ignore
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'],
            )
            model.summary()
            return model

        else:
            crf = CRF(
                len(AioLabel),
                name='crf_layer'
                )
            output = crf(features)

            lr_schedule=LRSchedule_LINEAR(
            init_lr=2e-5,
            init_warmup_lr=0.0,
            final_lr=5e-6,
            warmup_steps=0,
            decay_steps=400)
            optimizer = Adam(learning_rate = lr_schedule) # type: ignore

            model = Model(
                inputs=[x1_in, x2_in, x3_in],
                outputs=output,
                name="hugface_crf"
                )
            model.compile(
                optimizer=optimizer, # type: ignore
                loss=crf.get_loss,
                metrics=['accuracy'],
            )
            model.summary()

            return model

    def load_model(self, model_file):
        self.model.load_weights(model_file)
        self.model.summary()

    def tokenize(self, text: str):
        text = text.strip()
        text = re.sub(r"([\=\/\(\)\<\>\+\-\_])", " \\1 ", text)
        text = re.sub(r"[ ]+", " ", text)

        doc_stanza = self.nlp(text)
        return [
            [extract_lemma(word) for word in sentence.words]
            for sentence in doc_stanza.sentences
        ]

    def prepare_data(self, tokenized, word_max_len: int = 256):
        def tokenizer_func(sentence):
            tokenizer_res = self.tokenizer(
                sentence,
                max_length=word_max_len,
                truncation=True,
                is_split_into_words=True
            )

            word_indexes = tokenizer_res.word_ids(batch_index=0)

            # IDK what is this part, just copied
            first_index, ori_i = -1, 0
            new_token_map = []
            for i, word_index in enumerate(word_indexes):
                if word_index is not None:
                    first_index = word_index

                    if first_index == ori_i:
                        new_token_map.append(WordMap(sentence[word_index], i))
                        ori_i += 1

            return (
                tokenizer_res["input_ids"],
                tokenizer_res["token_type_ids"],
                tokenizer_res["attention_mask"],
                new_token_map
                )

        input_ids,\
        token_type_ids,\
        attention_mask,\
        word_index     = list(zip(*(tokenizer_func(sentence) for sentence in tokenized)))

        input_ids      = pad_sequences(input_ids, word_max_len, value=0, padding='post',truncating='post')
        token_type_ids = pad_sequences(token_type_ids, word_max_len, value=0, padding='post',truncating='post')
        attention_mask = pad_sequences(attention_mask, word_max_len, value=0, padding='post',truncating='post')


        return (input_ids, token_type_ids, attention_mask), word_index

    def process_text(
        self,
        text: str,
        word_max_len: int = 256,
        batch_size: int = 64,
        ommit_undefined: bool = True
        ):
        tokenized = self.tokenize(text)
        input_data, word_index = self.prepare_data(tokenized, word_max_len)
        processed = self.model.predict(input_data, batch_size=batch_size)

        output = []
        for i in range(len(word_index)):
            sentence = []
            for j in range(len(word_index[i])):
                if self.model_type == ModelType.SOFTMAX:
                    condition = processed[i][j][-1] < len(word_index[i])
                else:
                    condition = True
                if condition:
                    if self.model_type == ModelType.SOFTMAX:
                        label_id  = np.argmax(processed[i][word_index[i][j].index])
                    else:
                        label_id  = processed[i][word_index[i][j].index]
                    label_tag = AioLabel(label_id)
                else:
                    label_tag = AioLabel.UNDEFINED
                if word_index[i][j] is not None:
                    if not (ommit_undefined and label_tag == AioLabel.UNDEFINED):
                        sentence.append((word_index[i][j].token, label_tag))
            output.append(sentence)

        return output

    def assemble_output(self, output: list):
        last_label = AioLabel.UNDEFINED
        last_word = ""
        data = defaultdict(set)

        for token, label in itertools.chain(*output):
            if label.label_type == "B":
                if last_word:
                    data[last_label.label_name] |= {last_word}
                last_word = token
            elif label.label_type == "I":
                if last_word and last_label.label_name == label.label_name:
                    last_word += ' ' + token
                else:
                    last_word = token
            else:
                last_word = ""

            last_label = label

        if last_word:
            data[last_label.label_name] |= {last_word}

        data = {key: list(value) for key, value in data.items()}
        return data


if __name__ == "__main__":
    model = HugFace_Model(
        checkpoint_path="/nfs/home/kyuditski/aioiner/AIONER/pretrained_models/bioformer-cased-v1.0/",
        lowercase=False,
        model_type=ModelType.SOFTMAX
    )
    model.load_model("/nfs/home/kyuditski/aioiner/AIONER/pretrained_models/AIONER/Bioformer-softmax-AIONER.h5")
    test = model.process_text("PRMT5 deficiency enforces the transcriptional and epigenetic programs of Klrg1+CD8+ terminal effector T cells")
    model.assemble_output(test)
    pass
