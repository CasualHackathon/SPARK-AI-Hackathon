import time
from typing import Union, Dict, Any, Optional, List, AsyncIterator, AsyncContextManager
import asyncio
from contextlib import asynccontextmanager
from fastmcp.client import Client as MCPClient
import logging

logger = logging.getLogger(__name__)

class MCPClientMixin:
    def __init__(self, mcp_transport):
        if mcp_transport and mcp_transport != "mcp_server":
            try:
                self._client = MCPClient(mcp_transport)
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client with transport {mcp_transport}: {e}")
                self._client = None
        else:
            self._client = None
            
        self._last_sender = None
        self._last_topic = None
        self._last_message_id = None

        # Enhanced session management
        self._session_lock = asyncio.Lock()
        self._task_sessions = {}
        self._session_count = 0
        self._max_concurrent_sessions = 10  
        self._cleanup_interval = 300  
        self._last_cleanup = time.time()
        
        # Track session metrics for monitoring
        self._session_stats = {
            "created": 0,
            "closed": 0,
            "failed": 0,
            "active": 0
        }

    @asynccontextmanager
    async def get_session(self):
        """
        Get a session with robust resource management and cleanup.
        
        Features:
        - Automatic session reuse per task
        - Resource limits to prevent exhaustion
        - Proper cleanup on cancellation/failure
        - Periodic cleanup of stale sessions
        """
        if self._client is None:
            raise RuntimeError("MCP client is not configured (mcp_transport is missing or invalid)")

        current_task = asyncio.current_task()
        if current_task is None:
            raise RuntimeError("MCPClientMixin.get_session() must be called from within an async task")
            
        task_id = id(current_task)
        
        # Periodic cleanup of stale sessions
        await self._cleanup_stale_sessions()
        
        # Check if current task already has a session
        if task_id in self._task_sessions:
            session_info = self._task_sessions[task_id]
            if session_info["session"] and not session_info.get("closed", False):
                try:
                    session_info["last_accessed"] = time.time()
                    yield session_info["session"]
                    return
                except Exception as e:
                    logger.warning(f"Existing session for task {task_id} failed: {e}")
                    # Mark as closed and continue to create new session
                    session_info["closed"] = True

        # Create new session with resource limits
        async with self._session_lock:
            # Check session limits
            if self._session_count >= self._max_concurrent_sessions:
                # Try to cleanup stale sessions first
                await self._force_cleanup_stale_sessions()
                
                if self._session_count >= self._max_concurrent_sessions:
                    raise RuntimeError(f"Maximum concurrent sessions ({self._max_concurrent_sessions}) reached")
            
            session = None
            session_info = None
            
            try:
                # Create new session
                session = await self._client.__aenter__()
                current_time = time.time()
                
                session_info = {
                    "session": session,
                    "created_at": current_time,
                    "last_accessed": current_time,
                    "task_id": task_id,
                    "closed": False
                }
                
                self._task_sessions[task_id] = session_info
                self._session_count += 1
                self._session_stats["created"] += 1
                self._session_stats["active"] += 1
                
                logger.debug(f"Created MCP session for task {task_id} (total: {self._session_count})")
                
                # Register cleanup callback for task cancellation
                current_task.add_done_callback(
                    lambda t: asyncio.create_task(self._cleanup_task_session(task_id))
                )
                
                yield session
                
            except asyncio.CancelledError:
                logger.info(f"Session creation cancelled for task {task_id}")
                await self._cleanup_session(task_id, session_info, session)
                raise
            except Exception as e:
                logger.error(f"Failed to create MCP session for task {task_id}: {e}")
                self._session_stats["failed"] += 1
                await self._cleanup_session(task_id, session_info, session)
                raise
            finally:
                # Always attempt cleanup on context exit
                await self._cleanup_session(task_id, session_info, session)

    async def _cleanup_session(self, task_id: int, session_info: Optional[Dict], session: Optional[Any]):
        """Clean up a specific session with proper error handling."""
        try:
            if session_info and not session_info.get("closed", False):
                session_info["closed"] = True
                
            if session and self._client:
                try:
                    await self._client.__aexit__(None, None, None)
                    self._session_stats["closed"] += 1
                    logger.debug(f"Successfully closed MCP session for task {task_id}")
                except Exception as e:
                    logger.error(f"Error closing MCP session for task {task_id}: {e}")
                    self._session_stats["failed"] += 1
        except Exception as e:
            logger.error(f"Error during session cleanup for task {task_id}: {e}")
        finally:
            # Always remove from tracking
            if task_id in self._task_sessions:
                del self._task_sessions[task_id]
                self._session_count = max(0, self._session_count - 1)
                self._session_stats["active"] = max(0, self._session_stats["active"] - 1)

    async def _cleanup_task_session(self, task_id: int):
        """Cleanup callback for when a task completes or is cancelled."""
        if task_id in self._task_sessions:
            session_info = self._task_sessions[task_id]
            await self._cleanup_session(task_id, session_info, session_info.get("session"))

    async def _cleanup_stale_sessions(self):
        """Periodic cleanup of stale sessions."""
        current_time = time.time()
        
        # Only run cleanup periodically
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
            
        self._last_cleanup = current_time
        stale_threshold = current_time - 600  # 10 minutes
        
        stale_tasks = []
        for task_id, session_info in self._task_sessions.items():
            if (session_info.get("last_accessed", 0) < stale_threshold or 
                session_info.get("closed", False)):
                stale_tasks.append(task_id)
        
        for task_id in stale_tasks:
            logger.info(f"Cleaning up stale MCP session for task {task_id}")
            session_info = self._task_sessions.get(task_id)
            if session_info:
                await self._cleanup_session(task_id, session_info, session_info.get("session"))

    async def _force_cleanup_stale_sessions(self):
        """Force cleanup of all stale sessions when hitting limits."""
        current_time = time.time()
        stale_threshold = current_time - 300  # 5 minutes for forced cleanup
        
        stale_tasks = []
        for task_id, session_info in self._task_sessions.items():
            if (session_info.get("last_accessed", 0) < stale_threshold or 
                session_info.get("closed", False)):
                stale_tasks.append(task_id)
        
        cleanup_tasks = [
            self._cleanup_session(
                task_id, 
                self._task_sessions.get(task_id), 
                self._task_sessions.get(task_id, {}).get("session")
            )
            for task_id in stale_tasks
        ]
        
        if cleanup_tasks:
            logger.info(f"Force cleaning up {len(cleanup_tasks)} stale MCP sessions")
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    async def list_mcp_tools(self):
        """Get the list of available tools from the MCP server"""
        if self._client is None:
            return []
        async with self.get_session() as session:
            return await session.list_tools()

    async def call_mcp_tool(self, tool_name: str, **kwargs):
        """Call a tool on the MCP server"""
        if self._client is None:
            return f"MCP tool '{tool_name}' failed: Client not initialized"
        try:
            async with self.get_session() as session:
                res = await session.call_tool(tool_name, arguments=kwargs)
                if not res:
                    return ""

                # Handle different types of MCP responses
                for item in res:
                    # If it's a text response, check if it's a coroutine object string
                    if hasattr(item, 'text') and item.text is not None:
                        text = item.text
                        # Check if the text indicates a coroutine object (FastMCP async tool issue)
                        if "<coroutine object" in text and "at 0x" in text:
                            # This indicates the MCP server returned a coroutine object instead of executing it
                            # Return an error message indicating the issue
                            return f"Error: MCP tool '{tool_name}' returned a coroutine object instead of executing it. This suggests the tool is async but not properly handled by the MCP server."
                        return text
                    # If it's a JSON response, return the JSON content
                    elif hasattr(item, 'json') and item.json is not None:
                        import json
                        return json.dumps(item.json, ensure_ascii=False, indent=2)

                # Fallback to string representation
                if res:
                    result_str = str(res[0])
                    # Check for coroutine object in fallback as well
                    if "<coroutine object" in result_str and "at 0x" in result_str:
                        return f"Error: MCP tool '{tool_name}' returned a coroutine object instead of executing it. This suggests the tool is async but not properly handled by the MCP server."
                    return result_str

                return ""
        except asyncio.CancelledError:
            logger.warning(f"MCP tool call '{tool_name}' was cancelled")
            raise
        except Exception as e:
            logger.error(f"MCP tool '{tool_name}' call failed: {e}")
            return f"MCP tool '{tool_name}' execution failed: {str(e)}"

    async def send_mcp_message(self, recipient: str, message: Union[str, Dict[str, Any]],
                              topic: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message to the MCP system

        Args:
            recipient: Recipient ID
            message: Message content (string or dictionary)
            topic: Message topic
            metadata: Additional metadata

        Returns:
            bool: Whether the message was sent successfully
        """
        if self._client is None:
            return False
        if isinstance(message, str):
            content = {
                "text": message,
                "source": "agent",
            }
            if metadata:
                content["metadata"] = metadata
        else:
            content = message

        try:
            async with self.get_session() as session:
                await session.send_message(
                    recipient=recipient,
                    message=content,
                    topic=topic or "general"
                )
            return True
        except Exception as e:
            logger.error(f"Failed to send MCP message: {e}")
            return False

    async def cleanup(self):
        """Enhanced cleanup method with comprehensive resource cleanup."""
        logger.info("Starting comprehensive MCP client cleanup")
        
        # Close all active sessions
        cleanup_tasks = []
        for task_id, session_info in list(self._task_sessions.items()):
            cleanup_tasks.append(
                self._cleanup_session(task_id, session_info, session_info.get("session"))
            )
        
        if cleanup_tasks:
            logger.info(f"Cleaning up {len(cleanup_tasks)} active MCP sessions")
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Reset all tracking
        self._task_sessions.clear()
        self._session_count = 0
        self._session_stats["active"] = 0
        
        logger.info("MCP client cleanup completed")
        logger.info(f"Session stats: {self._session_stats}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics for monitoring."""
        return {
            **self._session_stats,
            "current_sessions": len(self._task_sessions),
            "max_sessions": self._max_concurrent_sessions
        }
