from os import name
from xml.dom.minidom import Document
from flask import jsonify, make_response, request
from src.model import Client
from src.customer import client
from bson import ObjectId


@client.get('/afficher_clients/')
def show_cust():

    inst = Client()

    new_cust = inst.afficher_clients()

    if new_cust:
        return make_response(jsonify({"response": new_cust}), 200)
    return make_response(jsonify({"response": []}), 200)


@client.get('/info_client/<id>')
def show_info(id):

    id_str = str(id)
    _id = ObjectId(id_str)

    clit = Client()

    info = clit.info_client(id_clit=_id)

    # Retourner toutes les missions du client
    missions_client = clit.afficher_missions(id_str)

    if info:
        return make_response(jsonify({"response": {"info": info, "missions": missions_client}}), 200)
    else:
        return make_response(jsonify({"response": "Vide"}), 201)


@client.post('/nouveau_client/')
def new_cust():

    data = request.get_json()

    clit = Client()

    new_customer = clit.ajouter_client(data=data)

    if new_customer:
        return make_response(jsonify({"response": new_customer}), 200)
    else:
        return make_response(jsonify({"response": "Failed"}), 400)


@client.put('/modifier_client/')
def update_cust():

    data = request.get_json()

    clit = Client()

    modif_clit = clit.modifier_client(data=data)

    if modif_clit:
        return make_response(jsonify({"response": modif_clit}), 200)
    else:
        return make_response(jsonify({"response": "Updating failed"}), 400)


@client.delete('/supprimer_client/<id>')
def delete_cust(id):
    """Supprime un client et toutes ses missions associées"""
    try:
        clit = Client()
        result = clit.supprimer_client(id)
        
        if result["success"]:
            return make_response(jsonify({
                "response": "success",
                "message": result["message"],
                "client_name": result["client_name"]
            }), 200)
        else:
            return make_response(jsonify({
                "response": "error",
                "message": result["message"]
            }), 400)
            
    except Exception as e:
        return make_response(jsonify({
            "response": "error",
            "message": f"Erreur serveur: {str(e)}"
        }), 500)
