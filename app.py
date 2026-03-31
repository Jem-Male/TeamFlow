from flask import Flask, render_template, request, redirect, url_for, session
from models import db
from repositories import UserRepository, TaskRepository
from services import AuthService, TaskService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ochen_sekretnyi_klych'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teamflow.db'
db.init_app(app)

user_repo = UserRepository()
task_repo = TaskRepository()
auth_service = AuthService(user_repo)
task_service = TaskService(task_repo, user_repo)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user, err = auth_service.register(
            request.form.get('username'),
            request.form.get('email'),
            request.form.get('password')
        )
        if err: return render_template('register.html', err=True)
        session['user_id'] = user.id
        return redirect(url_for('profile'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, err = auth_service.login(request.form.get('email'), request.form.get('password'))
        if err: return render_template('login.html', err=err)
        session['user_id'] = user.id
        return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    user = user_repo.get_by_id(user_id)
    return render_template('profile.html', user=user)

@app.route('/tasks')
def tasks():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    tasks_list, is_manager = task_service.get_tasks_for_user(user_id)
    return render_template('tasks.html', tasks=tasks_list, created=is_manager)

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    user_id = session.get('user_id')
    if not user_id: return redirect(url_for('login'))
    
    if request.method == 'POST':
        _, err = task_service.create_task(
            user_id, request.form.get('title'), 
            request.form.get('description'), request.form.get('user_id')
        )
        if err: return err, 403
        return redirect(url_for('tasks'))

    labors = user_repo.get_all_performers()
    user = user_repo.get_by_id(user_id)
    return render_template('created_task.html', manager=(user.role == 'manager'), labors=labors)

@app.route('/task/<int:task_id>')
def task_detail(task_id):
    if not session.get('user_id'): return redirect(url_for('login'))
    task = task_service.get_task_details(task_id)
    if not task: return "Задача не найдена", 404
    return render_template('task_detail.html', task=task)

@app.route('/task/<int:task_id>/update_status', methods=['POST'])
def update_status(task_id):
    if task_service.toggle_status(task_id, session.get('user_id')):
        return redirect(url_for('tasks'))
    return "Отказ в доступе", 403

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if task_service.delete_task(task_id, session.get('user_id')):
        return redirect(url_for('tasks'))
    return "Отказ в доступе", 403

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)