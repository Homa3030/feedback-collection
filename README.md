# feedback-collection

This is a Feedback Collection project for FSE course.

## After the database models are updated, run:
```
python -m flask db migrate
python -m flask db upgrade
```

This will create a migration with up-to-date data models and modify the database correspondingly.

if you have some problems with code execution:
Firstly, download and install PostgesSQL from the official site. Set a password for postres(you will need it later).
Secondly, create Environment Variable with the name FEEDBACK_DB and value: postgreesql://postgres:<your_password_of_postgres>@localhost/feedback   (remove angle brackets)
Thirdly, If you have problem with Migrate library, then execute in terminal: pip install Flask-Migrate
Fourthly, If you still have problem with the long Traceback, then go to pgadmin4 (http://127.0.0.1:50841/browser/) and create database "feedback", if you have problem with database creation (OperationalError) try to execute: CREATE DATABASE feedback TEMPLATE template0.