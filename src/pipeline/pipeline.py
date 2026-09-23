"""LangGraph orchestration for the MarketScout research pipeline."""

import base64
from functools import lru_cache
from typing import Any, Callable
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from src.agents.company_research_agent import run_company_research_agent
from src.agents.competitive_landscape_agent import run_competitive_landscape_agent
from src.agents.industry_analysis_agent import run_industry_analysis_agent
from src.agents.market_data_agent import run_market_data_agent
from src.agents.market_gap_agent import run_market_gap_analysis_agent
from src.agents.opportunity_agent import run_opportunity_agent
from src.agents.report_synthesis_agent import run_report_synthesis_agent
from src.pipeline.state import MarketResearchState


CHECKPOINTER = InMemorySaver()


def _agent_data(name: str, runner: Callable[..., dict[str, Any]], value: Any) -> tuple[Any, list[str]]:
    try:
        result = runner(value)
    except Exception as exc:
        return None, [f"{name}: {exc}"]
    if not result.get("success"):
        return None, [f"{name}: {result.get('error', 'unknown error')}"]
    return result.get("data"), []


def company_research_node(state: MarketResearchState) -> dict[str, Any]:
    data, errors = _agent_data("Company research", run_company_research_agent, state["company_name"])
    return {"company_research_data": data, "errors": errors}


def industry_analysis_node(state: MarketResearchState) -> dict[str, Any]:
    data, errors = _agent_data(
        "Industry analysis", run_industry_analysis_agent, state.get("company_research_data")
    )
    return {"domain_research_data": data, "errors": errors}


def domain_selection_node(state: MarketResearchState) -> dict[str, Any]:
    opportunities = state.get("domain_research_data") or []
    if not opportunities:
        return {"errors": ["Domain selection: no industry opportunities were produced"]}

    selected = state.get("selected_domain")
    if not selected:
        selected = interrupt(
            {
                "kind": "domain_selection",
                "message": "Select a domain to continue the market research pipeline.",
                "options": opportunities,
            }
        )
    if isinstance(selected, int):
        if selected < 1 or selected > len(opportunities):
            return {"errors": ["Domain selection: selected index is out of range"]}
        selected = opportunities[selected - 1]["domain"]
    if not isinstance(selected, str) or not selected.strip():
        return {"errors": ["Domain selection: a non-empty domain is required"]}
    return {"selected_domain": selected.strip(), "errors": []}


def market_data_node(state: MarketResearchState) -> dict[str, Any]:
    data, errors = _agent_data("Market data", run_market_data_agent, state.get("selected_domain"))
    return {"market_research_data": data, "errors": errors}


def competitive_landscape_node(state: MarketResearchState) -> dict[str, Any]:
    domain = state.get("selected_domain") or ""
    opportunity = next(
        (item for item in state.get("domain_research_data", []) if item.get("domain") == domain),
        {"domain": domain, "score": 0.0, "rationale": "User-selected domain", "sources": []},
    )
    data, errors = _agent_data(
        "Competitive landscape", run_competitive_landscape_agent, opportunity
    )
    return {"competitive_research_data": data, "errors": errors}


def market_gap_node(state: MarketResearchState) -> dict[str, Any]:
    if state.get("errors"):
        return {}
    payload = {
        "company_profile": state.get("company_research_data"),
        "competitor_list": state.get("competitive_research_data"),
        "market_stats": state.get("market_research_data"),
    }
    data, errors = _agent_data("Market gap analysis", run_market_gap_analysis_agent, payload)
    return {"gap_analysis_data": data, "errors": errors}


def opportunity_node(state: MarketResearchState) -> dict[str, Any]:
    if state.get("errors"):
        return {}
    data, errors = _agent_data(
        "Opportunity analysis", run_opportunity_agent, state.get("gap_analysis_data")
    )
    return {"opportunity_research_data": data, "errors": errors}


def report_synthesis_node(state: MarketResearchState) -> dict[str, Any]:
    if state.get("errors"):
        return {}
    payload = {
        "company_research_data": state.get("company_research_data"),
        "domain_research_data": state.get("domain_research_data"),
        "market_research_data": state.get("market_research_data"),
        "competitive_research_data": state.get("competitive_research_data"),
        "gap_analysis_data": state.get("gap_analysis_data"),
        "opportunity_research_data": state.get("opportunity_research_data"),
    }
    data, errors = _agent_data("Report synthesis", run_report_synthesis_agent, payload)
    return {"report_data": data, "errors": errors}


@lru_cache(maxsize=1)
def build_market_research_graph():
    builder = StateGraph(MarketResearchState)
    builder.add_node("company_research", company_research_node)
    builder.add_node("industry_analysis", industry_analysis_node)
    builder.add_node("select_domain", domain_selection_node)
    builder.add_node("market_data", market_data_node)
    builder.add_node("competitive_landscape", competitive_landscape_node)
    builder.add_node("market_gap_analysis", market_gap_node)
    builder.add_node("opportunity_analysis", opportunity_node)
    builder.add_node("report_synthesis", report_synthesis_node)

    builder.add_edge(START, "company_research")
    builder.add_edge("company_research", "industry_analysis")
    builder.add_edge("industry_analysis", "select_domain")
    builder.add_edge("select_domain", "market_data")
    builder.add_edge("select_domain", "competitive_landscape")
    builder.add_edge(["market_data", "competitive_landscape"], "market_gap_analysis")
    builder.add_edge("market_gap_analysis", "opportunity_analysis")
    builder.add_edge("opportunity_analysis", "report_synthesis")
    builder.add_edge("report_synthesis", END)
    return builder.compile(checkpointer=CHECKPOINTER)


market_research_graph = build_market_research_graph()


def _serialize_state(state: dict[str, Any], thread_id: str) -> dict[str, Any]:
    interrupts = state.get("__interrupt__", ())
    if interrupts:
        return {
            "success": True,
            "status": "interrupted",
            "thread_id": thread_id,
            "interrupt": interrupts[0].value,
        }

    public_state = {key: value for key, value in state.items() if not key.startswith("__")}
    report = public_state.get("report_data")
    if report and isinstance(report.get("pdf_content"), bytes):
        report = dict(report)
        report["pdf_content"] = base64.b64encode(report["pdf_content"]).decode("ascii")
        report["pdf_content_encoding"] = "base64"
        public_state["report_data"] = report
    errors = public_state.get("errors", [])
    return {
        "success": not errors,
        "status": "failed" if errors else "completed",
        "thread_id": thread_id,
        "data": public_state,
        "errors": errors,
    }


def run_linear_pipeline(
    company_name: str,
    selected_domain: str | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Start the graph, returning an interrupt when domain input is required."""
    active_thread = thread_id or str(uuid4())
    config = {"configurable": {"thread_id": active_thread}}
    initial: MarketResearchState = {
        "company_name": company_name,
        "selected_domain": selected_domain,
        "errors": [],
    }
    result = market_research_graph.invoke(initial, config=config)
    return _serialize_state(result, active_thread)


def resume_pipeline(thread_id: str, selected_domain: str | int) -> dict[str, Any]:
    """Resume a graph paused at the domain-selection interrupt."""
    config = {"configurable": {"thread_id": thread_id}}
    result = market_research_graph.invoke(Command(resume=selected_domain), config=config)
    return _serialize_state(result, thread_id)


def run_pipeline(company_name: str, selected_domain: str | None = None) -> dict[str, Any]:
    """Backward-compatible alias for the LangGraph pipeline entry point."""
    return run_linear_pipeline(company_name, selected_domain)
