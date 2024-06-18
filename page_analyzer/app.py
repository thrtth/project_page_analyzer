import os

from flask import Flask
from flask.cli import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
