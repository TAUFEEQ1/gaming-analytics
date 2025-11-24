#!/usr/bin/env python
"""Script to create the notifications table in the database."""

from database import engine, Base, Notification

def create_tables():
    """Create all tables defined in the models."""
    Base.metadata.create_all(bind=engine)
    print("✓ Notification table created successfully!")
    print("\nTable schema:")
    print("- id (INTEGER, PRIMARY KEY)")
    print("- timestamp (DATETIME)")
    print("- anomaly_type (VARCHAR)")
    print("- severity (VARCHAR)")
    print("- value (FLOAT)")
    print("- z_score (FLOAT)")
    print("- message (TEXT)")
    print("- is_read (BOOLEAN, default=False)")
    print("- created_at (DATETIME)")

if __name__ == "__main__":
    create_tables()
