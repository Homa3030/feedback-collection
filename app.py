from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    surname = db.Column(db.String(20), nullable=False)
    mail = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    type = db.Column(db.Integer, nullable=False)

    # 0 - DOE
    # 1 - Professor/TA
    # 2 - Student
    def __repr__(self):
        return '<User %r>' % self.id


@app.route("/login")
def login():
    return "Login page"


@app.route("/registration")
def reg():
    return "Registration page"


@app.route("/")
def home():
    return "Hello, Nursultan!"


if __name__ == "__main__":
    app.run(debug=True)
