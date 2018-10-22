from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import re
from hashutils import make_pw_hash, check_pw_hash
from datetime import datetime

match_username_password = re.compile(r"\w{3,20}\Z")

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'the1u33rdandbut'

class Blog(db.Model):
    """First persistent class"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(255))
    date_pub = db.Column(db.DateTime)
    date_upd = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner
        self.date_pub = datetime.utcnow()
        self.date_upd = datetime.utcnow()

class User(db.Model):
    """Owners of the blog posts"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    # whitelist pages that do not require logged in user;
    # must do this to avoid endless redirect loop on login
    allowed_routes = ['login', 'register', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        print(request.endpoint)
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash('Logged in')
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        error_bool = False
        username = request.form['username']
        password = request.form['password']
        vpassword = request.form['vpassword']

        if match_username_password.match(username) == None:
            error_bool = True
            flash('Invalid username; must be 3-20 alphanumeric chars', 'error')

        if match_username_password.match(password) == None:
            error_bool = True
            flash('Invalid password; must be 3-20 alphanumeric chars', 'error')

        if vpassword != password:
            error_bool = True
            flash('Passwords do not match', 'error')

        if error_bool:
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            flash('User "'+username+'" not available; please choose another', 'error')

    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/', methods=['GET'])
def index():
    users = User.query.all()
    return render_template('index.html', title="Build a Blog", authors=users)

@app.route('/blog', methods=['GET'])
def blog():
    post_id = request.args.get('id', "")
    user_id = request.args.get('user', "")

    if post_id != "":
        #get single post
        post = Blog.query.filter_by(id=post_id).first()
        return render_template('post_display.html', title="Build a Blog", post=post)
    
    if user_id != "":
        #get user list
        posts = Blog.query.filter_by(owner_id=user_id).all()
        author_name = User.query.get(user_id).username
        return render_template('post_list.html', title="Build a Blog", posts_for=author_name, posts=posts)

    #get all posts
    posts = Blog.query.order_by("Blog.id DESC").all()
    return render_template('post_list.html', title="Build a Blog", posts_for='Everyone', posts=posts)

@app.route('/newpost', methods=['GET', 'POST'])
def add_post():
    if request.method == 'GET':
        return render_template('add_post.html', title="Build a Blog")

    owner = User.query.filter_by(username=session['username']).first()

    error_msg = ""
    title = request.form['title']
    if title == "":
        error_msg = "Post title cannot be empty. "
        flash(error_msg, 'error')
    body = request.form['body']
    if body == "":
        error_msg = "Post body cannot be empty. "
        flash(error_msg, 'error')

    if error_msg == "":
        new_post = Blog(title, body, owner)
        db.session.add(new_post)
        db.session.commit()
        flash('Post added!')
        return redirect('/blog?id=' + str(new_post.id))
    else:
        return render_template('add_post.html', title="Build a Blog", post_title=title, post_body=body)


if __name__ == '__main__':
    app.run()