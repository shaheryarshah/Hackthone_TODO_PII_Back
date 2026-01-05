"""Todo service for business logic."""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models.todo import Todo
from schemas.todo import TodoCreate, TodoUpdate


class TodoService:
    """Service class for Todo operations."""

    # Priority sort order
    PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id

    def _apply_user_filter(self, query):
        """Apply user_id filter to query if user_id is set."""
        if self.user_id is not None:
            return query.filter(Todo.user_id == self.user_id)
        return query

    def _calculate_overdue(self, todo: Todo) -> bool:
        """Calculate if a todo is overdue."""
        if todo.due_date is None or todo.completed:
            return False
        return todo.due_date < datetime.utcnow()

    def _build_filters(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        tag: Optional[str] = None,
    ):
        """Build filter conditions for todo query."""
        conditions = []

        # Search in title and description (case-insensitive)
        if search:
            conditions.append(
                or_(
                    Todo.title.ilike(f"%{search}%"),
                    Todo.description.ilike(f"%{search}%")
                )
            )

        # Filter by status (completed/pending)
        if status == "completed":
            conditions.append(Todo.completed == True)
        elif status == "pending":
            conditions.append(Todo.completed == False)

        # Filter by priority
        if priority:
            conditions.append(Todo.priority == priority.lower())

        # Filter by due date range
        if due_before:
            conditions.append(Todo.due_date <= due_before)
        if due_after:
            conditions.append(Todo.due_date >= due_after)

        # Filter by tag (JSON contains for SQLite)
        if tag:
            conditions.append(Todo.tags.like(f'%"{tag}"%'))

        return conditions

    def _apply_sort(
        self,
        query,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ):
        """Apply sorting to query."""
        sort_column = None

        if sort_by == "due_date":
            sort_column = Todo.due_date
        elif sort_by == "priority":
            # Custom sort by priority order
            sort_column = Todo.priority
        elif sort_by == "title":
            sort_column = Todo.title
        else:
            # Default: sort by created_at
            sort_column = Todo.created_at

        # Apply sort order
        if sort_order and sort_order.lower() == "asc":
            if sort_by == "priority":
                # Custom case statement for priority order
                from sqlalchemy import case
                return query.order_by(
                    case(
                        (Todo.priority == "high", 1),
                        (Todo.priority == "medium", 2),
                        (Todo.priority == "low", 3),
                        else_=4
                    ).asc()
                )
            else:
                return query.order_by(sort_column.asc())
        else:
            # Default descending
            if sort_by == "priority":
                from sqlalchemy import case
                return query.order_by(
                    case(
                        (Todo.priority == "high", 1),
                        (Todo.priority == "medium", 2),
                        (Todo.priority == "low", 3),
                        else_=4
                    ).asc()
                )
            else:
                return query.order_by(sort_column.desc())

        return query

    def create(self, todo_data: TodoCreate) -> Todo:
        """Create a new todo for the authenticated user."""
        todo = Todo(
            title=todo_data.title,
            description=todo_data.description,
            user_id=self.user_id,
            priority=todo_data.priority or "medium",
            tags=todo_data.tags or [],
            due_date=todo_data.due_date,
            recurrence=todo_data.recurrence or "none"
        )
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def get_all(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_before: Optional[datetime] = None,
        due_after: Optional[datetime] = None,
        tag: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Todo]:
        """Get all todos for the authenticated user with optional filters and sorting."""
        query = self._apply_user_filter(self.db.query(Todo))

        # Apply filters
        conditions = self._build_filters(search, status, priority, due_before, due_after, tag)
        if conditions:
            query = query.filter(and_(*conditions))

        # Apply sorting
        query = self._apply_sort(query, sort_by, sort_order)

        return query.all()

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """Get a todo by ID for the authenticated user."""
        query = self._apply_user_filter(self.db.query(Todo))
        return query.filter(Todo.id == todo_id).first()

    def update(self, todo_id: int, todo_data: TodoUpdate) -> Optional[Todo]:
        """Update a todo for the authenticated user."""
        todo = self.get_by_id(todo_id)
        if not todo:
            return None

        update_data = todo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)

        self.db.commit()
        self.db.refresh(todo)
        return todo

    def delete(self, todo_id: int) -> bool:
        """Delete a todo for the authenticated user."""
        todo = self.get_by_id(todo_id)
        if not todo:
            return False

        self.db.delete(todo)
        self.db.commit()
        return True

    def mark_complete(self, todo_id: int) -> Optional[tuple[Todo, Optional[Todo]]]:
        """
        Mark a todo as complete for the authenticated user.
        Returns tuple of (completed_task, next_task) or (completed_task, None) if no recurrence.
        """
        todo = self.get_by_id(todo_id)
        if not todo:
            return None

        if todo.completed:
            # Already completed
            return (todo, None)

        todo.completed = True
        self.db.commit()

        # Handle recurrence: create next instance
        next_task = None
        if todo.recurrence and todo.recurrence != "none" and todo.due_date:
            next_task = self._create_next_instance(todo)

        self.db.refresh(todo)
        return (todo, next_task)

    def _create_next_instance(self, todo: Todo) -> Todo:
        """Create next instance of a recurring task."""
        due_date = todo.due_date
        recurrence = todo.recurrence

        # Calculate next due date
        if recurrence == "daily":
            next_due_date = due_date + timedelta(days=1)
        elif recurrence == "weekly":
            next_due_date = due_date + timedelta(weeks=1)
        elif recurrence == "monthly":
            # Add one month, handling month overflow
            year = due_date.year
            month = due_date.month + 1
            if month > 12:
                year += 1
                month = 1

            # Handle February 30th edge case
            day = due_date.day
            max_day = 31
            if month in [4, 6, 9, 11]:
                max_day = 30
            elif month == 2:
                if (year % 400 == 0) or (year % 100 != 0 and year % 4 == 0):
                    max_day = 29
                else:
                    max_day = 28

            if day > max_day:
                day = max_day

            next_due_date = due_date.replace(year=year, month=month, day=day)
        else:
            return None

        # Create new instance
        next_task = Todo(
            title=todo.title,
            description=todo.description,
            user_id=todo.user_id,
            priority=todo.priority,
            tags=todo.tags,
            due_date=next_due_date,
            recurrence=todo.recurrence,
            completed=False
        )
        self.db.add(next_task)
        self.db.commit()
        self.db.refresh(next_task)
        return next_task

    def get_todos_due_soon(self, hours: int = 1) -> List[Todo]:
        """Get todos due within the specified hours for the authenticated user."""
        now = datetime.utcnow()
        due_threshold = now + timedelta(hours=hours)

        query = self._apply_user_filter(self.db.query(Todo))
        return query.filter(
            and_(
                Todo.completed == False,
                Todo.due_date.isnot(None),
                Todo.due_date <= due_threshold,
                Todo.due_date >= now
            )
        ).all()
