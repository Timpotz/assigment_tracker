from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import DeclarativeBase
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from forms import RegisterForm, AddClass, SubmitAssignment, LoginForm
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate


## DB CONFIG
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
## DB CONFIG
load_dotenv()
database_URI=os.getenv('DB_URI')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = database_URI
db.init_app(app)
Bootstrap5(app)
login_manager= LoginManager()
login_manager.init_app(app)

# Initialize Flask-Migrate
#migrate = Migrate(app, db)


class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ktp = Column(BigInteger, unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    # Add more fields as needed

class Class(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    # Add more fields as needed

class Assignment(db.Model):
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, db.ForeignKey('class.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, db.ForeignKey('user.id'))
    url = Column(String(255), nullable=False)
    student_name=Column(String(100), nullable=False)
    class_ = db.relationship('Class', backref=db.backref('assignments', cascade='all, delete-orphan'))
    # Add more fields as needed

with app.app_context():
    db.create_all()

def admin_user(func):
    @wraps(func)
    def check_if_admin(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            abort(403)  # Unauthorized
    return check_if_admin

@app.context_processor
def inject_is_admin():
    is_admin = current_user.is_authenticated and current_user.id == 1
    return dict(is_admin=is_admin)

@app.context_processor
def inject_is_authenticated():
    is_authenticated = current_user.is_authenticated
    return dict(is_authenticated=is_authenticated)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    classes=Class.query.all()
    return render_template('index.html',classes=classes)

@app.route('/login',methods=["POST","GET"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        user_exist=User.query.filter_by(email=email).first()
        is_password_correct=check_password_hash(user_exist.password, password)
        if user_exist and is_password_correct:
            login_user(user_exist)
            return redirect(url_for('home'))
        else:
            flash('Incorrect email / password','fail')
            redirect(url_for('login'))

    return render_template('login.html',form=form)

@app.route('/register',methods=["POST","GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        password=form.password.data
        hashed=generate_password_hash(password, method='scrypt', salt_length=16)
        user = User(
            name= form.name.data,
            email= form.email.data,
            password= hashed,
            ktp= int(form.ktp.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('You have registered successfully','success')
        return redirect(url_for('register'))

    return render_template('register.html',form=form)


@app.route('/addclass',methods=["POST","GET"])
@login_required
@admin_user
def add_class():
    form= AddClass()
    classes = Class.query.all()
    if form.validate_on_submit():
        newclass= Class(
            name=form.name.data
        )
        db.session.add(newclass)
        db.session.commit()
        flash('Class Added Successfully', 'success')
        return redirect(url_for('classes'))
    return render_template('addclass.html',form=form,classes=classes)

@app.route('/submit',methods=["POST","GET"])
@login_required
def submit_assignment():
    form= SubmitAssignment()
    classes = Class.query.all()
    if form.validate_on_submit():
        assignment=Assignment(
            class_id=form.class_id.data,
            student_name=current_user.name,
            url=form.url.data,
            student_id=current_user.id
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment Submitted Successfully', 'success')
        return redirect(url_for('submit_assignment'))
    return render_template('submitassignment.html',form=form,classes=classes)

@app.route('/class/<int:class_id>')
@login_required
@admin_user
def class_details(class_id):
    class_ = Class.query.get_or_404(class_id)
    classes = Class.query.all()
    assignments = Assignment.query.filter_by(class_id=class_id).all()
    students = []
    max_urls_per_student = 0
    for assignment in assignments:
        found = False
        for student in students:
            if student['name'] == assignment.student_name:
                student['urls'].append(assignment.url)
                max_urls_per_student = max(max_urls_per_student, len(student['urls']))
                found = True
                break
        if not found:
            students.append({'name': assignment.student_name, 'urls': [assignment.url]})
            max_urls_per_student = max(max_urls_per_student, 1)

    return render_template('class_details.html', class_=class_, students=students,
                           max_urls_per_student=max_urls_per_student,classes=classes)

@app.route('/my_assignments')
@login_required
def my_assignments():
    assignments = Assignment.query.filter_by(student_id=current_user.id).all()
    return render_template('my_assignments.html', assignments=assignments)

@app.route('/classes')
def classes():
    classes = Class.query.all()
    return render_template('class_list.html', classes=classes)

@app.route('/update_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def update_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    form = SubmitAssignment(obj=assignment)
    if form.validate_on_submit():
        assignment.url = form.url.data
        db.session.commit()
        flash('Assignment updated successfully', 'success')
        return redirect(url_for('my_assignments'))
    return render_template('update_assignment.html', form=form)

@app.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted successfully', 'success')
    return redirect(url_for('my_assignments'))

@app.route('/delete_class/<int:class_id>', methods=['POST'])
@login_required
@admin_user
def delete_class(class_id):
    class_delete = Class.query.get_or_404(class_id)
    db.session.delete(class_delete)
    db.session.commit()
    flash('Class deleted successfully', 'success')
    return redirect(url_for('classes'))

@app.route('/currentuser')
@login_required
def currentuser():
    name = current_user.name
    email = current_user.email
    id = current_user.id
    authenticated=current_user.is_authenticated
    return f'{name}, {email}, {id},{authenticated}'

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# def drop_tables():
#     # Drop specific tables
#     with app.app_context():
#         db.drop_all()
#     print('Tables dropped successfully')

if __name__ == '__main__':
    app.run()

