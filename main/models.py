from main import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from main import login
from hashlib import md5
from time import time
import jwt
from main import app



followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('following_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(15), index = True, unique = True)
    name = db.Column(db.String(15))
    email = db.Column(db.String(20), index = True, unique = True)
    password_hash = db.Column(db.String(30))
    last_seen = db.Column(db.DateTime, default = datetime.utcnow)
    about_me = db.Column(db.String(30))
    badge = db.Column(db.String(15), default = 'Rookie')
    banned = db.Column(db.Integer, default = 0)
    ban_reason = db.Column(db.String(30), default = '')
    dares = db.relationship('Dare', backref = 'user', lazy = 'dynamic')
    upvoted = db.relationship('Upvote', backref = 'user', lazy = 'dynamic')
    commented = db.relationship('Comment', backref = 'user', lazy = 'dynamic')
    following = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.following_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    my_reports = db.relationship('Report', backref = 'reporter', lazy = 'dynamic',foreign_keys = 'Report.reporter_id')
    reports_on_me = db.relationship('Report', backref = 'user', lazy = 'dynamic',foreign_keys = 'Report.profile_id')

    def __repr__(self):
        return self.username + ' profile'

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in = 600):
        return jwt.encode(
            {'reset_password':self.id, 'exp':time() + expires_in},
            app.config['SECRET_KEY'],algorithm = 'HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms = ['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def is_following(self, user):
        return self.following.filter(
            followers.c.following_id == user.id).count() > 0
        
    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def followed_posts(self):
        followed =  Dare.query.join(followers,
                    (followers.c.following_id == Dare.user_id)).filter(
                        followers.c.follower_id == self.id)
        own = Dare.query.filter_by(user = self)   
        return followed.union(own).order_by(Dare.timestamp.desc())
                          

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Dare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dare = db.Column(db.String(30), nullable = False)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    votes = db.Column(db.Integer, nullable = False, default = 0)
    banned = db.Column(db.Integer, default = 0)
    ban_reason = db.Column(db.String(30), default = '')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    upvotes = db.relationship('Upvote', backref = 'dare', lazy = 'dynamic')
    comments = db.relationship('Comment', backref = 'dare', lazy = 'dynamic')
    reports = db.relationship('Report', backref = 'dare', lazy = 'dynamic')

    def __repr__(self):
        return 'Dare by ' + self.user.name


class Upvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dare_id = db.Column(db.Integer, db.ForeignKey('dare.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return self.user.username + ' voted for ' + dare.dare


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(30), nullable = False)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    dare_id = db.Column(db.Integer, db.ForeignKey('dare.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return self.user.username + ' commented on ' + self.dare.dare


class Report(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text, nullable = False)
    seen = db.Column(db.Integer, default = 0)
    page_of_report = db.Column(db.String(30), nullable = False)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    action_taken = db.Column(db.String(30))
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dare_id = db.Column(db.Integer, db.ForeignKey('dare.id'))

    def __repr__(self):
        return 'Report by ' + str(self.reporter.username)   

