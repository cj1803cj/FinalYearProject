from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), index=True, unique=True)
    email = db.Column(db.String(50), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # use __repr__ method to change formatting of printed objects when debugging
    def __repr__(self):
        return '<User {}>'.format(self.username)    