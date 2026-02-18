"""
Schémas de validation pour les missions
"""

from marshmallow import Schema, fields, validate, ValidationError, post_load
from typing import Dict, Any


class MissionCreateSchema(Schema):
    """Schéma pour la création d'une mission"""
    
    annee_auditee = fields.Str(
        required=True,
        validate=validate.Length(min=4, max=4, error="L'année doit faire exactement 4 caractères (ex: 2024)"),
        error_messages={
            "required": "L'année auditée est requise",
            "invalid": "L'année doit faire exactement 4 caractères (ex: 2024)"
        }
    )
    
    id_client = fields.Str(
        required=True,
        validate=validate.Length(min=1, error="L'ID du client ne peut pas être vide"),
        error_messages={
            "required": "L'ID du client est requis",
            "invalid": "L'ID du client ne peut pas être vide"
        }
    )
    
    date_debut = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^\d{4}-\d{2}-\d{2}$',
            error="La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"
        ),
        error_messages={
            "required": "La date de début est requise",
            "invalid": "La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"
        }
    )
    
    date_fin = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^\d{4}-\d{2}-\d{2}$',
            error="La date doit être au format YYYY-MM-DD (ex: 2024-12-31)"
        ),
        error_messages={
            "required": "La date de fin est requise",
            "invalid": "La date doit être au format YYYY-MM-DD (ex: 2024-12-31)"
        }
    )
    
    date_debut_mandat = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^\d{4}-\d{2}-\d{2}$',
            error="La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"
        ),
        error_messages={
            "required": "La date de début du mandat est requise",
            "invalid": "La date doit être au format YYYY-MM-DD (ex: 2024-01-01)"
        }
    )
    
    date_fin_mandat = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^\d{4}-\d{2}-\d{2}$',
            error="La date doit être au format YYYY-MM-DD (ex: 2024-12-31)"
        ),
        error_messages={
            "required": "La date de fin du mandat est requise",
            "invalid": "La date doit être au format YYYY-MM-DD (ex: 2024-12-31)"
        }
    )
    
    @post_load
    def validate_dates(self, data, **kwargs):
        """Valide que la date de début est antérieure à la date de fin"""
        from datetime import datetime
        try:
            date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d')
            date_fin = datetime.strptime(data['date_fin'], '%Y-%m-%d')
            
            if date_debut >= date_fin:
                raise ValidationError("La date de début doit être antérieure à la date de fin")
            
            # Valider les dates du mandat
            date_debut_mandat = datetime.strptime(data['date_debut_mandat'], '%Y-%m-%d')
            date_fin_mandat = datetime.strptime(data['date_fin_mandat'], '%Y-%m-%d')
            
            if date_debut_mandat >= date_fin_mandat:
                raise ValidationError("La date de début du mandat doit être antérieure à la date de fin du mandat")
        except ValueError:
            raise ValidationError("Format de date invalide")
        
        return data


class MissionResponseSchema(Schema):
    """Schéma pour la réponse d'une mission"""
    
    _id = fields.Str(required=True)
    id_client = fields.Str(required=True)
    annee_auditee = fields.Str(required=True)
    date_debut = fields.Str(required=True)
    date_fin = fields.Str(required=True)
    date_debut_mandat = fields.Str(required=False, allow_none=True)
    date_fin_mandat = fields.Str(required=False, allow_none=True)
    balances = fields.List(fields.Str())
    balance_variation = fields.Dict()
    grouping = fields.Dict()
    efi = fields.Dict()
    materiality = fields.List(fields.Dict())


def validate_mission_data(data: Dict[str, Any], schema_class: Schema = MissionCreateSchema) -> Dict[str, Any]:
    """
    Valide les données d'une mission selon le schéma fourni
    
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


def serialize_mission(mission_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sérialise les données d'une mission pour la réponse
    
    Args:
        mission_data: Données de la mission
        
    Returns:
        Données sérialisées
    """
    schema = MissionResponseSchema()
    return schema.dump(mission_data)




