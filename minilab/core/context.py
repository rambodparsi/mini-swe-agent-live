"""Shared context of one attempt: task, artifacts with provenance, events and extra cost."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Artifact:
    value: Any
    producer: str
    version: int
    hook: str
    step: int


@dataclass
class Context:
    task: str
    instance: dict = field(default_factory=dict)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    costs: dict[str, float] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=dict)
    helper_model: dict = field(default_factory=dict)
    hook: str = ""
    step: int = 0

    def put(self, name: str, value: Any, producer: str) -> None:
        version = self.artifacts[name].version + 1 if name in self.artifacts else 1
        self.artifacts[name] = Artifact(value, producer, version, self.hook, self.step)

    def get(self, name: str, default: Any = None) -> Any:
        return self.artifacts[name].value if name in self.artifacts else default

    def log(self, producer: str, **data) -> None:
        self.events.append({"producer": producer, "hook": self.hook, "step": self.step, **data})

    def add_cost(self, producer: str, cost: float, tokens: int = 0) -> None:
        self.costs[producer] = self.costs.get(producer, 0.0) + cost
        self.tokens[producer] = self.tokens.get(producer, 0) + tokens

    def serialize(self) -> dict:
        return {
            "artifacts": {name: asdict(a) for name, a in self.artifacts.items()},
            "events": self.events,
            "costs": self.costs,
            "tokens": self.tokens,
        }
