
from flask import Blueprint

mission = Blueprint("mission", __name__, url_prefix="/cors/mission")

from src.mission import routes