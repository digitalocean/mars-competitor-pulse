"""Compiled Competitor Pulse graph (MARS / LangGraph Agent Server export)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from competitor_pulse.nodes import (
    act,
    analyze,
    ask,
    draft,
    gather,
    intake,
    plan,
    report,
    should_ask,
)
from competitor_pulse.state import PulseState


def build_graph() -> StateGraph:
    """Construct the uncompiled StateGraph."""
    builder: StateGraph = StateGraph(PulseState)
    builder.add_node("intake", intake)
    builder.add_node("plan", plan)
    builder.add_node("gather", gather)
    builder.add_node("analyze", analyze)
    builder.add_node("draft", draft)
    builder.add_node("ask", ask)
    builder.add_node("act", act)
    builder.add_node("report", report)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "plan")
    builder.add_edge("plan", "gather")
    builder.add_edge("gather", "analyze")
    builder.add_edge("analyze", "draft")
    builder.add_conditional_edges(
        "draft",
        should_ask,
        {"ask": "ask", "report": "report"},
    )
    builder.add_edge("ask", "act")
    builder.add_edge("act", "report")
    builder.add_edge("report", END)
    return builder


def compile_graph(checkpointer: Any = None):
    """Compile with optional checkpointer (required for interrupt resume locally)."""
    builder = build_graph()
    kwargs: dict[str, Any] = {"name": "CompetitorPulse"}
    if checkpointer is not None:
        kwargs["checkpointer"] = checkpointer
    return builder.compile(**kwargs)


# Module-level compiled export for langgraph.json / Agent Server
graph = compile_graph()
