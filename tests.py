import pytest
from app import app, db
from models import User, Task
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Настройка тестового клиента."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False # Отключаем CSRF для тестов
    
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.drop_all()

@pytest.fixture
def setup_users(client):
    """Создает менеджера и исполнителя."""
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
    db.session.add(manager)
    db.session.add(performer)
    db.session.commit()
    return manager.id, performer.id

def test_home_page(client):
    """Главная страница доступна."""
    response = client.get('/')
    assert response.status_code == 200

def test_profile_redirects_unauthenticated(client):
    """Редирект на регистрацию, если не залогинен (как в твоем новом app.py)."""
    response = client.get('/profile')
    assert response.status_code == 302
    assert "/register" in response.headers["Location"]

def test_register_user(client):
    """Регистрация теперь ведет в Профиль (проверяем это)."""
    response = client.post('/register', data={
        "username": "tester",
        "email": "tester@mail.com",
        "password": "password"
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"] # В новом коде редирект в профиль

def test_login_success(client, setup_users):
    """Проверка входа через AuthService (вызывается в роуте)."""
    response = client.post('/login', data={
        "email": "manager@mail.com",
        "password": "1234"
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]

def test_manager_can_create_task(client, setup_users):
    """Менеджер создает задачу через TaskService."""
    manager_id, performer_id = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = manager_id
        
    response = client.post('/create_task', data={
        "title": "SOLID Task",
        "description": "Test SOLID",
        "user_id": performer_id
    })
    
    assert response.status_code == 302 # Успешный редирект на /tasks
    
    with app.app_context():
        task = db.session.scalar(db.select(Task).where(Task.title == "SOLID Task"))
        assert task is not None
        assert task.user_id == performer_id

def test_performer_cannot_create_task(client, setup_users):
    """Исполнитель получает 403 (проверка логики в TaskService)."""
    _, performer_id = setup_users
    
    with client.session_transaction() as sess:
        sess['user_id'] = performer_id
        
    response = client.post('/create_task', data={
        "title": "Illegal Task",
        "user_id": performer_id
    })
    
    assert response.status_code == 403

def test_update_task_status(client, setup_users):
    """Смена статуса (логика TaskService.toggle_status)."""
    manager_id, performer_id = setup_users
    
    # Создаем задачу вручную для теста
    with app.app_context():
        t = Task(title="Status Task", user_id=performer_id)
        db.session.add(t)
        db.session.commit()
        task_id = t.id

    with client.session_transaction() as sess:
        sess['user_id'] = performer_id
        
    response = client.post(f'/task/{task_id}/update_status')
    assert response.status_code == 302

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.status == "done"