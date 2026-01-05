"""SQLAlchemy Enum definitions for Todo extended features."""

from sqlalchemy import Enum as SQLEnum


class Priority(str, SQLEnum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrencePattern(str, SQLEnum):
    """Recurrence patterns for tasks."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
