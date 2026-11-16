"""LabAgent: mini's DefaultAgent with the mini-lab hooks. With no modules it behaves exactly like DefaultAgent."""

from dataclasses import asdict, is_dataclass

from minilab.core.context import Context
from minilab.core.module import Module, call, check_modules
from minisweagent.agents.default import DefaultAgent
from minisweagent.exceptions import Submitted


class LabAgent(DefaultAgent):
    def __init__(self, *args, modules: list[Module] | None = None, ctx: Context | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.modules = modules or []
        self.ctx = ctx or Context(task="")
        check_modules(self.modules)

    def hook(self, name: str, *args) -> list:
        self.ctx.step = self.n_calls
        return call(self.modules, self.ctx, name, *args)

    def query(self) -> dict:
        for module, messages in zip(self.modules, self.hook("before_query", self)):
            for message in messages:
                self.ctx.log(module.name, injected=message.get("content"))
                self.add_messages({**message, "extra": {**message.get("extra", {}), "minilab": module.name}})
        return super().query()

    def execute_actions(self, message: dict) -> list[dict]:
        outputs = []
        for action in message.get("extra", {}).get("actions", []):
            try:
                output = self.env.execute(action)
            except Submitted as e:
                patch = e.messages[0]["extra"]["submission"]
                if (feedback := next((f for f in self.hook("on_submit", patch) if f is not None), None)) is None:
                    raise
                self.ctx.log("agent", rejected_patch=patch, feedback=feedback)
                outputs.append({"output": feedback, "returncode": 1, "exception_info": "Submission rejected"})
                break
            self.hook("on_execute", action, output)
            transformed, self.ctx.hook = output, "transform_output"
            for m in self.modules:
                transformed = m.transform_output(action, transformed, self.ctx)
            if transformed is not output:
                self.ctx.log("agent", raw_output=output, transformed_output=transformed)
            outputs.append(transformed)
        return self.add_messages(*self.model.format_observation_messages(message, outputs, self.get_template_vars()))

    def serialize(self, *extra_dicts) -> dict:
        modules = [{"name": m.name, **(asdict(m) if is_dataclass(m) else {})} for m in self.modules]
        return super().serialize({"info": {"minilab": {"modules": modules, **self.ctx.serialize()}}}, *extra_dicts)
