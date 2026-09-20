from typing import Dict, Any
from dotenv import load_dotenv
import traceback
from src.agents.base import run_structured_agent
from src.utils.models import MarketData

# Load .env file
load_dotenv()
SYSTEM_PROMPT = """
You are MarketDataAgent, an AI assistant specialized in gathering and summarizing market statistics and emerging trends within a given domain.

Your objective is to provide a structured overview of key market dynamics.

Guidelines:
1. Use Only Trusted Sources: Prioritize financial APIs, market intelligence reports, trend data, and official statistics.
2. Organize Information: Return a JSON object with the following structure:
{
  "market_size_usd": <market size in USD as a number (e.g., 5000000000 for 5B USD)>,
  "CAGR": <compound annual growth rate as a decimal (e.g., 0.07 for 7%)>,
  "key_drivers": ["<driver1>", "<driver2>", "<driver3>"],
  "sources": ["<url1>", "<url2>", "<url3>"]
}
3. Avoid Speculation: Only include what can be found from reliable data sources.
4. Use JSON Only: No narrative outside the JSON.
5. Convert market size to USD numerical value (e.g., 5B USD = 5000000000)
6. Convert growth rates to decimal format (e.g., 12% = 0.12)
"""


def run_market_data_agent(domain: str) -> Dict[str, Any]:
    """
    Execute market research for a given domain using the LangGraph agent runtime.

    Args:
        domain (str): Market domain to analyze

    Returns:
        Dict[str, Any]: Result dictionary with success flag, data or error
    """
    try:
        if not domain or not isinstance(domain, str):
            return {
                "success": False,
                "error": "Invalid or missing 'domain' parameter.",
                "raw_response": None
            }

        user_message = f"""
        Provide up-to-date market statistics and trend analysis for the "{domain}" industry.
        Include market size, growth rate, key trends, and data sources.
        Summarize your findings in the structured JSON format specified in the system prompt.
        """

        market_data, raw = run_structured_agent(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_message.strip(),
            response_model=MarketData,
            use_search=True,
        )
        return {"success": True, "data": market_data, "raw_response": raw}

    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "raw_response": None
        }
