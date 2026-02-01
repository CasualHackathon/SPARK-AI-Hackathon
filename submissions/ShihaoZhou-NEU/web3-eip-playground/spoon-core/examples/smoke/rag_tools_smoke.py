"""Smoke test for RAG Tools, verifying dependency injection and backward compatibility.

Run:
  python3 examples/smoke/rag_tools_smoke.py
"""

import asyncio
import os
import sys
import pathlib

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

# Mock missing dependencies to isolate tool logic testing
from unittest.mock import MagicMock
import sys

# Mock openai and related modules that might be missing in this env
sys.modules["openai"] = MagicMock()
sys.modules["spoon_ai.min_pypi"] = MagicMock() # potential internal dep

# We need to mock ChatBot because rag_tools imports it
mock_chat = MagicMock()
sys.modules["spoon_ai.chat"] = mock_chat

# Mock RAG backends
sys.modules["pinecone"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["qdrant_client"] = MagicMock()
sys.modules["faiss"] = MagicMock()

try:
    from spoon_ai.tools.rag_tools import RAGQATool, RAGSearchTool
    # Mock ChatBot inside the module if needed, though sys.modules should cover it
    mock_chat.ChatBot = MagicMock
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Print sys.path to help debug
    print(sys.path)
    sys.exit(1)

class MockLLM:
    async def ask(self, messages, **kwargs):
        return "This is a mock answer with citation [1]."

async def main():
    print("=== Testing RAG Tools Compatibility ===")
    
    # 1. Test Backward Compatibility (No args)
    try:
        tool_v1 = RAGQATool()
        print("[PASS] V1 Initialization (No args) passed.")
        assert tool_v1._llm is None
    except Exception as e:
        print(f"[FAIL] V1 Initialization failed: {e}")

    # 2. Test Backward Compatibility (Pydantic fields)
    try:
        tool_v2 = RAGQATool(name="custom_rag", description="Custom desc")
        print("[PASS] V1 Initialization (Pydantic fields) passed.")
        assert tool_v2.name == "custom_rag"
        assert tool_v2._llm is None
    except Exception as e:
        print(f"[FAIL] V1 Initialization (Pydantic fields) failed: {e}")

    # 3. Test Dependency Injection (New feature)
    try:
        mock_llm = MockLLM()
        tool_v3 = RAGQATool(llm=mock_llm)
        print("[PASS] V2 Initialization (Dependency Injection) passed.")
        assert tool_v3._llm is mock_llm
    except Exception as e:
        print(f"[FAIL] V2 Initialization (Dependency Injection) failed: {e}")

    # 4. Test Dependency Injection Mixed with Pydantic
    try:
        mock_llm = MockLLM()
        tool_v4 = RAGQATool(llm=mock_llm, name="injected_tool")
        print("[PASS] V2 Initialization (Mixed) passed.")
        assert tool_v4.name == "injected_tool"
        assert tool_v4._llm is mock_llm
    except Exception as e:
        print(f"[FAIL] V2 Initialization (Mixed) failed: {e}")

    print("\n=== Testing Parameter Defaults ===")
    # 5. Check schema defaults
    search_tool = RAGSearchTool()
    props = search_tool.parameters["properties"]
    
    if "default: 5" in props["top_k"].get("description", ""):
        print("[PASS] RAGSearchTool top_k description contains default.")
    else:
        print(f"[FAIL] RAGSearchTool top_k description missing default: {props['top_k']}")

    if "default: 'default'" in props["collection"].get("description", ""):
        print("[PASS] RAGSearchTool collection description contains default.")
    else:
        print(f"[FAIL] RAGSearchTool collection description missing default: {props['collection']}")

    print("\nAll Smoke Tests Completed.")

if __name__ == "__main__":
    asyncio.run(main())
