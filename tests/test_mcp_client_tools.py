import unittest
from unittest.mock import patch

from src.mcp_client.tools import MCPToolError, search_tool
from src.utils.config import MCPSettings


class MCPClientToolTests(unittest.TestCase):
    def test_search_tool_calls_remote_mcp_tool(self):
        settings = MCPSettings(url="http://tools.example/sse", max_retries=0)
        with patch("src.mcp_client.tools.get_config") as get_config, patch(
            "src.mcp_client.tools._call_tool",
            return_value={"sources": ["https://example.com"], "information": ["Example"], "status": "success"},
        ) as call_tool:
            get_config.return_value.mcp = settings
            result = search_tool("example query")

        self.assertEqual(result["status"], "success")
        call_tool.assert_called_once_with("search_tool", {"query": "example query"}, settings)

    def test_search_tool_rejects_blank_query_without_remote_call(self):
        with patch("src.mcp_client.tools._call_tool") as call_tool:
            result = search_tool("   ")

        self.assertEqual(result["status"], "error")
        call_tool.assert_not_called()

    def test_remote_error_is_propagated(self):
        settings = MCPSettings(url="http://tools.example/sse", max_retries=0)
        with patch("src.mcp_client.tools.get_config") as get_config, patch(
            "src.mcp_client.tools._call_tool", side_effect=MCPToolError("offline")
        ):
            get_config.return_value.mcp = settings
            with self.assertRaisesRegex(MCPToolError, "offline"):
                search_tool("example query")


if __name__ == "__main__":
    unittest.main()
