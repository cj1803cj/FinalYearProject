from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
# tell flask-login where to find login function
login.login_view = 'login'

# import routes at bottom to avoid circular imports as a result
# of routes also importing the app module
from app import routes, models