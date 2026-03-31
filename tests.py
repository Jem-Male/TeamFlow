import pytest
from app import app, db
from models import User, Task
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Создает тестового клиента с базой данных в оперативной памяти."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def setup_users(client):
    """Создает двух пользователей: менеджера и исполнителя, возвращает их ID."""
    manager = User(
        username="manager_test", 
        email="manager@mail.com", 
        password_hash=generate_password_hash("1234"), 
        role="manager"
    )
    performer = User(
        username="performer_test", 
        email="performer@mail.com", 
        password_hash=generate_password_hash("1234"), 
        role="performer"
    )
    db.session.add_all([manager, performer])
    db.session.commit()
    return manager.id, performer.id

def test_home_page(client):
    """Проверка доступности главной страницы."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"TeamFlow" in response.data

def test_profile_redirects_unauthenticated(client):
    """Незалогиненный пользователь не должен попасть в профиль."""
    response = client.get('/profile')
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]


def test_register_user(client):
    """Проверка успешной регистрации нового пользователя."""
    response = client.post('/register', data={
        "username": "new_guy",
        "email": "new@mail.com",
        "password": "securepassword"
    })
    assert response.status_code == 302 # Редирект на home
    
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "new@mail.com"))
        assert user is not None
        assert user.role == "performer"

def test_logout(client, setup_users):
    """Проверка выхода из аккаунта."""
    manager_id, _ = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = manager_id
        
    response = client.get('/logout')
    assert response.status_code == 302
    
    with client.session_transaction() as sess:
        assert 'user_id' not in sess



def test_tasks_page_access(client, setup_users):
    """Проверка, что авторизованный пользователь может зайти в список задач."""
    _, performer_id = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = performer_id
        
    response = client.get('/tasks')
    assert response.status_code == 200

def test_manager_can_create_task(client, setup_users):
    """Проверка: менеджер может создать задачу."""
    manager_id, performer_id = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = manager_id
        
    response = client.post('/create_task', data={
        "title": "Сделать бекенд",
        "description": "Написать API на Flask",
        "user_id": performer_id
    })
    
    assert response.status_code == 302
    
    with app.app_context():
        task = db.session.scalar(db.select(Task).where(Task.title == "Сделать бекенд"))
        assert task is not None
        assert task.user_id == performer_id
        assert task.status == "new"

def test_performer_cannot_create_task(client, setup_users):
    """Проверка: обычный исполнитель получает ошибку 403 при попытке создать задачу."""
    _, performer_id = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = performer_id
        
    response = client.post('/create_task', data={
        "title": "Хакнуть систему",
        "description": "...",
        "user_id": performer_id
    })
    
    assert response.status_code == 403

def test_update_task_status(client, setup_users):
    """Проверка переключения статуса задачи."""
    manager_id, performer_id = setup_users
    
    with app.app_context():
        new_task = Task(title="Тестовая задача", user_id=performer_id)
        db.session.add(new_task)
        db.session.commit()
        task_id = new_task.id

    with client.session_transaction() as sess:
        sess['user_id'] = performer_id
        
    response = client.post(f'/task/{task_id}/update_status')
    assert response.status_code == 302

    with app.app_context():
        updated_task = db.session.get(Task, task_id)
        assert updated_task.status == "done"