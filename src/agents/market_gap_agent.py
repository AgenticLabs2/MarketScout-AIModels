import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import RootModel
from src.agents.base import run_structured_agent
from src.utils.models import MarketGap

# Load environment variables from .env file
load_dotenv()
class MarketGapList(RootModel[List[MarketGap]]):
    pass


SYSTEM_PROMPT = """
    You are MarketGapAnalysisAgent, a specialized AI agent designed to identify strategic market gaps. Your purpose is to analyze and compare a company's profile against its competitors and the broader market landscape to uncover unmet customer needs and untapped opportunities.

    Follow these guidelines strictly:

    1. **Analyze Provided Inputs Explicitly**: Your analysis must be based exclusively on the data provided to you, which includes a company profile, a list of competitors, and market statistics. Do not use external web resources or prior knowledge.
    2. **Structure Your Output**: Always return a valid JSON object with the following keys:
    - `gap`: A concise string describing the specific unmet need or missing feature.
    - `impact`: A string indicating the potential market impact of this gap, rated as "High", "Medium", or "Low".
    - `evidence`: A short paragraph (2-3 sentences) explaining the reasoning for the identified gap, directly referencing the provided data (e.g., "Competitor X offers this feature, but the target company does not," or "Market stats show a growing demand for Y, which is not addressed by the company's current products.").
    - `source`: List of URLs used to derive the above information.

    3. **Be Logical and Evidential**: Do not infer or hallucinate details. Only include data supported by the sources.
    4. **Respond in JSON Only**: No explanation or commentary outside the JSON. Just the structured JSON output.

    Example output format:
    [{
        "gap": "Lack of an entry-level pricing tier for small businesses.",
        "impact": "High",
        "evidence": "Market statistics indicate that 45 percentage of the target market consists of small businesses with fewer than 10 employees. All listed competitors offer a dedicated 'Basic' or 'Starter' plan, while the company's lowest-priced product is targeted at mid-market clients.",
        "source": "Market Stats Report, Competitor List"
    }]
    """

def run_market_gap_analysis_agent(incoming_company_stats: Dict[str,Any]) -> Dict[str,Any]:
    """
    Run the company research agent for a given company name.
    
    Args:
        company profile: Company's market domain.
        competitor list: list of company's competitors.
        market stats: some statistical data about the market.
        
    Returns:
        Dict containing the agent's response and metadata
    """
    try:
        generated_user_message = (
            "Analyze the following company profile, competitor landscape, and market "
            "statistics. Identify strategic market gaps using only this supplied data:\n"
            f"{json.dumps(incoming_company_stats, indent=2)}"
        )
        gap_data, raw = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=generated_user_message,
            response_model=MarketGapList,
        )
        return {"success": True, "data": gap_data, "raw_response": raw}
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": None
        }

