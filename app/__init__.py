from flask import Flask

from utils import find_graze
find_graze()

from ui import app
