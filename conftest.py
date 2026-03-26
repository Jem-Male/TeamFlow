import pytest
from app import app
from models import db


@pytest.fixture
def client():
    app.config["TESTING"] = True

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        client = app.test_client()
        yield client
        db.drop_all()