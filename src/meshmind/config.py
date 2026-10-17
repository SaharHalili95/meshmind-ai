"""Typed configuration containers and YAML loading."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TopologyConfig:
    name: str = "abilene"
    capacity_scale: float = 1.0
    max_utilization: float = 1.5

    def __post_init__(self) -> None:
        if self.capacity_scale <= 0:
            raise ValueError("capacity_scale must be > 0")
        if self.max_utilization < 1.0:
            raise ValueError("max_utilization must be >= 1.0")


@dataclass(frozen=True)
class TrafficConfig:
    profile: str = "high"
    flows_per_episode: int = 25

    def __post_init__(self) -> None:
        if self.flows_per_episode < 1:
            raise ValueError("flows_per_episode must be >= 1")


@dataclass(frozen=True)
class EnvironmentConfig:
    max_steps: int = 20
    load_decay: float = 0.85
    invalid_action_penalty: float = -100.0
    loop_penalty: float = -100.0
    max_steps_penalty: float = -100.0
    latency_weight: float = 0.1
    delivery_reward: float = 10.0
    drop_penalty: float = 50.0

    def __post_init__(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        if not 0.0 <= self.load_decay <= 1.0:
            raise ValueError("load_decay must be in [0, 1]")


@dataclass(frozen=True)
class AgentConfig:
    alpha: float = 0.1
    gamma: float = 0.95
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.998

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        if not 0.0 <= self.gamma <= 1.0:
            raise ValueError("gamma must be in [0, 1]")
        if not 0.0 <= self.epsilon_end <= self.epsilon_start <= 1.0:
            raise ValueError("require 0 <= epsilon_end <= epsilon_start <= 1")
        if not 0.0 < self.epsilon_decay <= 1.0:
            raise ValueError("epsilon_decay must be in (0, 1]")


@dataclass(frozen=True)
class ExperimentConfig:
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    traffic: TrafficConfig = field(default_factory=TrafficConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    seeds: tuple[int, ...] = (42, 100, 2026, 7, 13, 21, 314, 777, 1234, 9001)
    train_episodes: int = 3000
    eval_episodes: int = 100
    results_dir: str = "results"

    def __post_init__(self) -> None:
        if not self.seeds:
            raise ValueError("at least one seed is required")
        if self.train_episodes < 1 or self.eval_episodes < 1:
            raise ValueError("train_episodes and eval_episodes must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["seeds"] = list(self.seeds)
        return data


_SECTIONS: dict[str, type] = {
    "topology": TopologyConfig,
    "traffic": TrafficConfig,
    "environment": EnvironmentConfig,
    "agent": AgentConfig,
}


def _build_section(cls: type, raw: dict[str, Any] | None) -> Any:
    raw = raw or {}
    allowed = {f.name for f in fields(cls)}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f"unknown keys for {cls.__name__}: {sorted(unknown)}")
    return cls(**raw)


def config_from_dict(raw: dict[str, Any]) -> ExperimentConfig:
    sections = {name: _build_section(cls, raw.get(name)) for name, cls in _SECTIONS.items()}
    experiment = dict(raw.get("experiment") or {})
    allowed = {"seeds", "train_episodes", "eval_episodes", "results_dir"}
    unknown = set(experiment) - allowed
    if unknown:
        raise ValueError(f"unknown keys for experiment: {sorted(unknown)}")
    if "seeds" in experiment:
        experiment["seeds"] = tuple(int(s) for s in experiment["seeds"])
    unknown_sections = set(raw) - set(_SECTIONS) - {"experiment"}
    if unknown_sections:
        raise ValueError(f"unknown config sections: {sorted(unknown_sections)}")
    return ExperimentConfig(**sections, **experiment)


def load_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"config file {path} must contain a mapping")
    return config_from_dict(raw)
