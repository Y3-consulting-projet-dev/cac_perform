"""
Schémas de validation pour la refonte de l'import (balances, mapping,
fichiers auxiliaires/immobilisations). Nouveau périmètre V2 — voir
docs/PLAN_import_refonte.md. N'étend ni ne remplace mission_schemas.py /
client_schemas.py existants.
"""
from typing import Any, Dict

from marshmallow import Schema, fields, validate, ValidationError

# Champs cibles reconnus pour le mapping d'une balance générale. Reprend
# l'inventaire des formats détectés aujourd'hui par Mission.creation_balance()
# (api/src/model.py) comme référence, sans importer ni modifier ce fichier
# (CLAUDE.md : parsing historique isolé).
CHAMPS_BALANCE_GENERALE = [
    "numero", "libelle",
    "debit_initial", "credit_initial",
    "debit_mvt", "credit_mvt",
    "debit_fin", "credit_fin",
]

TYPES_BALANCE_AUXILIAIRE = ["client", "fournisseur"]


class MappingColonnesSchema(Schema):
    """Correspondance {champ cible: colonne source détectée} pour une balance générale."""

    numero = fields.Str(required=True)
    libelle = fields.Str(required=True)
    debit_initial = fields.Str(required=False, allow_none=True)
    credit_initial = fields.Str(required=False, allow_none=True)
    debit_mvt = fields.Str(required=False, allow_none=True)
    credit_mvt = fields.Str(required=False, allow_none=True)
    debit_fin = fields.Str(required=False, allow_none=True)
    credit_fin = fields.Str(required=False, allow_none=True)
    montant = fields.Str(required=False, allow_none=True)  # format "simple" (3 colonnes)


class MappingApercuResponseSchema(Schema):
    """Réponse de l'aperçu de mapping : colonnes détectées + proposition par défaut."""

    colonnes_detectees = fields.List(fields.Str(), required=True)
    feuille = fields.Str(required=True)
    format_propose = fields.Str(required=True)
    mapping_propose = fields.Dict(required=True)
    nb_lignes_detectees = fields.Int(required=True)


class MappingImportCreateSchema(Schema):
    """Schéma pour mémoriser un mapping (identifié par client + logiciel comptable)."""

    id_client = fields.Str(required=True, validate=validate.Length(min=1))
    logiciel_comptable = fields.Str(required=True, validate=validate.Length(min=1))
    mapping = fields.Dict(required=True)


class MappingImportResponseSchema(Schema):
    """Schéma de sortie d'un mapping mémorisé (une version)."""

    _id = fields.Str(required=True)
    id_client = fields.Str(required=True)
    logiciel_comptable = fields.Str(required=True)
    mapping = fields.Dict(required=True)
    version = fields.Int(required=True)
    created_at = fields.Str(required=True)


class BalanceAuxiliaireUploadSchema(Schema):
    """Champs de formulaire attendus pour l'import d'une balance auxiliaire."""

    type_auxiliaire = fields.Str(required=True, validate=validate.OneOf(TYPES_BALANCE_AUXILIAIRE))
    id_client = fields.Str(required=True, validate=validate.Length(min=1))
    annee = fields.Str(required=True, validate=validate.Length(min=4, max=4))


class ImmobilisationUploadSchema(Schema):
    """Champs de formulaire attendus pour l'import du fichier des immobilisations."""

    id_client = fields.Str(required=True, validate=validate.Length(min=1))
    annee = fields.Str(required=True, validate=validate.Length(min=4, max=4))


def validate_import_data(data: Dict[str, Any], schema_class) -> Dict[str, Any]:
    """Valide des données selon le schéma marshmallow fourni."""
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as err:
        raise ValidationError(err.messages)
