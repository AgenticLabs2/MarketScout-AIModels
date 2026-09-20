import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import RootModel
from src.agents.base import run_structured_agent
from src.utils.models import CompetitiveLandscape

# Load environment variables from .env file
load_dotenv()
class CompetitiveLandscapeList(RootModel[List[CompetitiveLandscape]]):
    pass


SYSTEM_PROMPT = """
You are CompetitiveLandscapeAgent, a specialized AI agent tasked with mapping competitors and their product/market positions within a given domain. Your goal is to identify key players, their offerings, and competitive positioning.

Follow these guidelines strictly:

1. **Use Trusted Sources Only**: Prioritize data from industry reports, company websites, business directories, and reputable market research sources.
2. **Structure Your Output**: Always return a valid JSON array with competitor objects containing:
   - `competitor`: Company name
   - `product`: Main product/service in the domain
   - `market_share`: Estimated market share (0.0 to 1.0, use 0.0 if unknown)
   - `note`: Brief description of their competitive position/strategy
   - `sources`: Array of URLs or sources where information was found

3. **Focus on the Domain**: Only include competitors that are relevant to the specified domain.
4. **Be Factual, Not Speculative**: Base market share estimates on available data, use 0.0 if no reliable data exists.
5. **Respond in JSON Only**: No explanation or commentary outside the JSON array.

Example output format:
[
  {
    "competitor": "Company A",
    "product": "Product X",
    "market_share": 0.15,
    "note": "Market leader with strong enterprise focus",
    "sources": ["https://example.com/market-report", "https://company-a.com/about"]
  },
  {
    "competitor": "Company B", 
    "product": "Product Y",
    "market_share": 0.08,
    "note": "Emerging player with innovative approach",
    "sources": ["https://company-b.com/about", "https://techcrunch.com/article"]
  }
]
"""

def run_competitive_landscape_agent(industry_opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the competitive landscape agent for a given industry opportunity.
    
    Args:
        industry_opportunity: Dict containing domain, score, rationale, and sources
        
    Returns:
        Dict containing the agent's response and metadata
    """
    try:
        domain = industry_opportunity.get("domain", "")
        score = industry_opportunity.get("score", 0.0)
        rationale = industry_opportunity.get("rationale", "")
        
        message = f"""Map the competitive landscape for the {domain} domain (opportunity score: {score}).
        
Context: {rationale}

Identify key competitors, their products, market positions, and competitive strategies in this domain."""
        
        competitors_data, raw = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=message,
            response_model=CompetitiveLandscapeList,
            use_search=True,
        )
        return {"success": True, "data": competitors_data, "raw_response": raw}
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": None
        }
