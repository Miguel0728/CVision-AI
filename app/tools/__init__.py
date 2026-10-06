"""Paquete de herramientas. Cada módulo registra sus herramientas al importarse."""
from app.tools import candidates, emails, jobs
from app.tools.registry import get_tool_card, get_tool_label, get_tool_schemas, run_tool

TOOL_MODULES = (candidates, emails, jobs)

__all__ = ["TOOL_MODULES", "get_tool_card", "get_tool_label", "get_tool_schemas", "run_tool"]
