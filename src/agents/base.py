"""Base Agent interface for F1 Pit Wall Strategy System."""
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from src.core.models import AgentReport

TContext = TypeVar("TContext")


class BaseSpecialistAgent(ABC, Generic[TContext]):
    """Abstract base class for all specialist pit wall agents (Rule-Based & LLM)."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def evaluate(self, context: TContext) -> AgentReport:
        """Evaluates strategy candidates given the role-specific context."""
        pass
