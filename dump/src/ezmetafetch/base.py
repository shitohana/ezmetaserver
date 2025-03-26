from functools import cached_property
from logging import DEBUG, INFO, Logger
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .config_model import ConfigModel


class Base(BaseModel):
    terms_file: Path | None = Field(default=None)
    ids_file: Path | None = Field(default=None)
    db: str = Field(default="sra")
    output: Path = Field(default_factory=lambda: Path.cwd())
    config: ConfigModel = Field(default_factory=ConfigModel)

    @field_validator("output")
    @classmethod
    def init_output(cls, path: Path):
        if not path.exists():
            try:
                path.mkdir()
            except Exception as e:
                raise(e)
        return path

    @cached_property
    def logger(self) -> Logger:
        return Logger("EzMetaFetch", level=DEBUG if self.config.http.debug else INFO)

    @cached_property
    def terms_list(self):
        if self.terms_file is not None:
            return self.terms_file.read_text().strip().split("\n")
        else:
            return []

    @cached_property
    def ids_list(self):
        if self.ids_file is not None:
            return list(map(int, self.ids_file.read_text().strip().split("\n")))
        else:
            return []
