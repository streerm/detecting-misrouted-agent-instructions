from .types import ToolCall, ToolSpec, Turn

__all__ = ["ToolCall", "ToolSpec", "Turn", "ToolHub", "load_mcp_config"]


def __getattr__(name):  # lazy: the mcp SDK is an optional extra
    if name in ("ToolHub", "load_mcp_config"):
        from . import mcp_hub
        return getattr(mcp_hub, name)
    raise AttributeError(name)
