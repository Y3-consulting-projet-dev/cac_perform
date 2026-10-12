"""
Schémas de validation pour le verrou IPE (Module 1, CAC-IPE-01).
Nouveau périmètre V2 — voir docs/PLAN_verrou_IPE.md. N'étend ni ne remplace
mission_schemas.py / import_schemas.py existants.
"""
from typing import Any, Dict

from marshmallow import Schema, fields, validate, ValidationError

MODULES_IPE = ["ipe_1_clients", "ipe_2_fournisseurs", "ipe_3_immobilisations"]


class ValidationFiabiliteSchema(Schema):
    """Corps attendu pour POST /api/v1/missions/<id>/ipe/validation (validation manager)."""

    validee = fields.Bool(required=True)
    commentaire = fields.Str(required=False, allow_none=True)
    # Pas de contrôle de rôle possible aujourd'hui (voir CLAUDE.md, point de
    # sécurité connu) : utilisateur_id reste optionnel et nullable.
    utilisateur_id = fields.Str(required=False, allow_none=True)


def validate_ipe_data(data: Dict[str, Any], schema_class) -> Dict[str, Any]:
    """Valide des données selon le schéma marshmallow fourni."""
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as err:
        raise ValidationError(err.messages)
