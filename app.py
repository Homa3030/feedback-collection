from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, UserMixin
from flask_migrate import Migrate
import os


db = SQLAlchemy()
login_manager = LoginManager()
app = Flask(__name__, instance_relative_config=False)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('FEEDBACK_DB', 'error')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)

# Initialize Plugins
db.init_app(app)
login_manager.init_app(app)
with app.app_context():
    db.create_all()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    surname = db.Column(db.String(20), nullable=False)
    mail = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    type = db.Column(db.Integer, nullable=False)

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    # 0 - DOE
    # 1 - Professor/TA
    # 2 - Student
    def __repr__(self):
        return '%s %s, %s' % (self.name, self.surname, self.mail)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    answers = db.Column(db.ARRAY(db.String), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    #If question is open-ended then answers = {} (empty array)

class FormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questions = db.relationship('Question', backref='form_template')
    visible = db.Column(db.Boolean, nullable=False)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'))


@app.route('/save_form_as_template/<form_id>', methods=['POST'])
def save_form_as_template(form_id):
    form_template_id = Form.query.get(form_id).template_id

    new_form_template = FormTemplate()
    new_form_template.visible = True
    db.session.add(new_form_template)

    questions = FormTemplate.query.get(form_template_id).questions
    
    for question in questions:
        new_question = Question()
        new_question.question = question.question
        new_question.answers = question.answers
        new_question.template_id = new_form_template.id
        db.session.add(new_question)

    db.session.commit()


def add_question(form_id, question, answers):
    new_question = Question()
    new_question.question = question
    new_question.answers = answers
    new_question.template_id = form_id

    db.session.add(new_question)
    db.commit()


def delete_question(form_id, question_id):
    questions = FormTemplate.query.get(form_id).questions

    for question in questions:
        if int(question.id) == int(question_id):
            db.session.delete(question)
            db.session.commit()
            break


def change_question(form_id, question_id, new_question_string, answers):
    questions = FormTemplate.query.get(form_id).questions
    for question in questions:
        if int(question.id) == int(question_id):
            question.question = new_question_string
            question.answers = answers
            db.session.commit()
            break
   


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', title='Login')
    else:
        mail = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(mail=mail, password=password).first()
        if user is not None:
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('incorrect.html', title='Invalid credentials')



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/constructor")
def constructor():
    return render_template('questions constructor.html', title="Constructor")

@app.route("/statistics")
def statistics():
    return render_template('statistics.html', title="Statistics")
@app.route("/")
def home():
    return render_template('index.html', title='Home')


if __name__ == "__main__":
    app.secret_key = "123"
    app.run(debug=True)
