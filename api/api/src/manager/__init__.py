from flask import Blueprint

manager = Blueprint("manager", __name__, url_prefix="/cors/manager")

from src.manager import routes
