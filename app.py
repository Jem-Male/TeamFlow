from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User
from sqlalchemy import select, or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ochen_sekretnyi_klych'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teamflow.db'
db.init_app(app)

@app.route('/')
def home():
    us = None
    user = session.get('user_id') 
    if user:
        us = db.session.scalar(select(User).where(user == User.id))
    
    return render_template('home.html', us = us)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5000)