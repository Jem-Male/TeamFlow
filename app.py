from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Task
from sqlalchemy import select, or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ochen_sekretnyi_klych'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teamflow.db'
db.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        test = db.session.scalar(
            select(User).where(
                or_(
                    User.email == email,
                    User.username == username
                )
            )
        )
        
        if test:
            return render_template('register.html', err=True)
            
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            return f"Ошибка при создании: {e}"

    return render_template('register.html', err=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.session.scalar(select(User).where(User.email == email))
        
        if user is None:
            return render_template('login.html', err = 'Почта не найдена')
        
        elif not check_password_hash(user.password_hash, password):
            return render_template('login.html', err = 'Пароль не верный')

        session['user_id'] = user.id
        return redirect(url_for('profile'))
    
    return render_template('login.html', err = False)

@app.route('/profile')
def profile():
    client = session.get('user_id') or None
    if client is not None:
        user = db.session.scalar(select(User).where(User.id == client))
        return render_template('profile.html', user = user, task=False)
    return redirect(url_for('register'))

@app.route('/tasks')
def tasks():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('login'))
    
    user = db.session.get(User, user_id)
    if user.role == "manager":
        # Менеджер видит ВСЕ задачи всех пользователей
        tasks_list = db.session.scalars(select(Task)).all()
        return render_template('tasks.html', tasks=tasks_list, created=True)
    else:
        # Исполнитель видит только свои
        tasks_list = db.session.scalars(select(Task).where(Task.user_id == user.id)).all()
        return render_template('tasks.html', tasks=tasks_list, created=False)
    
    
@app.route('/create_task', methods=['GET','POST'])
def create_task():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    manager = db.session.scalar(select(User).where(User.id == user_id, User.role == 'manager'))
    
    if request.method == 'POST':
        if not manager:
            return "У вас нет прав для этого действия", 403
        
        title = request.form.get('title')
        description = request.form.get('description')
        performer_id = request.form.get('user_id')
        
        new_task = Task(
            title=title,
            description=description,
            user_id=performer_id 
        )
        
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('tasks')) # Переходим к списку задач

    if manager: 
        labors = db.session.scalars(select(User).where(User.role == "performer")).all()
        return render_template('created_task.html', manager=True, labors=labors)
    
    return render_template('created_task.html', manager=False, labors=False)

@app.route('/task/<int:task_id>/update_status', methods=['POST'])
def update_status(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Ищем задачу или выдаем 404, если её нет
    task = db.get_or_404(Task, task_id)
    user = db.session.scalar(select(User).where(User.id == user_id))

    # Проверка прав: менеджер может всё, исполнитель — только свои задачи
    if user.role == 'manager' or task.user_id == user.id:
        # Если статус уже done — можем вернуть в new (тоггл), 
        # но по твоему запросу просто ставим 'done'
        task.status = 'done' if task.status != 'done' else 'new'
        
        db.session.commit()
        return redirect(url_for('tasks'))

    return "У вас нет прав для изменения этой задачи", 403

@app.route('/task/<int:task_id>')
def task_detail(task_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    task = db.get_or_404(Task, task_id)
    return render_template('task_detail.html', task=task)

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    user_id = session.get('user_id')
    user = db.session.get(User, user_id)
    task = db.get_or_404(Task, task_id)
    
    if user.role == 'manager':
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('tasks'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5000)