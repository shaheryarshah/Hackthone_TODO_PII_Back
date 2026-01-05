"""Script to create test user and todos for testing."""
from pathlib import Path
import sys

# Add src to path
_src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(_src_path))

from database import engine, Base
from models.user import User
from models.todo import Todo
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

Session = sessionmaker(bind=engine)
db = Session()

try:
    # Check if test user exists
    existing = db.query(User).filter(User.email == 'test@example.com').first()
    if existing:
        print(f'Using existing test user with ID: {existing.id}')
        user = existing
    else:
        # Create test user
        user = User(email='test@example.com')
        user.password_hash = 'testpass123'  # Note: Should use proper bcrypt hashing
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f'Created test user with ID: {user.id}')

    # Create test todos with extended features
    test_todos = [
        Todo(
            user_id=user.id,
            title='High Priority Task',
            priority='high',
            description='Important urgent task',
            due_date=datetime.utcnow() + timedelta(days=1),
            completed=False
        ),
        Todo(
            user_id=user.id,
            title='Medium Priority Task',
            priority='medium',
            tags=['work', 'urgent'],
            completed=False
        ),
        Todo(
            user_id=user.id,
            title='Low Priority Task',
            priority='low',
            due_date=datetime.utcnow() + timedelta(days=3),
            tags=['personal'],
            completed=False
        ),
        Todo(
            user_id=user.id,
            title='Recurring Daily Task',
            priority='medium',
            due_date=datetime.utcnow() + timedelta(hours=4),
            recurrence='daily',
            completed=False
        ),
        Todo(
            user_id=user.id,
            title='Overdue Task',
            priority='high',
            due_date=datetime.utcnow() - timedelta(days=2),
            tags=['important'],
            completed=False
        ),
        Todo(
            user_id=user.id,
            title='Completed Task with Tags',
            priority='low',
            tags=['work', 'done'],
            completed=True
        ),
    ]

    for todo in test_todos:
        db.add(todo)

    db.commit()
    print(f'Created {len(test_todos)} test todos with extended features')

    # Print summary
    print('\n=== Test Data Summary ===')
    print('Email: test@example.com')
    print('Password: testpass123')
    print('\nCreated todos:')
    for todo in test_todos:
        print(f'  - {todo.title} (priority: {todo.priority}, tags: {todo.tags})')

except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
