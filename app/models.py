from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

# User class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), index=True, unique=True)
    email = db.Column(db.String(50), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # use __repr__ method to change formatting of printed objects when debugging
    def __repr__(self):
        return '<User {}>'.format(self.username)

# Project class
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(60))
    description = db.Column(db.String(150))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    language = db.Column(db.String(15))
    git_url = db.Column(db.String(50))
    img_url = db.Column(db.String(50))

    def __repr__(self):
        return '<Project {}>'.format(self.title)

# function to load user from id for flask-login to store user in session
@login.user_loader
def load_user(id):
    return User.query.get(int(id))