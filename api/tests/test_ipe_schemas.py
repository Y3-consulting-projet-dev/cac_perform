"""
Tests de schemas/ipe_schemas.py : le commentaire de validation/invalidation
IPE est désormais obligatoire, avec une longueur minimale — pour la
validation ET l'invalidation (même schéma, même champ `commentaire`).
Voir docs/PLAN_verrou_IPE.md.
"""
from marshmallow import ValidationError
import pytest

from src.schemas.ipe_schemas import (
    ValidationFiabiliteSchema,
    LONGUEUR_MIN_COMMENTAIRE_VALIDATION,
    validate_ipe_data,
)


def test_commentaire_absent_est_refuse():
    with pytest.raises(ValidationError) as exc_info:
        validate_ipe_data({"validee": True}, ValidationFiabiliteSchema)
    # Message clair en français, pas le "Missing data for required field." générique de marshmallow.
    assert "obligatoire" in str(exc_info.value)


def test_commentaire_trop_court_est_refuse():
    with pytest.raises(ValidationError) as exc_info:
        validate_ipe_data({"validee": True, "commentaire": "trop court"}, ValidationFiabiliteSchema)
    # Message clair, pas une erreur générique.
    assert "15" in str(exc_info.value) or "caractères" in str(exc_info.value)


def test_commentaire_valide_est_accepte_pour_une_validation():
    data = validate_ipe_data(
        {"validee": True, "commentaire": "Écarts qualifiés, validation justifiée."},
        ValidationFiabiliteSchema,
    )
    assert data["commentaire"] == "Écarts qualifiés, validation justifiée."


def test_commentaire_obligatoire_aussi_pour_une_invalidation():
    """Le commentaire est obligatoire pour toute validation ET invalidation, pas seulement validee=True."""
    with pytest.raises(ValidationError):
        validate_ipe_data({"validee": False}, ValidationFiabiliteSchema)

    data = validate_ipe_data(
        {"validee": False, "commentaire": "Fichier remplacé, fiabilité à revérifier."},
        ValidationFiabiliteSchema,
    )
    assert data["validee"] is False


def test_longueur_minimale_exacte():
    commentaire_limite = "x" * LONGUEUR_MIN_COMMENTAIRE_VALIDATION
    data = validate_ipe_data({"validee": True, "commentaire": commentaire_limite}, ValidationFiabiliteSchema)
    assert data["commentaire"] == commentaire_limite

    commentaire_trop_court = "x" * (LONGUEUR_MIN_COMMENTAIRE_VALIDATION - 1)
    with pytest.raises(ValidationError):
        validate_ipe_data({"validee": True, "commentaire": commentaire_trop_court}, ValidationFiabiliteSchema)
