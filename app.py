from flask import Flask, request, jsonify, render_template, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from engine import recommend
from forms import LoginForm
import pandas as pd
import pickle

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# read second column of dataset to obtain project names
df = pd.read_csv('TopStaredRepositories.csv', usecols=[1])

# load model which has already been saved using pickle library
tfidf_vectorizer = pickle.load(open('tfidf_vectorizer.pickle', 'rb'))

# index endpoint
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

# login endpoint
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # process form submission
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        # redirect user to index page
        return redirect(url_for('index'))
    # render login template if get request
    return render_template('login.html', title='Sign In', form=form)

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