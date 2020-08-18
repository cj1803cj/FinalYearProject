from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User
from engine import recommend

import pandas as pd
import pickle



# read second column of dataset to obtain project names
df = pd.read_csv('TopStaredRepositories.csv', usecols=[1])

# load model which has already been saved using pickle library
tfidf_vectorizer = pickle.load(open('tfidf_vectorizer.pickle', 'rb'))

# call method before processing any requests
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# index endpoint
@app.route('/')
@app.route('/index')
@login_required
def index():
    projects = [
        {
            'owner': {'username': 'Chris'},
            'title': 'Recommending projects on the web'
        },
        {
            'owner': {'username': 'Emily'},
            'title': 'Recommending more projects'
        }
    ]
    return render_template('index.html', title='Home', projects=projects)

# login endpoint
@app.route('/login', methods=['GET', 'POST'])
def login():
    # redirect user to index page if they are already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    # process form submission
    if form.validate_on_submit():
        # search db for user by username form data
        user = User.query.filter_by(username=form.username.data).first()
        # conditional for unsuccessful username search OR check_password returns false
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        # successful login
        login_user(user, remember=form.remember_me.data)

        # set next_page to next argument from request to handle redirects from login_required pages
        next_page = request.args.get('next')
        # redirect user to index page if no next argument was found, or if next argument contains a URL with another domain
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        # redirect user to next page after successful login
        return redirect(next_page)

    # render login template if get request
    return render_template('login.html', title='Sign In', form=form)

# logout endpoint
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# register endpoint
@app.route('/register', methods=['GET', 'POST'])
def register():
    # redirect user to index page if they are already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    # process form submission
    if form.validate_on_submit():
        # create new user object with form data as arguments
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # add user to db
        db.session.add(user)
        db.session.commit()
        flash('You have successfully registered!')
        return redirect(url_for('login'))

    # render register template if get request
    return render_template('register.html', title='Register', form=form)

# user profile endpoint
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    projects = [
        {'owner': user, 'title': 'Project #1'},
        {'owner': user, 'title': 'Project #2'},
    ]
    return render_template('user.html', user=user, projects=projects)

# edit profile endpoint
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

# api endpoint
@app.route('/api/', methods =['POST'])
def process_request():
    # get user input
    user_input = request.get_json()

    # save project name as title
    title = user_input['Repository Name']

    # call recommend function with necessary arguments
    recommended_projects = recommend(title, df, tfidf_vectorizer)

    return jsonify(recommended_projects)

if __name__ == '__main__':
    app.run()