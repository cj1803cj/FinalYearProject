import os

class Config(object):
    JSON_SORT_KEYS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'