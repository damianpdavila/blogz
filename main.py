from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:d03p29d64@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'the1u33rdandbut'

class Blog(db.Model):
    """First persistent class"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    """Owners of the blog posts"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    # whitelist pages that do not require logged in user;
    # must do this to avoid endless redirect loop on login
    allowed_routes = ['login', 'register', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'email' not in session:
        print(request.endpoint)
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash('Logged in')
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['vpassword']

        # TODO validate the data

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            # TODO return dup user message
            return "<h1>User email already exists</h1>"

    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')

@app.route('/', methods=['GET'])
@app.route('/blog', methods=['GET'])
def index():

    post_id = request.args.get('id', "")

    # if no post id passed in query parms, then retrieve all
    if post_id == "":
        posts = Blog.query.all()
        return render_template('post_list.html', title="Build a Blog", posts=posts)

    # if post id passed in query parms, then retrieve that one
    post = Blog.query.filter_by(id=post_id).first()

    return render_template('post_display.html', title="Build a Blog", post_title=post.title, post_body=post.body, post_id=post.id)


@app.route('/newpost', methods=['GET', 'POST'])
def add_post():

    if request.method == 'GET':
        return render_template('add_post.html', title="Build a Blog")

    owner = User.query.filter_by(email=session['email']).first()

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