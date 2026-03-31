from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Task

class AuthService:
    def __init__(self, user_repo):
        self.user_repo = user_repo  

    def register(self, username, email, password):
        if self.user_repo.get_by_email(email):
            return None, "Пользователь с такой почтой уже существует"
        hashed = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed)
        self.user_repo.create(new_user)
        return new_user, None

    def login(self, email, password):
        user = self.user_repo.get_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user, None
        return None, "Неверная почта или пароль"

class TaskService:
    def __init__(self, task_repo, user_repo):
        self.task_repo = task_repo
        self.user_repo = user_repo

    def get_tasks_for_user(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if user.role == 'manager':
            return self.task_repo.get_all(), True # True значит "созданные" (режим менеджера)
        return self.task_repo.get_by_user(user_id), False

    def create_task(self, manager_id, title, description, performer_id):
        manager = self.user_repo.get_by_id(manager_id)
        if not manager or manager.role != 'manager':
            return None, "Только менеджер может создавать задачи"
        new_task = Task(title=title, description=description, user_id=performer_id)
        self.task_repo.save(new_task)
        return new_task, None

    def toggle_status(self, task_id, user_id):
        task = self.task_repo.get_by_id(task_id)
        user = self.user_repo.get_by_id(user_id)
        if task and (user.role == 'manager' or task.user_id == user_id):
            task.status = 'done' if task.status != 'done' else 'new'
            self.task_repo.save(task)
            return True
        return False

    def delete_task(self, task_id, user_id):
        user = self.user_repo.get_by_id(user_id)
        task = self.task_repo.get_by_id(task_id)
        if task and user.role == 'manager':
            self.task_repo.delete(task)
            return True
        return False
    
    def get_task_details(self, task_id):
        return self.task_repo.get_by_id(task_id)