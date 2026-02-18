from flask import Blueprint

client = Blueprint('client', __name__, url_prefix='/cors/client')

from src.customer import routes