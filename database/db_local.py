"""
Program: Alx Afrique
Auteur: Ikary Ryann
test for a local -MySQL- database connection
"""

import pymysql
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
from sqlalchemy.sql import func
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, abort, request, jsonify, g, url_for, make_response
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import json
from bson import json_util
from sqlalchemy_serializer import SerializerMixin

app = Flask(__name__)

# assumes you did not create a password for your database
# and the database username is the default, 'root'
# change if necessary
username = 'userDeepeyes'
password = ''
userpass = 'mysql+pymysql://' + username + ':' + password + '@'
server = '127.0.0.1'
# change to YOUR database name, with a slash added as shown
dbname = '/deepeyes'

# this socket is going to be very different on a WINDOWS computer
# try 'C:/xampp/mysql/mysql.sock'
socket = '?unix_socket=/var/run/mysqld/mysqld.sock'

# put them all together as a string that shows SQLAlchemy where the database is
app.config['SQLALCHEMY_DATABASE_URI'] = userpass + server + dbname + socket
app.config['SECRET_KEY'] = 'le meilleur Arbitre de sa generation'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# NOTHING BELOW THIS LINE NEEDS TO CHANGE
# this route will test the database connection and nothing more


class Users(db.Model, SerializerMixin):
    __tablename__ = 'users'

    serialize_only = ('id', 'username', 'name', 'email', 'password',
                      'picture', 'role', 'age', 'created_at',)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(155))
    password = db.Column(db.String(128))
    age = db.Column(db.Integer)
    role = db.Column(db.String(38), nullable=False)
    picture = db.Column(db.String(300))
    verified = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    posts = db.relationship('Post', backref='users', lazy=True)

    def __repr__(self):
        return '<Hacker %r>' % self.username

    def hash_passwd(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration=3600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            print('ok error')
            return None
        user = Users.query.get(data['id'])
        return user


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(80), nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'


@auth.verify_password  # hacker verification auth login
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = Users.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = Users.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            data = {'error': 'true', 'message': 'Incorrect Authentification'}
            response = jsonify(data), 400  # existing user
            return response
    g.user = user
    return True


@app.route('/api/users', methods=['POST'])
def new_users():
    data = {}
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    name = request.json.get('name')
    role = request.json.get('role')
    if username is None or password is None or email is None or role is None:
        data = {'error': 'true', 'message': 'please fill all input'}
        response = jsonify(data), 400  # error
        return response
    if Users.query.filter_by(username=username).first() is not None:
        data = {'error': 'true', 'message': 'existing username'}
        response = jsonify(data), 400  # existing user
        return response
    if Users.query.filter_by(email=email).first() is not None:
        data = {'error': 'true', 'message': 'existing email'}
        response = jsonify(data), 400  # existing user
        return response
    user = Users(username=username, email=email, name=name, role=role,
                 verified=False)
    user.hash_passwd(password)
    db.session.add(user)
    db.session.commit()
    data = {'username': user.username, 'email': user.email, "role": user.role,
            'password':  user.password, 'verified': user.verified,
            'created_at': user.created_at, 'name': user.name}
    ok = {'error': 'false', "data": data}
    return jsonify(ok), 201, {'Location': url_for('get_user',
                              id=user.id, _external=True)}


@app.route('/api/users/<int:id>')
def get_user(id):
    user = Users.query.get(id)
    if not user:
        abort(400)
    data = {'username': user.username, 'email': user.email,
            'password': user.password}
    return jsonify(data)


@app.route('/api/users/login')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(3600)
    data = {'token': token.decode('ascii'), 'error': 'false', 'duration': 3600}
    return jsonify(data)


@app.route('/api/users/info')
@auth.login_required
def get_users():
    try:
        # result = g.user.to_dict()
        data = {'error': 'false', 'data': g.user.to_dict()}
    except AttributeError:
        data = {'error': 'true', 'message': g.user.to_dict()}
    return jsonify(data)


@app.route('/api/post/create', methods=['POST'])
@auth.login_required
def create_post():
    title = request.form.get('title', type=None)
    body = request.form.get('body', type=None)
    category = request.form.get('category', type=None)
    user_id = g.user.id
    if title == '' or body == '' or category == '':
        data = {'error': 'true', 'message': '🙄 please fill all input'}
        response = jsonify(data), 400  # error
        return response
    post = Post(title=title, body=body, category=category, users_id=user_id)
    db.session.add(post)
    db.session.commit()
    data = {'title': post.title, 'body': post.body, "user_id": post.users_id,
            'category':  post.category, 'id': post.id}
    ok = {'error': 'false', "data": data}
    return jsonify(ok), 201,


@app.route('/')
def index():
    return {'error🚦': 'false', 'message': '🚦Welcome to DeepEyes APIs 🤛👌'}


@app.errorhandler(404)
def page_not_found(error):
    return jsonify({'error': 'true', 'message': '🚦Route don\'t exist 👀👁'}), 404


if __name__ == '__main__':
    app.run(debug=True)
