from models import User

def register_user(client, username="test", email="test@mail.com", password="123456"):
    return client.post("/register", data={
        "username": username,
        "email": email,
        "password": password
    })

def test_register_success(client):
    response = register_user(client)
    assert response.status_code == 302
    user = User.query.filter_by(email="test@mail.com").first()
    assert user is not None

def test_register_duplicate(client):
    register_user(client)
    response = register_user(client)
    assert response.status_code == 200

def test_login_success(client):

    register_user(client)
    response = client.post("/login", data={
        "email": "test@mail.com",
        "password": "123456"
    })
    assert response.status_code == 302


def test_login_sets_session(client):
    register_user(client)
    client.post("/login", data={
        "email": "test@mail.com",
        "password": "123456"
    })

    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_login_wrong_password(client):

    register_user(client)

    response = client.post("/login", data={
        "email": "test@mail.com",
        "password": "wrong"
    })
    assert response.status_code == 200


def test_login_user_not_found(client):

    response = client.post("/login", data={
        "email": "no@mail.com",
        "password": "123456"
    })

    assert response.status_code == 200