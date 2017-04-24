from flask import Flask

from utils import find_graze
find_graze()

app = Flask(__name__)
