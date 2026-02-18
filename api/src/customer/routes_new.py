"""
Routes pour les clients - Version restructurée
Utilise la nouvelle architecture avec resources, services et schemas
"""

from src.customer import client
from src.resources.client_resources import (
    new_cust,
    show_cust,
    show_info,
    update_cust,
    delete_cust,
    ClientResource
)


# Routes utilisant les nouvelles resources
@client.get('/afficher_clients/')
def show_clients_route():
    """GET /cors/client/afficher_clients/ - Affiche tous les clients"""
    return show_cust()


@client.get('/info_client/<id>')
def show_client_info_route(id):
    """GET /cors/client/info_client/<id> - Affiche les infos d'un client"""
    return show_info(id)


@client.post('/nouveau_client/')
def create_client_route():
    """POST /cors/client/nouveau_client/ - Crée un nouveau client"""
    return new_cust()


@client.put('/modifier_client/')
def update_client_route():
    """PUT /cors/client/modifier_client/ - Modifie un client"""
    return update_cust()


@client.delete('/supprimer_client/<id>')
def delete_client_route(id):
    """DELETE /cors/client/supprimer_client/<id> - Supprime un client"""
    return delete_cust(id)


@client.get('/referentiels/')
def get_referentiels_route():
    """GET /cors/client/referentiels/ - Récupère les référentiels disponibles"""
    return ClientResource.get_referentiels()


# Routes alternatives utilisant directement les classes Resource (optionnel)
@client.get('/v2/clients/')
def list_clients_v2():
    """GET /cors/client/v2/clients/ - Version alternative avec classe Resource"""
    return ClientResource.get_all_clients()


@client.post('/v2/clients/')
def create_client_v2():
    """POST /cors/client/v2/clients/ - Version alternative avec classe Resource"""
    return ClientResource.create_client()


@client.get('/v2/clients/<client_id>')
def get_client_v2(client_id):
    """GET /cors/client/v2/clients/<id> - Version alternative avec classe Resource"""
    return ClientResource.get_client_info(client_id)


@client.put('/v2/clients/')
def update_client_v2():
    """PUT /cors/client/v2/clients/ - Version alternative avec classe Resource"""
    return ClientResource.update_client()


@client.delete('/v2/clients/<client_id>')
def delete_client_v2(client_id):
    """DELETE /cors/client/v2/clients/<id> - Version alternative avec classe Resource"""
    return ClientResource.delete_client(client_id)
