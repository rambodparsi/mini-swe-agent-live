"""Module base class with the mini-lab hooks, module loading, and prompt sections."""

import importlib
import re
from dataclasses import dataclass

from minilab.core.context import Context

ORDER = ["requirements", "planning", "testing", "review"]
SINGLE = ["transform_output", "on_submit", "select_attempt"]


@dataclass
class Add:
    text: str


@dataclass
class Replace:
    text: str


class Module:
    """Base class of research modules. Subclasses are dataclasses (their fields are the module's parameters)
    and override only the hooks they need. `on_submit` returns None to accept or feedback text to reject."""

    name = "base"
    category = ""

    def before_run(self, ctx: Context) -> None: ...
    def setup_env(self, env, ctx: Context) -> None: ...
    def prompt_sections(self, ctx: Context) -> dict[str, Add | Replace]:
        return {}

    def before_query(self, agent, ctx: Context) -> list[dict]:
        return []

    def on_execute(self, action: dict, output: dict, ctx: Context) -> None: ...
    def transform_output(self, action: dict, output: dict, ctx: Context) -> dict:
        return output

    def on_submit(self, patch: str, ctx: Context) -> str | None:
        return None

    def after_run(self, result: dict, ctx: Context) -> dict:
        return result

    def select_attempt(self, attempts: list[dict], ctx: Context) -> dict:
        return attempts[0]


def overrides(module: Module, hook: str) -> bool:
    return getattr(type(module), hook) is not getattr(Module, hook)


def check_modules(modules: list[Module]) -> None:
    for hook in SINGLE:
        if len(users := [m.name for m in modules if overrides(m, hook)]) > 1:
            raise ValueError(f"Only one module may implement {hook} in an experiment, got {users}")


def call(modules: list[Module], ctx: Context, hook: str, *args) -> list:
    ctx.hook = hook
    return [getattr(m, hook)(*args, ctx) for m in modules]


def load_modules(spec: dict[str, dict]) -> list[Module]:
    from minilab.modules import MODULES

    modules = []
    for name, params in spec.items():
        path = MODULES.get(name, name)
        if "." not in path:
            raise KeyError(f"Unknown module {name!r}; known: {sorted(MODULES)}")
        module_path, cls = path.rsplit(".", 1)
        modules.append(getattr(importlib.import_module(module_path), cls)(**(params or {})))
    check_modules(modules)
    return sorted(modules, key=lambda m: ORDER.index(m.category) if m.category in ORDER else len(ORDER))


def apply_sections(template: str, sections: dict[str, Add | Replace]) -> str:
    """Replace or add `## <name>` sections of an instance template. Other text stays byte for byte."""
    for name, section in sections.items():
        if isinstance(section, Replace):
            pattern = rf"^## {re.escape(name)}\n.*?(?=^## |^</instructions>|\Z)"
            new = f"## {name}\n{section.text.rstrip()}\n\n"
            template, n = re.subn(pattern, lambda _: new, template, count=1, flags=re.S | re.M)
            if not n:
                raise KeyError(f"No section '## {name}' in the instance template")
        elif "</instructions>" in template:
            template = template.replace("</instructions>", f"## {name}\n{section.text.rstrip()}\n\n</instructions>", 1)
        else:
            template += f"\n## {name}\n{section.text.rstrip()}\n"
    return template
