import re

from app import create_app
from app import db


def _fill_rule(rule):
    url = rule
    url = re.sub(r"<(?:[^:>]+:)?int:([^>]+)>", "1", url)
    url = re.sub(r"<(?:[^:>]+:)?string:([^>]+)>", "1", url)
    url = re.sub(r"<(?:[^:>]+:)?path:([^>]+)>", "1", url)
    url = re.sub(r"<(?:[^:>]+:)?uuid:([^>]+)>", "1", url)
    url = re.sub(r"<(?:[^:>]+:)?float:([^>]+)>", "1", url)
    url = re.sub(r"<([^>]+)>", "1", url)
    return url


def _seed_minimal_data():
    from app.models.user import User
    from app.models.review import Review

    if not db.session.get(User, 1):
        user = User(username="testuser", email="test@example.com", password_hash="testhash")
        db.session.add(user)

    if not db.session.get(Review, 1):
        review = Review(
            title="Test Review",
            movie_name="Test Movie",
            overall_rating=5.0,
            overall_thoughts="ok",
            acting_rating=5.0,
            cast_selection_rating=5.0,
            pacing_rating=5.0,
            plot_rating=5.0,
            author_id=1,
        )
        db.session.add(review)

    db.session.commit()


def test_get_routes_do_not_return_500():
    app = create_app("testing")
    client = app.test_client()

    with app.app_context():
        db.create_all()
        _seed_minimal_data()

        rules = [rule for rule in app.url_map.iter_rules() if "static" not in rule.endpoint]

        for rule in rules:
            url = _fill_rule(rule.rule)
            response = client.get(url)
            assert response.status_code < 500, f"GET {url} returned {response.status_code} for endpoint {rule.endpoint}"
