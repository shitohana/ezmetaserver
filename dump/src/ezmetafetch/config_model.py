from pathlib import Path

from pydantic import BaseModel, Field, computed_field
import yaml


class HttpConf(BaseModel):
    min_timeout: int = Field(default=1)
    max_timeout: int = Field(default=2)
    retry_on: list[int] = Field(default_factory=lambda: [429])
    api_key: str | None = Field(default=None)
    debug: bool = Field(default=False)
    
    @computed_field(return_type=int)
    @property
    def rate_limit(self):
        return 3 if self.api_key is None else 10

class FetchConf(BaseModel):
    max_retries: int = Field(default=5)
    ids_per_request: int = Field(default=100)


class SearchConf(FetchConf):
    terms_per_request: int = Field(default=10)


class ConfigModel(BaseModel):
    http: HttpConf = Field(default_factory=HttpConf)
    search: SearchConf = Field(default_factory=SearchConf)
    fetch: FetchConf = Field(default_factory=FetchConf)

    @classmethod
    def from_json(cls, path: str | Path):
        assert (file := Path(path)).exists(), FileNotFoundError
        return cls.model_validate_json(file.read_text())
    
    @classmethod
    def from_yaml(cls, path: str | Path):
        assert (file := Path(path)).exists(), FileNotFoundError
        with file.open("r") as file:
            data = yaml.safe_load(file)
        return cls(**data)