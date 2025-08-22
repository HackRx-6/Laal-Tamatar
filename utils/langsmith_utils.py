"""
LangSmith utilities for tracing and monitoring
"""

import os
import functools
from typing import Any, Callable, Dict, Optional
from langsmith import Client, traceable
from langsmith.run_helpers import get_current_run_tree
from utils.config import (
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize LangSmith client
client = None
if LANGSMITH_TRACING and LANGSMITH_API_KEY:
    try:
        client = Client(
            api_url=LANGSMITH_ENDPOINT,
            api_key=LANGSMITH_API_KEY,
        )
        # Set environment variables for LangChain integration
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
        logger.info(f"LangSmith client initialized for project: {LANGSMITH_PROJECT}")
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith client: {e}")
        client = None
else:
    logger.info("LangSmith tracing disabled or API key not provided")


def langsmith_trace(
    name: Optional[str] = None,
    run_type: str = "chain",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_run_id: Optional[str] = None,
    project_name: Optional[str] = None,
):
    """
    Decorator to trace function calls with LangSmith

    Args:
        name: Name for the trace (defaults to function name)
        run_type: Type of run ("chain", "tool", "llm", "retriever", etc.)
        tags: List of tags for the trace
        metadata: Additional metadata for the trace
        parent_run_id: Parent run ID for nested traces
        project_name: Override project name
    """

    def decorator(func: Callable) -> Callable:
        if not LANGSMITH_TRACING or not client:
            # If tracing is disabled, return original function
            return func

        trace_name = name or func.__name__
        trace_tags = tags or []
        trace_metadata = metadata or {}
        trace_project = project_name or LANGSMITH_PROJECT

        @functools.wraps(func)
        @traceable(
            name=trace_name,
            run_type=run_type,
            tags=trace_tags,
            metadata=trace_metadata,
            project_name=trace_project,
        )
        def wrapper(*args, **kwargs):
            try:
                # Add function context to metadata
                current_run = get_current_run_tree()
                if current_run:
                    current_run.add_tags(
                        [f"function:{func.__name__}", f"module:{func.__module__}"]
                    )

                logger.info(f"Starting LangSmith trace: {trace_name}")
                result = func(*args, **kwargs)
                logger.info(f"Completed LangSmith trace: {trace_name}")
                return result
            except Exception as e:
                logger.error(f"Error in traced function {trace_name}: {e}")
                # Add error information to the trace
                current_run = get_current_run_tree()
                if current_run:
                    current_run.add_tags(["error"])
                    current_run.end(error=str(e))
                raise

        return wrapper

    return decorator


def get_parent_run_id() -> Optional[str]:
    """Get the current parent run ID for nested tracing"""
    try:
        current_run = get_current_run_tree()
        return current_run.id if current_run else None
    except Exception:
        return None


def add_trace_tags(tags: list):
    """Add tags to the current trace"""
    try:
        current_run = get_current_run_tree()
        if current_run:
            current_run.add_tags(tags)
    except Exception as e:
        logger.warning(f"Failed to add tags to trace: {e}")


def add_trace_metadata(metadata: Dict[str, Any]):
    """Add metadata to the current trace"""
    try:
        current_run = get_current_run_tree()
        if current_run:
            current_run.add_metadata(metadata)
    except Exception as e:
        logger.warning(f"Failed to add metadata to trace: {e}")


def create_child_trace(
    name: str,
    run_type: str = "chain",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Create a child trace under the current parent"""
    if not LANGSMITH_TRACING or not client:
        return None

    parent_run_id = get_parent_run_id()
    return langsmith_trace(
        name=name,
        run_type=run_type,
        tags=tags,
        metadata=metadata,
        parent_run_id=parent_run_id,
    )
