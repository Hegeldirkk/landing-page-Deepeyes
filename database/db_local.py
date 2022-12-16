"""
Program: Alx Afrique
Auteur: Ikary Ryann
test for a local -MySQL- database connection
make sure your virtualenv is activated!
make sure you have "started all" in XAMPP!
code below works for a MySQL database in XAMPP
- NOT XAMPP VM - on Mac OS
"""

import pymysql
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
from sqlalchemy.sql import func
from passlib.apps import custom_app_context as pwd_context
from flask import Flask, abort, request, jsonify, g, url_for, make_response

app = Flask(__name__)

# assumes you did not create a password for your database
# and the database username is the default, 'root'
# change if necessary
username = 'userDeepeyes'
password = 'Mysql2022!'
userpass = 'mysql+pymysql://' + username + ':' + password + '@'
server  = '127.0.0.7'
# change to YOUR database name, with a slash added as shown
dbname   = '/deepeyes'

# this socket is going to be very different on a WINDOWS computer
# try 'C:/xampp/mysql/mysql.sock'
socket   = '?unix_socket=/var/run/mysqld/mysqld.sock'

# put them all together as a string that shows SQLAlchemy where the database is
app.config['SQLALCHEMY_DATABASE_URI'] = userpass + server + dbname + socket

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

# NOTHING BELOW THIS LINE NEEDS TO CHANGE
# this route will test the database connection and nothing more
class Hacker(db.Model):
    __tablename__ = 'hacker'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    H_password = db.Column(db.String(128))
    age = db.Column(db.Integer)
    picture = db.Column(db.String(300))
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())

    def __repr__(self):
        return '<Hacker %r>' % self.username

    def hash_passwd(self, password):
        self.H_password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.H_password)

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    C_password = db.Column(db.String(128))
    logo = db.Column(db.String(300))
    created_at = db.Column(db.DateTime(timezone=True),
                           server_default=func.now())
    posts = db.relationship('Post', backref='company', lazy=True)

    def __repr__(self):
        return '<Company %r>' % self.name

    def hash_passwd(self, password):
        self.C_password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.C_password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False,
        default=datetime.utcnow)
    category = db.Column(db.String(80), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'),
        nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'

@app.route('/api/hacker', methods = ['POST'])
def new_hacker():
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    if username is None or password is None or email is None:
        response = jsonify({ 'error': 'true', 'message': 'please fill all input'}), 400 # error
        return response
    if Hacker.query.filter_by(username = username).first() is not None:
        response = jsonify({ 'error': 'true', 'message': 'existing username'}), 400 # existing user
        return response
    if Hacker.query.filter_by(email = email).first() is not None:
        response = jsonify({ 'error': 'true', 'message': 'existing email'}), 400 # existing user
        return response
    user = Hacker(username = username, email = email)
    user.hash_passwd(password)
    db.session.add(user)
    db.session.commit()
    data = {'error': 'false', 'username': user.username, 'email': user.email, 'password': user.H_password, 'created_at': user.created_at}
    return jsonify(data), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

@app.route('/api/company', methods = ['POST'])
def new_company():
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
    if name is None or password is None or email is None:
        response = jsonify({ 'error': 'true', 'message': 'please fill all input'}), 400 # error
        return response
    if Company.query.filter_by(name = name).first() is not None:
        response = jsonify({ 'error': 'true', 'message': 'existing name'}), 400 # existing user
        return response
    if Company.query.filter_by(email = email).first() is not None:
        response = jsonify({ 'error': 'true', 'message': 'existing email'}), 400 # existing user
        return response
    user = Company(name = name, email = email)
    user.hash_passwd(password)
    db.session.add(user)
    db.session.commit()
    data = {'error': 'false','name': user.name, 'email': user.email, 'password': user.C_password, 'created_at': user.created_at}
    return jsonify(data), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

@app.route('/api/hacker/<int:id>')
def get_user(id):
    user = Hacker.query.get(id)
    if not user:
        abort(400)
    data = {'username': user.username, 'email': user.email, 'password': user.H_password}
    return jsonify(data)

@app.route('/')
def testdb():
    try:
        db.session.query('1').from_statement(text('SELECT 1')).all()
        return '<h1>It works.</h1>'
    except Exception as e:
        # see Terminal for description of the error
        print("\nThe error:\n" + str(e) + "\n")
        return '<h1>Something is broken.</h1>'


if __name__ == '__main__':
    app.run(debug=True)
