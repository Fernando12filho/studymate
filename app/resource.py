from flask import Blueprint
from .models import Topic, Note
from .extensions import db
from .models import Resource

bp = Blueprint('resource', __name__, url_prefix='/resource')

