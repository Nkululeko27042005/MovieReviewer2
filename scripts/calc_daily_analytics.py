"""Calculate platform daily analytics for a given date.

Usage:
    python scripts/calc_daily_analytics.py 2026-06-24
or:
    python scripts/calc_daily_analytics.py    # uses today
"""
import sys
from datetime import datetime, date

from app import create_app, db


def main():
    app = create_app()
    with app.app_context():
        from app.services.analytics_service import AnalyticsService

        if len(sys.argv) > 1:
            date_str = sys.argv[1]
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                print('Invalid date format, use YYYY-MM-DD')
                return
        else:
            date_obj = date.today()

        print(f'Calculating analytics for {date_obj}...')
        analytics = AnalyticsService.calculate_global_daily_analytics(date_obj)
        if analytics:
            print('Calculation complete. Analytics:')
            try:
                print(analytics.to_dict())
            except Exception:
                # Fallback print
                print('Analytics object created')
        else:
            print('No analytics object returned')


if __name__ == '__main__':
    main()
