from my_server import server, db, User, Job
from datetime import datetime

# add user
def add_user(username, password, email):
    with server.app_context():
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

def delete_user(username):
    with server.app_context():
        user_to_delete = User.query.filter_by(username=username).first()
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()

def check_user(username):
    with server.app_context():
        return User.query.filter_by(username=username).first()

print(check_user('2023-S1-US-17'))
