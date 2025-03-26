from __future__ import annotations
import os
import sys

sys.path.insert(0, os.environ.get('APP_DIR', ''))

from typing import Union, List
from typing_extensions import Literal
from abc import ABC, abstractmethod
from flask import current_app

from pydantic import BaseModel
import yaml
from hugface import HugFace_Model, ModelType

def init_aioner_model():
    config_path = os.environ['CONFIG_FILE']
    with open(config_path) as file:
        config = yaml.safe_load(file)

    model = HugFace_Model(
        checkpoint_path=config["models"]["aioner"]["checkpoint"],
        lowercase=config["models"]["aioner"]["lowercase"],
        model_type=ModelType(config["models"]["aioner"]["model_type"])
    )
    model.load_model(config["models"]["aioner"]["path"])
    return model


class ProcessModel(BaseModel):
    entries: List[str]
    model_type: Literal["aioner", "bionlp", "jnlpba"]

init_aioner_model()
