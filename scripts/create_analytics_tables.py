"""Create analytics tables if they don't exist.

Run locally with:

    python scripts/create_analytics_tables.py

This uses the app config and SQLAlchemy engine to create only the
`daily_analytics` and `user_analytics` tables (safe, checkfirst=True).
"""
from app import create_app, db


def main():
    app = create_app()
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from app.models.analytics import DailyAnalytics, UserAnalytics

        print('Ensuring analytics tables exist...')
        DailyAnalytics.__table__.create(bind=db.engine, checkfirst=True)
        UserAnalytics.__table__.create(bind=db.engine, checkfirst=True)
        print('Done: analytics tables created or already existed.')


if __name__ == '__main__':
    main()
