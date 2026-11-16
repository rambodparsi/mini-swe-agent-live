from minilab.core.context import Context
from minilab.core.helper_llm import HelperModel, ask
from minilab.core.runner import helper_model_config
from minisweagent.models.test_models import make_output


def test_ask_records_answer_cost_and_event():
    ctx = Context(
        task="t",
        helper_model={
            "model_class": "minisweagent.models.test_models.DeterministicModel",
            "model_name": "deterministic",
            "outputs": [make_output("first", [], cost=0.25), make_output("second", [], cost=0.5)],
        },
    )
    assert [ask(ctx, "srs", "write it") for _ in range(2)] == ["first", "first"]
    assert (ctx.costs, ctx.tokens) == ({"srs": 0.5}, {"srs": 0})
    assert [e["helper_call"]["answer"] for e in ctx.events] == ["first", "first"]
    assert ctx.events[0]["producer"] == "srs" and ctx.events[0]["helper_call"]["prompt"] == "write it"


def test_helper_model_answers_without_tools_through_litellm():
    ctx = Context(task="t", helper_model={"model_name": "gpt-4o-mini", "model_kwargs": {"mock_response": "an SRS"}})
    assert ask(ctx, "srs", "write it") == "an SRS"
    assert ctx.tokens["srs"] > 0 and ctx.events[0]["helper_call"]["model"] == "gpt-4o-mini"
    assert HelperModel(model_name="x")._parse_actions(None) == []


def test_helper_model_defaults_to_main_model():
    main = {
        "model": {"model_name": "openai/gpt-5.1", "model_kwargs": {"reasoning_effort": "medium"}, "model_class": "x"}
    }
    assert helper_model_config(main) == {"model_name": "openai/gpt-5.1", "model_kwargs": {"reasoning_effort": "medium"}}
    assert helper_model_config({**main, "minilab": {"helper_model": {"model_name": "y"}}}) == {"model_name": "y"}
