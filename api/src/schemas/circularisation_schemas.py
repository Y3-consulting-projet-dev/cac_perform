"""
Schémas de la circularisation, sous-lot a (docs/PLAN_circularisation.md).
Types seulement : les règles (motif d'au moins 15 caractères, utilisateur
identifié) sont vérifiées par circularisation_service, avec ses messages.
"""
from marshmallow import Schema, fields, validate, EXCLUDE

from src.services.circularisation_service import MODES


class _Base(Schema):
    class Meta:
        unknown = EXCLUDE

    utilisateur_id = fields.Str(load_default=None, allow_none=True)


class PopulationSchema(_Base):
    pass


class DecisionTiersSchema(_Base):
    numero = fields.Str(required=True, validate=validate.Length(min=1))
    retenu = fields.Bool(required=True)
    motif = fields.Str(load_default=None, allow_none=True)


class ModeSchema(_Base):
    mode = fields.Str(required=True, validate=validate.OneOf(MODES))
    motif = fields.Str(load_default=None, allow_none=True)


class DecisionMemoSchema(_Base):
    commentaire = fields.Str(load_default=None, allow_none=True)
