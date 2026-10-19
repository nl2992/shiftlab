from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paper: Literal[1, 2, 3] = 1
    seeds: list[int] = Field(default_factory=lambda: [11, 22, 33], min_length=1)
    n: int = Field(default=1200, ge=100)
    train_end: int = Field(default=200, ge=20)
    calibration_end: int = Field(default=350, ge=40)
    change_at: int = 650
    shift: Literal["none", "benign", "concept", "variance"] = "concept"
    strength: float = Field(default=1.5, ge=0)
    delay: int = Field(default=3, ge=0)
    missing: float = Field(default=0, ge=0, lt=1)
    window: int = Field(default=80, ge=10)
    alpha: float = Field(default=0.1, gt=0, lt=1)
    threshold: float = Field(default=20, gt=0)
    retrain_cost: float = Field(default=10, ge=0)
    budget: int = Field(default=5, ge=0)
    period: int = Field(default=150, ge=1)
    output: str = "outputs"
    device: Literal["cpu"] = "cpu"

    @model_validator(mode="after")
    def chronology(self):
        if not self.train_end < self.calibration_end < self.change_at < self.n:
            raise ValueError("require train < calibration < change < n")
        if self.window > self.calibration_end - self.train_end:
            raise ValueError("window exceeds calibration samples")
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("data seeds must be unique")
        return self


def load_config(path: str | Path) -> Config:
    return Config.model_validate(yaml.safe_load(Path(path).read_text()))
