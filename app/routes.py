from flask import request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ProjectForm, EmptyForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Project
from app.email import send_password_reset_email
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
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(title=form.title.data, owner=current_user)
        db.session.add(project)
        db.session.commit()
        flash('Project created!')
        # redirect to home page to avoid inserting duplicate posts
        # if a user refreshes after submitting the form
        # (post/redirect/get pattern)
        return redirect(url_for('index'))
    
    # get page number from request
    page = request.args.get('page', 1, type=int)
    projects = current_user.followed_projects().paginate(page, app.config['POSTS_PER_PAGE'], False)

    # ternary operators to assign next page url and previous
    # page url if there are more projects to display
    next_url = url_for('index', page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('index', page=projects.prev_num) \
        if projects.has_prev else None
    return render_template('index.html', title='Home', form=form, projects=projects.items, next_url=next_url, prev_url=prev_url)
# end of index endpoint


# explore endpoint
@app.route('/explore')
@login_required
def explore():
    # get page number from request
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)

    # ternary operators to assign next page url and previous
    # page url if there are more projects to display
    next_url = url_for('explore', page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('explore', page=projects.prev_num) \
        if projects.has_prev else None
    return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url)
# end of explore endpoint


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
# end of login endpoint


# logout endpoint
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
# end of logout endpoint


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
# end of register endpoint


# user profile endpoint
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    following = user.followed.all()
    followers = user.followers.all()
    page = request.args.get('page', 1, type=int)
    projects = user.projects.order_by(Project.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('user', username=user.username, page=projects.prev_num) \
        if projects.has_prev else None
    form = EmptyForm()
    return render_template('user.html', title=f'{user.username}\'s profile', user=user, following=following, followers=followers, projects=projects.items, next_url=next_url, prev_url=prev_url, form=form)
# end of user profile endpoint


# user popup endpoint
@app.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)
# end of user popup endpoint


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
# end of edit profile endpoint


# follow user endpoint
# TODO combine code for follow and unfollow routes to follow DRY best practices
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are now following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
# end of follow user endpoint


# unfollow user endpoint
@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are no longer following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
# end of unfollow user endpoint


# reset password request endpoint
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)
# end of reset password request endpoint


# reset password endpoint
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # if user is already signed in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    # redirect to index if token is invalid
    if not user:
        return redirect(url_for('index'))
    # present form to reset password if token is valid
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
# end of reset password endpoint


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