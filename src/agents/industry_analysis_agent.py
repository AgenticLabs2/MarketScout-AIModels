import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import RootModel
from src.agents.base import run_structured_agent
from src.utils.models import IndustryOpportunity

# Load environment variables from .env file
load_dotenv()
class IndustryOpportunityList(RootModel[List[IndustryOpportunity]]):
    pass


SYSTEM_PROMPT = """
You are IndustryAnalysisAgent, an AI expert in market strategy and domain expansion.

Your task is to analyze a structured company profile and suggest a ranked list of promising industries/domains the company could expand into.

Guidelines:
1. Consider current industry, product strengths, technological capabilities, market position, and geography.
2. Rank at least 3–5 high-potential domains. Assign each a `score` (0.0–1.0) representing strategic fit and opportunity.
3. For each domain, include a 1–2 sentence `rationale` explaining why it's a good fit.
4. Use any provided `sources` to support or reference your rationale if applicable.
5. Return only a JSON list in the following format:

[
  { "domain": "Retail Tech", "score": 0.92, "rationale": "Company’s strong e-commerce platform could pivot to retail analytics.", "sources": ["https://example.com"] },
  ...
]

Be factual and logical. Avoid hallucination or baseless speculation. Respond only with the structured JSON list.
"""

def run_industry_analysis_agent(company_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Industry Analysis Agent for a given structured company profile.

    Args:
        company_profile: Structured JSON with company details.

    Returns:
        Dict with success status, parsed data or error, and raw output.
    """
    try:
        input_json = json.dumps(company_profile, indent=2)
        output_data, raw = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"Analyze the following company profile:\n{input_json}",
            response_model=IndustryOpportunityList,
        )
        return {"success": True, "data": output_data, "raw_response": raw}
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": None
        }
