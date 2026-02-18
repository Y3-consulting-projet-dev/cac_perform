"""
Schémas de validation pour les clients
"""

from marshmallow import Schema, fields, validate, ValidationError, post_load
from typing import Dict, Any


class ClientCreateSchema(Schema):
    """Schéma pour la création d'un client"""
    
    nom = fields.Str(
        required=True, 
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "Le nom du client est requis"}
    )
    
    activite = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=200),
        error_messages={"required": "L'activité du client est requise"}
    )
    
    referentiel = fields.Str(
        required=True,
        validate=validate.OneOf(["syscohada", "ifrs", "pcg"]),
        error_messages={"required": "Le référentiel comptable est requis"}
    )
    
    forme_juridique = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=50),
        error_messages={"required": "La forme juridique est requise"}
    )
    
    capital = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        error_messages={"required": "Le capital est requis"}
    )
    
    siege_social = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=200),
        error_messages={"required": "Le siège social est requis"}
    )
    
    adresse = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=300),
        error_messages={"required": "L'adresse est requise"}
    )
    
    n_cc = fields.Str(
        required=False,
        validate=validate.Length(max=50),
        allow_none=True
    )


class ClientUpdateSchema(ClientCreateSchema):
    """Schéma pour la modification d'un client"""
    
    _id = fields.Str(
        required=True,
        error_messages={"required": "L'ID du client est requis pour la modification"}
    )
    
    # Rendre tous les champs optionnels pour la modification
    nom = fields.Str(validate=validate.Length(min=2, max=100), required=False)
    activite = fields.Str(validate=validate.Length(min=2, max=200), required=False)
    referentiel = fields.Str(validate=validate.OneOf(["syscohada", "ifrs", "pcg"]), required=False)
    forme_juridique = fields.Str(validate=validate.Length(min=2, max=50), required=False)
    capital = fields.Float(validate=validate.Range(min=0), required=False)
    siege_social = fields.Str(validate=validate.Length(min=5, max=200), required=False)
    adresse = fields.Str(validate=validate.Length(min=5, max=300), required=False)


class ClientResponseSchema(Schema):
    """Schéma pour la réponse client"""
    
    _id = fields.Str(required=True)
    nom = fields.Str(required=True)
    activite = fields.Str(required=True)
    referentiel = fields.Str(required=True)
    forme_juridique = fields.Str(required=True)
    capital = fields.Float(required=True)
    siege_social = fields.Str(required=True)
    adresse = fields.Str(required=True)
    n_cc = fields.Str(allow_none=True)


class ClientListResponseSchema(Schema):
    """Schéma pour la liste des clients"""
    
    clients = fields.List(fields.Nested(ClientResponseSchema))
    total = fields.Int()


class ClientWithMissionsSchema(ClientResponseSchema):
    """Schéma pour un client avec ses missions"""
    
    missions = fields.List(fields.Dict(), allow_none=True)


def validate_client_data(data: Dict[str, Any], schema_class: Schema) -> Dict[str, Any]:
    """
    Valide les données d'un client selon le schéma fourni
    
    Args:
        data: Données à valider
        schema_class: Classe de schéma à utiliser
        
    Returns:
        Données validées et nettoyées
        
    Raises:
        ValidationError: Si les données ne sont pas valides
    """
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as err:
        raise ValidationError(f"Erreurs de validation: {err.messages}")


def serialize_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sérialise les données d'un client pour la réponse
    
    Args:
        client_data: Données du client
        
    Returns:
        Données sérialisées
    """
    schema = ClientResponseSchema()
    return schema.dump(client_data)


def serialize_client_list(clients_data: list) -> Dict[str, Any]:
    """
    Sérialise une liste de clients pour la réponse
    
    Args:
        clients_data: Liste des clients
        
    Returns:
        Données sérialisées avec métadonnées
    """
    schema = ClientListResponseSchema()
    return schema.dump({
        "clients": clients_data,
        "total": len(clients_data)
    })
