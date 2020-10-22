# feedback-collection

This is a Feedback Collection project for FSE course.

## After the database models are updated, run:
```
python -m flask db migrate
python -m flask db upgrade
```

This will create a migration with up-to-date data models and modify the database correspondingly.