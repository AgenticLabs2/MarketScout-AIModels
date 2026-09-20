import json
import traceback
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import RootModel
from src.agents.base import run_structured_agent
from src.utils.models import Opportunity

# environment variables
load_dotenv()
class OpportunityList(RootModel[List[Opportunity]]):
    pass


SYSTEM_PROMPT = """
You are OpportunityAgent, an expert business strategist AI.

Your goal is to analyze structured data on market gaps, company capabilities, and competitive insights, then suggest high-impact, validated growth opportunities.

Instructions:
1. Use the provided `market_gaps` list to identify unmet needs or pain points in the market.
2. For each identified gap, generate a relevant business opportunity. Focus on feasibility, strategic value, and novelty.
3. Use the `search_tool` to find real, working links or sources that support each opportunity — no hallucinations.
4. Each item must include:
   - "title": short name for the opportunity
   - "priority": High | Medium | Low based on strategic value
   - "description": 1–3 sentences on the value proposition and business logic
   - "sources": list of supporting evidence or links (real or from provided context)

Respond **only** with raw JSON (no markdown formatting, no explanation) in the format:
[
  {
    "title": "Launch AI Chatbot",
    "priority": "High",
    "description": "The company can leverage its NLP capabilities to offer a customer support chatbot. This fills a major gap in CX in the retail sector.",
    "sources": ["https://gartner.com/chatbots-2025"]
  },
  ...
]

Be realistic, prioritize feasibility and relevance. No speculative or generic output.
"""

def run_opportunity_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate realistic, search-validated business opportunities from market gaps.
    """
    try:
        market_gaps = input_data
        if not market_gaps or not isinstance(market_gaps, list):
            return {
                "success": False,
                "error": "Missing or invalid 'market_gaps'. Expected a list of strings.",
                "raw_response": None
            }

        user_message = f"""
        Given the following market gaps:
        {json.dumps(market_gaps)}

        Generate 3–5 realistic growth opportunities.
        For each one, include title, priority, description, and sources (use the search_tool for links).
        Respond only in JSON array format.
        """

        parsed_data, raw = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_message.strip(),
            response_model=OpportunityList,
            use_search=True,
        )
        return {"success": True, "data": parsed_data, "raw_response": raw}

    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "raw_response": None
        }
