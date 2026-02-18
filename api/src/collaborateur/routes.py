from flask import jsonify, make_response
from src.collaborateur import collab

@collab.route('/test/')
def test():
    
    
    return make_response(jsonify({"response": "That's a test"}))
