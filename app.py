from flask import Flask, url_for, render_template, request, redirect, session, jsonify, json
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
    forms = db.relationship('FormTemplate', backref='user_form_temp')

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
    question_order = db.Column(db.Integer, default=0)
    # If question is open-ended then answers = {} (empty array)

class Answer(db.Model):
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    filler_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    answer = db.Column(db.String, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)

class FormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    questions = db.relationship('Question', backref='form_template_questions')
    visible = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    label = db.Column(db.String(32), nullable=False)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    answers = db.relationship('Answer', backref='form_answers')
    
##@app.route('/create_form', methods=['POST'])
def create_form_template(user, name):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
      
    new_template = FormTemplate()
    new_template.visible = False
    new_template.user_id = user
    new_template.label = name + str(new_template.id)
    db.session.add(new_template)
    db.session.commit()
    
    return str(new_template.id)

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

@app.route('/save_answer/<user_id>/<form_id>/<question_id>/<answer>', methods=['POST'])
def save_answer(user_id,form_id, question_id, answer):
    new_answ = Answer()
    new_answ.filler_id = user_id
    new_answ.question_id = question_id
    new_answ.form_id = form_id
    new_answ.answer = answer
    db.session.add(new_answ)
    db.session.commit()
    return "ok"

@app.route('/generate_form/<form_temp_id>', methods=['POST'])
def generate(form_temp_id):
    new_form = Form()
    new_form.template_id = form_temp_id
    db.session.add(new_form)
    db.session.commit()
    print(new_form.id)
    return jsonify({"form_id": new_form.id})


@app.route('/save_form_as_template/<form_id>/<name>', methods=['POST'])
def save_form_as_template(form_id, name):
    ## My way
    ## here we only change the visibilty of form template without duplicating form_template 
    ## and all questions of this form_template

    form_temp = FormTemplate.query.filter_by(id=form_id).first()
    form_temp.visible = True
    form_temp.label = str(name)
    db.session.commit()
    return "OK"

    ## Regina way
    ## here we create new form_template and also duplicate all questions(related to form_template with form_id)

    # form_template_id = Form.query.get(form_id).template_id

    # new_form_template = FormTemplate()
    # new_form_template.visible = True
    # db.session.add(new_form_template)

    # questions = FormTemplate.query.get(form_template_id).questions

    # for question in questions:
    #     new_question = Question()
    #     new_question.question = question.question
    #     new_question.answers = question.answers
    #     new_question.template_id = new_form_template.id
    #     db.session.add(new_question)
    # db.session.commit()

@app.route('/fills_form/<form_id>', methods=['GET'])
def get_all_questions(form_id):
    temp_form_id = Form.query.filter_by(id=form_id).first().template_id
    q_array = FormTemplate.query.get(temp_form_id).questions
    list = []
    for question in q_array:
        dic = {
            "id": question.id,
            "question": question.question,
            "answers": question.answers
        }
        list.append(dic)
        print(dic)
    return render_template('Survey.html', array=list, fid=form_id)


@app.route('/add_question', methods=['POST'])
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

    ret = db.session.query(func.max(Question.id)).scalar()
    print(ret)
    return jsonify({"id" : ret})

@app.route('/delete_question', methods=['POST'])
def delete_question():
    form_id = request.args.get('form_id')
    question_id = request.args.get('question_id')
    questions = FormTemplate.query.get(form_id).questions

    for question in questions:
        if int(question.id) == int(question_id):
            db.session.delete(question)
            db.session.commit()
            break
    return "Ok"

@app.route('/delete_template/<temp_id>', methods=['POST'])
def temp_delete(temp_id):
    temp = FormTemplate.query.get(temp_id)
    temp.visible = False
    db.session.commit()
    return "ok"


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



@app.route("/constructor/<user_id>")
def constructor(user_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    return render_template('questions constructor.html', title="Constructor", formID=create_form(user_id, "template"))


@app.route("/statistics/<user>")
def statistics(user):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    form_temps = FormTemplate.query.filter_by(user_id=user, visible= True).all()
    forms_array = []
    for temp in form_temps:
        forms = Form.query.filter_by(template_id=temp.id).all()
        label = temp.label
        i = 0
        for form in forms:
            dic = {
                "id": form.id,
                "label": label + '(' + str(form.id) + ')'
             }
            i += 1
            forms_array.append(dic)
    return render_template('statistics.html', title="Statistics", list= json.dumps(forms_array))

@app.route("/forms/<id>")
def forms(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    own_temp = FormTemplate.query.filter_by(user_id=id, visible=True).all()
    array = []
    for temp in own_temp:
        dic = {
            "id": temp.id,
            "label": temp.label
        }
        print(dic)
        array.append(dic)
    return render_template('forms.html', title="My Feedback Form", list=json.dumps(array))

@app.route("/Editor/<form_id>")
def editor(form_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    question_arr = Question.query.filter_by(template_id=form_id).all()
    array = []
    size = 0
    for temp in question_arr:
        dic = {
            "id": temp.id,
            "question": temp.question,
            "answers": temp.answers,
            "template_id": temp.template_id
        }
        size += 1
        print(dic)
        array.append(dic)
    return render_template('Editor.html', title="Edit", list=json.dumps(array), temp_id=form_id, size= size)

@app.route("/Responds/<form_id>", methods=['GET'])
def responds(form_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    form_template_id = Form.query.get(form_id).template_id
    print(form_template_id)
    answers = Form.query.get(form_id).answers
    question0 = FormTemplate.query.get(form_template_id).questions[0].id
    print(question0)
    users=[]
    answ_array=[]
    for answer in answers:
        if answer.question_id == question0:
            user = User.query.get(answer.filler_id)
            dic = {
                "id": answer.filler_id,
                "full_name" : user.name + " " + user.surname
            }
            users.append(dic)
    print(users)
    return render_template('Responds.html', title="Responds", user_list=json.dumps(users), fid=form_id)

@app.route("/Answers/<filler_id>/<form_id>")
def answers(filler_id, form_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.type != 0 and current_user.type != 1:
        abort(405)
        
    answers = Answer.query.filter_by(filler_id=filler_id, form_id=form_id).all()
    array = []
    for answer in answers:
        question_id = answer.question_id
        question = Question.query.get(question_id)
        dic = {
            "q_label": question.question,
            "ans_label": answer.answer
        }
        array.append(dic)
        print(dic)
    filler = User.query.get(filler_id)
    return render_template('Answers.html', title="Answers", list = json.dumps(array), name = filler.name + " " + filler.surname)
@app.route("/")
def home():
    return render_template('index.html', title='Home')


if __name__ == "__main__":
    app.secret_key = "123"
    app.run(debug=True)