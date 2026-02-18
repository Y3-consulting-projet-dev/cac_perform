from flask import Blueprint

collab = Blueprint("collab", __name__, url_prefix="/cors/collab")

from src.collaborateur import routes
