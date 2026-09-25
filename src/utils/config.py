"""Application configuration loaded from the project TOML file."""

from functools import lru_cache
import os
from pathlib import Path
import tomllib
from typing import Literal

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.toml"


class OpenAISettings(BaseModel):
    model: str = "o4-mini"
    api_key_env: str = "OPENAI_API_KEY"


class OllamaSettings(BaseModel):
    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"
    temperature: float = Field(default=0.0, ge=0.0)


class LLMSettings(BaseModel):
    provider: Literal["openai", "ollama"] = "openai"
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)


class MCPSettings(BaseModel):
    """Connection settings for the remote MarketScout MCP tool service."""

    url: str = "http://localhost:8000/sse"
    connect_timeout_seconds: float = Field(default=10.0, gt=0.0)
    tool_timeout_seconds: float = Field(default=30.0, gt=0.0)
    max_retries: int = Field(default=1, ge=0, le=3)


class AppConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and validate config.toml, optionally overridden by MARKETSCOUT_CONFIG."""
    configured_path = os.getenv("MARKETSCOUT_CONFIG")
    path = Path(configured_path).expanduser() if configured_path else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise RuntimeError(f"MarketScout config file not found: {path}")
    try:
        with path.open("rb") as config_file:
            return AppConfig.model_validate(tomllib.load(config_file))
    except Exception as exc:
        raise RuntimeError(f"Invalid MarketScout config file {path}: {exc}") from exc
