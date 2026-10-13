"""
Schémas de validation pour le verrou IPE (Module 1, CAC-IPE-01).
Nouveau périmètre V2 — voir docs/PLAN_verrou_IPE.md. N'étend ni ne remplace
mission_schemas.py / import_schemas.py existants.
"""
from typing import Any, Dict

from marshmallow import Schema, fields, validate, ValidationError

MODULES_IPE = ["ipe_1_clients", "ipe_2_fournisseurs", "ipe_3_immobilisations"]

# Longueur minimale imposée au commentaire de validation/invalidation —
# docs/PLAN_verrou_IPE.md : un commentaire est désormais obligatoire pour
# toute validation ET toute invalidation, pas seulement pour la validation.
LONGUEUR_MIN_COMMENTAIRE_VALIDATION = 15


class ValidationFiabiliteSchema(Schema):
    """Corps attendu pour POST /api/v1/missions/<id>/ipe/validation (validation manager)."""

    validee = fields.Bool(required=True)
    commentaire = fields.Str(
        required=True,
        error_messages={
            "required": f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
            "null": f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
        },
        validate=validate.Length(
            min=LONGUEUR_MIN_COMMENTAIRE_VALIDATION,
            error=f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
        ),
    )
    # Pas de contrôle de rôle possible aujourd'hui (voir CLAUDE.md, point de
    # sécurité connu) : utilisateur_id reste optionnel et nullable — rempli
    # côté frontend avec l'utilisateur connecté quand disponible.
    utilisateur_id = fields.Str(required=False, allow_none=True)


class SoumissionRevueSchema(Schema):
    """
    Corps attendu pour POST /api/v1/missions/<id>/ipe/soumettre (action
    auditeur — TODO(décision) : qui a le droit de soumettre n'est pas
    vérifié aujourd'hui, voir CLAUDE.md). Commentaire optionnel : rien dans
    docs/PLAN_verrou_IPE.md n'impose un commentaire à la soumission.
    """

    commentaire = fields.Str(required=False, allow_none=True)
    utilisateur_id = fields.Str(required=False, allow_none=True)


class DemandeCorrectionSchema(Schema):
    """
    Corps attendu pour POST /api/v1/missions/<id>/ipe/demander-correction
    (action manager — TODO(décision) : qui a le droit de demander une
    correction n'est pas vérifié aujourd'hui). Commentaire obligatoire,
    même longueur minimale que pour une validation/invalidation.
    """

    commentaire = fields.Str(
        required=True,
        error_messages={
            "required": f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
            "null": f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
        },
        validate=validate.Length(
            min=LONGUEUR_MIN_COMMENTAIRE_VALIDATION,
            error=f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères.",
        ),
    )
    utilisateur_id = fields.Str(required=False, allow_none=True)


class RemarqueCreationSchema(Schema):
    """
    Corps attendu pour POST /api/v1/missions/<id>/ipe/remarques — remarque à
    deux niveaux (docs/PLAN_verrou_IPE.md) : générale si `module`/
    `numero_compte` absents, sur un écart précis sinon.
    """

    commentaire = fields.Str(required=True, validate=validate.Length(min=1, error="Le commentaire ne peut pas être vide."))
    module = fields.Str(required=False, allow_none=True, validate=validate.OneOf(MODULES_IPE))
    numero_compte = fields.Str(required=False, allow_none=True)
    # "information" (par défaut) ou "demande_correction" : une demande de
    # correction non traitée bloque la validation.
    type = fields.Str(
        required=False,
        load_default="information",
        validate=validate.OneOf(["information", "demande_correction"], error="Type de remarque inconnu."),
    )
    utilisateur_id = fields.Str(required=False, allow_none=True)


class ReponseRemarqueSchema(Schema):
    """Corps attendu pour PUT .../ipe/remarques/<id>/reponse — réponse de l'auditeur à une remarque."""

    commentaire = fields.Str(required=True, validate=validate.Length(min=1, error="La réponse ne peut pas être vide."))
    utilisateur_id = fields.Str(required=False, allow_none=True)


class TraiterRemarqueSchema(Schema):
    """
    Corps attendu pour PUT .../ipe/remarques/<id>/traitee — marque (ou
    démarque) une remarque comme traitée. utilisateur_id sert à vérifier que
    le demandeur est l'auteur de la remarque (TODO(décision) : en attendant
    les rôles).
    """

    traitee = fields.Bool(required=True)
    utilisateur_id = fields.Str(required=False, allow_none=True)


_MESSAGE_COMMENTAIRE_MIN = (
    f"Le commentaire est obligatoire et doit contenir au moins {LONGUEUR_MIN_COMMENTAIRE_VALIDATION} caractères."
)


def _commentaire_obligatoire():
    return fields.Str(
        required=True,
        error_messages={"required": _MESSAGE_COMMENTAIRE_MIN, "null": _MESSAGE_COMMENTAIRE_MIN},
        validate=validate.Length(min=LONGUEUR_MIN_COMMENTAIRE_VALIDATION, error=_MESSAGE_COMMENTAIRE_MIN),
    )


class QualificationEcartSchema(Schema):
    """
    Corps attendu pour PUT /api/v1/missions/<id>/ipe/qualifications — cause
    (vérifiée contre revue_ipe_service.CAUSES_ECART, liste provisoire
    TODO(spec: CAC-IPE-01)) + commentaire obligatoire, par compte collectif.
    """

    module = fields.Str(required=True, validate=validate.OneOf(MODULES_IPE))
    numero_compte = fields.Str(required=True, validate=validate.Length(min=1))
    cause = fields.Str(required=True, error_messages={"required": "La cause de l'écart est obligatoire."})
    commentaire = _commentaire_obligatoire()
    utilisateur_id = fields.Str(required=False, allow_none=True)


class JustificationNonEvaluableSchema(Schema):
    """Corps attendu pour PUT /api/v1/missions/<id>/ipe/justifications-non-evaluables."""

    module = fields.Str(required=True, validate=validate.OneOf(MODULES_IPE))
    commentaire = _commentaire_obligatoire()
    utilisateur_id = fields.Str(required=False, allow_none=True)


def validate_ipe_data(data: Dict[str, Any], schema_class) -> Dict[str, Any]:
    """Valide des données selon le schéma marshmallow fourni."""
    schema = schema_class()
    try:
        return schema.load(data)
    except ValidationError as err:
        raise ValidationError(err.messages)
