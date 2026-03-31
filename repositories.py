from models import db, User, Task
from sqlalchemy import select

class UserRepository:
    def get_by_id(self, user_id):
        return db.session.get(User, user_id)

    def get_by_email(self, email):
        return db.session.scalar(select(User).where(User.email == email))

    def get_all_performers(self):
        return db.session.scalars(select(User).where(User.role == "performer")).all()

    def create(self, user):
        db.session.add(user)
        db.session.commit()

class TaskRepository:
    def get_all(self):
        return db.session.scalars(select(Task)).all()

    def get_by_user(self, user_id):
        return db.session.scalars(select(Task).where(Task.user_id == user_id)).all()

    def get_by_id(self, task_id):
        return db.session.get(Task, task_id)

    def save(self, task):
        db.session.add(task)
        db.session.commit()

    def delete(self, task):
        db.session.delete(task)
        db.session.commit()