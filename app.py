
from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, current_user, login_user, logout_user, UserMixin
from flask_migrate import Migrate
from flask import abort
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
    def repr(self):
        return '%s %s, %s' % (self.name, self.surname, self.mail)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    answers = db.Column(db.ARRAY(db.String), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    # If question is open-ended then answers = {} (empty array)

class Answer(db.Model):
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    filler_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    answer = db.Column(db.String, nullable=False)

class FormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questions = db.relationship('Question', backref='form_template_questions')
    visible = db.Column(db.Boolean, nullable=False)


class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/create_form', methods=['POST'])
def create_form():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

    new_template = FormTemplate()
    new_template.visible = False
    db.session.add(new_template)
    db.session.commit()

    new_form = Form()
    new_form.template_id = new_template.id
    db.session.add(new_form)
    db.session.commit()


    return str(new_form.id)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'))
    grades = db.relationship('Grade', backref='grade_for_res')

    @classmethod
    def calculate_average(cls, id):
        grades_arr = cls.query.get(id).grades
        count = len(grades_arr)

        if count == 0:
            return 0
        else:
            return sum([g.grade for g in grades_arr]) / count

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/fill_form/<form_id>', methods=['GET'])
def get_form_page(form_id):
    Form.query.get_or_404(form_id)
    return f'Here should be a page to fill the form {form_id}.'


@app.route('/get_relative_link/<form_id>', methods=['GET'])
def get_relative_link(form_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 2:
        abort(405)

    Form.query.get_or_404(form_id)
    return f'/fill_form/{form_id}'


@app.route('/save_form_as_template/<form_id>', methods=['POST'])
def save_form_as_template(form_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

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


@app.route('/add_question', methods=['GET'])
def add_question():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

    form_id = request.args.get('form_id')
    question = request.args.get('question')
    answers_string = request.args.get('answers')

    new_question = Question()
    new_question.question = question
    if answers_string is None:
        new_question.answers = {}
    else:
        answer_array = []
        answer_temp = ""
        i = 0
        while i != len(answers_string):
            if answers_string[i] == ',':
                answer_array.append(answer_temp)
                answer_temp = ""
                i += 1
                continue
            answer_temp += answers_string[i]
            i += 1
        if answer_temp != ",":
            answer_array.append(answer_temp)
        new_question.answers = answer_array


    new_question.template_id = form_id

    db.session.add(new_question)
    db.session.commit()
    
    return True


def delete_question(form_id, question_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

    questions = FormTemplate.query.get(form_id).questions

    for question in questions:
        if int(question.id) == int(question_id):
            db.session.delete(question)
            db.session.commit()
            break


def change_question(form_id, question_id, new_question_string, answers):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

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
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

    form_id = db.session.query(func.max(Form.id)).scalar()
    return render_template('questions constructor.html', title="Constructor", formID=form_id)


@app.route("/statistics")
def statistics():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)

    return render_template('statistics.html', title="Statistics")

@app.route("/forms")
def forms():
    return render_template('forms.html', title="My Feedback Form")

@app.route("/Editor")
def editor():
    return render_template('Editor.html', title="Edit")

@app.route("/Responds")
def responds():
    return render_template('Responds.html', title="Responds")
@app.route("/Answers")
def answers():
    return render_template('Answers.html', title="Answers")

@app.route("/")
def home():
    return render_template('index.html', title='Home')


if __name__ == "__main__":
    app.secret_key = "123"
    app.run(debug=True)