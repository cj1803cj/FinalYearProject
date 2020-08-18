from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app
from app.forms import LoginForm
from app.models import User
from engine import recommend

import pandas as pd
import pickle



# read second column of dataset to obtain project names
df = pd.read_csv('TopStaredRepositories.csv', usecols=[1])

# load model which has already been saved using pickle library
tfidf_vectorizer = pickle.load(open('tfidf_vectorizer.pickle', 'rb'))

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
        # search db using username form data
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