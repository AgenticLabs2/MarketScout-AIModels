"""Citation verification tool implemented with the LangGraph agent runtime."""

from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import run_structured_agent


class Citation(BaseModel):
    title: str
    url: str
    snippet: str


class CitationResult(BaseModel):
    claim_valid: bool
    citations: list[Citation] = Field(default_factory=list)


SYSTEM_PROMPT = """
You verify factual claims. Compare the supplied claim with its context and use the
search tool when external verification is necessary. Return whether the claim is
supported and include only real source URLs and concise supporting or refuting
snippets.
"""


def citation_agent(claim: str, context: str) -> dict[str, Any]:
    """Verify a claim and return structured supporting or refuting citations."""
    try:
        data, _ = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Claim: {claim}\n\nContext: {context}",
            response_model=CitationResult,
            use_search=True,
        )
        return data
    except Exception as exc:
        return {"claim_valid": False, "citations": [], "error": str(exc)}


citation_agent.__name__ = "claim_context_based_citation_tool"
citation_agent.__doc__ = "Verify a claim and return formatted source citations."
citation_agent.connection_timeout = 60
citation_agent.invocation_timeout = 60
