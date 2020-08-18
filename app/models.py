from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login
from hashlib import md5

# association table for followers, storing no additional data therefore no class is needed
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# User class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), index=True, unique=True)
    email = db.Column(db.String(50), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # add self-referential relationship for list of users the user follows
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # return user avatar from gravatar service
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=retro&s={}'.format(digest, size)

    # follow user logic
    def follow(self, user):
        # perform check to avoid duplicating db entry
        if not self.is_following(user):
            self.followed.append(user)

    # unfollow user logic
    def unfollow(self, user):
        # perform check to avoid duplicating db entry
        if self.is_following(user):
            self.followed.remove(user)

    # check if user is following logic
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    # get list of posts made by users who the user follows
    def followed_posts(self):
        fololwed = Project.query.join(
            followers, (followers.c.followed_id == Project.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Project.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Project.timestamp.desc())

    # use __repr__ method to change formatting of printed objects when debugging
    def __repr__(self):
        return '<User {}>'.format(self.username)
# end of User class

# Project class
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(60))
    description = db.Column(db.String(150))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    language = db.Column(db.String(15))
    git_url = db.Column(db.String(50))
    img_url = db.Column(db.String(50))

    def __repr__(self):
        return '<Project {}>'.format(self.title)
# end of Project class

# function to load user from id for flask-login to store user in session
@login.user_loader
def load_user(id):
    return User.query.get(int(id))