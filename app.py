from flask import Flask, request, jsonify, render_template
from engine import recommend
from forms import LoginForm
import pandas as pd
import pickle

app = Flask(__name__)
app.config.from_pyfile('config.py')

# read second column of dataset to obtain project names
df = pd.read_csv('TopStaredRepositories.csv', usecols=[1])

# load model which has already been saved using pickle library
tfidf_vectorizer = pickle.load(open('tfidf_vectorizer.pickle', 'rb'))

# index endpoint
@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', title='Sign In', form=form)

# api endpoint
@app.route('/api/', methods =['POST'])
def process_request():
    user_input = request.get_json()

    title = user_input['Repository Name']

    recommended_projects = recommend(title, df, tfidf_vectorizer)

    return jsonify(recommended_projects)

if __name__ == '__main__':
    app.run()