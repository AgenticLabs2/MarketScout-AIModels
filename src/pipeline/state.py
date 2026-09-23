"""Typed state shared by every node in the market-research graph."""

import operator
from typing import Annotated, Any
from typing_extensions import TypedDict


class MarketResearchState(TypedDict, total=False):
    company_name: str
    selected_domain: str | None
    company_research_data: dict[str, Any]
    domain_research_data: list[dict[str, Any]]
    market_research_data: dict[str, Any]
    competitive_research_data: list[dict[str, Any]]
    gap_analysis_data: list[dict[str, Any]]
    opportunity_research_data: list[dict[str, Any]]
    report_data: dict[str, Any]
    errors: Annotated[list[str], operator.add]
