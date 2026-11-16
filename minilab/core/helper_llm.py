"""Extra LLM calls made by modules (e.g. an SRS writer or a reviewer), with cost and tokens recorded per module."""

import litellm

from minilab.core.context import Context
from minisweagent.models import get_model
from minisweagent.models.litellm_model import LitellmModel

HELPER_MODEL_CLASS = "minilab.core.helper_llm.HelperModel"


class HelperModel(LitellmModel):
    """mini's LiteLLM model without the bash tool, for free-form answers. Keeps mini's retries and cost tracking."""

    def _query(self, messages: list[dict[str, str]], **kwargs):
        model_kwargs = {k: v for k, v in (self.config.model_kwargs | kwargs).items() if k != "parallel_tool_calls"}
        return litellm.completion(model=self.config.model_name, messages=messages, **model_kwargs)

    def _parse_actions(self, response) -> list[dict]:
        return []


def ask(ctx: Context, producer: str, prompt: str) -> str:
    """Send one prompt to the helper model (`minilab.helper_model` in the config) and return its answer."""
    model = get_model(config={"model_class": HELPER_MODEL_CLASS, **ctx.helper_model})
    response = model.query([{"role": "user", "content": prompt}])
    usage = (response.get("extra", {}).get("response") or {}).get("usage") or {}
    tokens = usage.get("total_tokens", 0)
    ctx.add_cost(producer, response.get("extra", {}).get("cost", 0.0), tokens)
    answer = response.get("content") or ""
    ctx.log(
        producer, helper_call={"model": model.config.model_name, "prompt": prompt, "answer": answer, "tokens": tokens}
    )
    return answer
