
"""Shared LangGraph/LangChain agent utilities."""

import json
import os
from typing import Any, TypeVar

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, RootModel, create_model

from src.mcp_client.tools import search_tool
from src.utils.config import LLMSettings, get_config
from src.utils.mcp_manager import MCPServerManager


StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


def create_chat_model(settings: LLMSettings | None = None) -> tuple[BaseChatModel, str]:
    """Create the configured OpenAI or Ollama chat model."""
    llm = settings or get_config().llm
    if llm.provider == "openai":
        api_key = os.getenv(llm.openai.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"{llm.openai.api_key_env} is not configured for the OpenAI provider"
            )
        return ChatOpenAI(model=llm.openai.model, api_key=api_key), llm.provider

    from langchain_ollama import ChatOllama

    return (
        ChatOllama(
            model=llm.ollama.model,
            base_url=llm.ollama.base_url,
            temperature=llm.ollama.temperature,
        ),
        llm.provider,
    )


def run_structured_agent(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[StructuredOutput],
    use_search: bool = False,
) -> tuple[Any, str]:
    """Run a LangGraph-backed agent and return validated data plus raw JSON."""
    model, provider = create_chat_model()
    tools = []
    if use_search:
        mcp_status = MCPServerManager().ensure_server_running()
        if not mcp_status["success"]:
            raise RuntimeError(f"MCP server is unavailable: {mcp_status['message']}")
        tools.append(
            StructuredTool.from_function(
                func=search_tool,
                name="search_tool",
                description="Search the web and return source URLs with extracted text.",
            )
        )

    is_root_model = issubclass(response_model, RootModel)
    effective_model: type[BaseModel] = response_model
    if is_root_model:
        root_annotation = response_model.model_fields["root"].annotation
        effective_model = create_model(
            f"{response_model.__name__}Envelope",
            data=(root_annotation, ...),
        )

    response_format = effective_model if provider == "openai" else ToolStrategy(effective_model)
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        response_format=response_format,
    )
    result = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
    structured = result.get("structured_response")
    if structured is None:
        raise RuntimeError("Agent did not return a structured response")
    if not isinstance(structured, effective_model):
        structured = effective_model.model_validate(structured)
    data = structured.data if is_root_model else structured.model_dump()
    return data, json.dumps(data, default=str)
