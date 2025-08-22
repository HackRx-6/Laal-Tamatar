import logging
import sys
from functools import wraps
import json
from typing import Any, Callable, Optional
import traceback

try:
    from .config import (
        DEFAULT_LOG_LEVEL,
        LOG_FUNCTION_CALLS,
        LOG_REQUESTS_RESPONSES,
        LOG_FORMAT,
    )
except ImportError:
    DEFAULT_LOG_LEVEL = logging.INFO
    LOG_FUNCTION_CALLS = True
    LOG_REQUESTS_RESPONSES = True
    LOG_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )


def setup_logger(name: str = __name__, level: Optional[int] = None) -> logging.Logger:
    if level is None:
        level = DEFAULT_LOG_LEVEL

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    file_handler = logging.FileHandler("bajaj_hackrx.log", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def log_function_call(logger: Optional[logging.Logger] = None):
    def decorator(func: Callable) -> Callable:
        actual_logger = logger if logger is not None else setup_logger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not LOG_FUNCTION_CALLS:
                return func(*args, **kwargs)

            func_name = func.__name__

            try:
                args_str = ", ".join([repr(arg) for arg in args])
                kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                actual_logger.info(f"ENTERING {func_name}({all_args})")
            except Exception as e:
                actual_logger.info(f"ENTERING {func_name} (args logging failed: {e})")

            try:
                result = func(*args, **kwargs)

                try:
                    result_str = repr(result)
                    actual_logger.info(f"EXITING {func_name} -> {result_str}")
                except Exception as e:
                    actual_logger.info(
                        f"EXITING {func_name} (result logging failed: {e})"
                    )

                return result

            except Exception as e:
                actual_logger.error(f"ERROR in {func_name}: {str(e)}")
                actual_logger.error(f"TRACEBACK: {traceback.format_exc()}")
                raise

        return wrapper

    return decorator


def safe_json_serialize(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str, indent=2)
    except Exception:
        return str(obj)


def log_request_response(logger: Optional[logging.Logger] = None):
    import inspect

    def decorator(func: Callable) -> Callable:
        actual_logger = logger if logger is not None else setup_logger(func.__module__)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not LOG_REQUESTS_RESPONSES:
                return func(*args, **kwargs)

            func_name = func.__name__

            try:
                if args and hasattr(args[0], "dict"):
                    request_data = args[0].dict()
                    actual_logger.info(
                        f"REQUEST to {func_name}: {safe_json_serialize(request_data)}"
                    )
                else:
                    actual_logger.info(
                        f"REQUEST to {func_name} with args: {repr(args)}, kwargs: {repr(kwargs)}"
                    )
            except Exception as e:
                actual_logger.warning(f"Failed to log request for {func_name}: {e}")

            try:
                result = func(*args, **kwargs)

                try:
                    if hasattr(result, "dict"):
                        response_data = result.dict()
                        actual_logger.info(
                            f"RESPONSE from {func_name}: {safe_json_serialize(response_data)}"
                        )
                    else:
                        result_str = safe_json_serialize(result)
                        actual_logger.info(f"RESPONSE from {func_name}: {result_str}")
                except Exception as e:
                    actual_logger.warning(
                        f"Failed to log response for {func_name}: {e}"
                    )

                return result

            except Exception as e:
                actual_logger.error(f"ERROR in {func_name}: {str(e)}")
                actual_logger.error(f"TRACEBACK: {traceback.format_exc()}")
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not LOG_REQUESTS_RESPONSES:
                return await func(*args, **kwargs)

            func_name = func.__name__

            try:
                if args and hasattr(args[0], "dict"):
                    request_data = args[0].dict()
                    actual_logger.info(
                        f"REQUEST to {func_name}: {safe_json_serialize(request_data)}"
                    )
                else:
                    actual_logger.info(
                        f"REQUEST to {func_name} with args: {repr(args)}, kwargs: {repr(kwargs)}"
                    )
            except Exception as e:
                actual_logger.warning(f"Failed to log request for {func_name}: {e}")

            try:
                result = await func(*args, **kwargs)

                try:
                    if hasattr(result, "dict"):
                        response_data = result.dict()
                        actual_logger.info(
                            f"RESPONSE from {func_name}: {safe_json_serialize(response_data)}"
                        )
                    else:
                        result_str = safe_json_serialize(result)
                        actual_logger.info(f"RESPONSE from {func_name}: {result_str}")
                except Exception as e:
                    actual_logger.warning(
                        f"Failed to log response for {func_name}: {e}"
                    )

                return result

            except Exception as e:
                actual_logger.error(f"ERROR in {func_name}: {str(e)}")
                actual_logger.error(f"TRACEBACK: {traceback.format_exc()}")
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
