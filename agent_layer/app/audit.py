"""审计日志薄封装。"""
from .daoql import write_audit, list_audit

__all__ = ["write_audit", "list_audit"]
