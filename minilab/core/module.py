"""Module base class with the mini-lab hooks, module loading, and prompt sections."""

import importlib
import re
from dataclasses import dataclass

from minilab.core.context import Context

ORDER = ["requirements", "planning", "testing", "review"]
SINGLE = ["transform_output", "on_submit", "select_attempt"]


SECTION_NAME = re.compile(r"[\w .,:()/&+-]+")


@dataclass
class Add:
    """A new `## <name>` section, placed before the section named in `before` (default: end of the instructions)."""

    text: str
    before: str | None = None


@dataclass
class Replace:
    text: str


class Module:
    """Base class of research modules. Subclasses are dataclasses (their fields are the module's parameters)
    and override only the hooks they need. `setup_env` returns a report of what it added (logged),
    `on_submit` returns None to accept or feedback text to reject."""

    name = "base"
    category = ""

    def before_run(self, ctx: Context) -> None: ...
    def setup_env(self, env, ctx: Context) -> dict | str | None: ...
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


def section_pattern(name: str) -> str:
    return rf"^## {re.escape(name)}\n.*?(?=^## |^</instructions>|\Z)"


def apply_sections(template: str, sections: dict[str, Add | Replace]) -> str:
    """Replace or add `## <name>` sections of an instance template. Other text stays byte for byte.
    The section text is not pasted in: a placeholder renders it from the `minilab_sections` template
    variable, so text containing Jinja syntax arrives verbatim (see `section_values`)."""
    for name, section in sections.items():
        if not SECTION_NAME.fullmatch(name):
            raise ValueError(f"Invalid section name {name!r}")
        block = f'## {name}\n{{{{ minilab_sections["{name}"] }}}}\n\n'
        if isinstance(section, Replace):
            template, n = re.subn(section_pattern(name), lambda _: block, template, count=1, flags=re.S | re.M)
            if not n:
                raise KeyError(f"No section '## {name}' in the instance template")
        elif section.before is not None:
            if not (match := re.search(rf"^## {re.escape(section.before)}\n", template, flags=re.M)):
                raise KeyError(f"No section '## {section.before}' to place '## {name}' before")
            template = template[: match.start()] + block + template[match.start() :]
        elif "</instructions>" in template:
            template = template.replace("</instructions>", block + "</instructions>", 1)
        else:
            template += f"\n{block}"
    return template


def section_values(sections: dict[str, Add | Replace]) -> dict[str, str]:
    return {name: section.text.rstrip() for name, section in sections.items()}
