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
    QualificationEcartSchema,
    JustificationNonEvaluableSchema,
    RemarqueCreationSchema,
    TraiterRemarqueSchema,
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


# ---------------------------------------------------------------------------
# Circuit de revue : qualification, justification, remarques
# ---------------------------------------------------------------------------

def test_qualification_exige_cause_et_commentaire():
    with pytest.raises(ValidationError):
        validate_ipe_data({"module": "ipe_2_fournisseurs", "numero_compte": "4011", "cause": "Cut-off"}, QualificationEcartSchema)
    with pytest.raises(ValidationError):
        validate_ipe_data(
            {"module": "ipe_2_fournisseurs", "numero_compte": "4011", "commentaire": "Facture reçue en janvier N+1."},
            QualificationEcartSchema,
        )
    data = validate_ipe_data(
        {"module": "ipe_2_fournisseurs", "numero_compte": "4011", "cause": "Cut-off", "commentaire": "Facture reçue en janvier N+1."},
        QualificationEcartSchema,
    )
    assert data["cause"] == "Cut-off"


def test_justification_non_evaluable_exige_un_commentaire_suffisant():
    with pytest.raises(ValidationError):
        validate_ipe_data({"module": "ipe_1_clients", "commentaire": "court"}, JustificationNonEvaluableSchema)
    data = validate_ipe_data(
        {"module": "ipe_1_clients", "commentaire": "Aucune créance client à la clôture."},
        JustificationNonEvaluableSchema,
    )
    assert data["module"] == "ipe_1_clients"


def test_remarque_informative_par_defaut_et_type_controle():
    assert validate_ipe_data({"commentaire": "Note."}, RemarqueCreationSchema)["type"] == "information"
    assert validate_ipe_data({"commentaire": "À corriger.", "type": "demande_correction"}, RemarqueCreationSchema)["type"] == "demande_correction"
    with pytest.raises(ValidationError):
        validate_ipe_data({"commentaire": "x", "type": "autre"}, RemarqueCreationSchema)


def test_marquage_traitee_accepte_l_utilisateur():
    """Le frontend envoie utilisateur_id : il doit être accepté (contrôle de l'auteur)."""
    data = validate_ipe_data({"traitee": True, "utilisateur_id": "Awa Koné"}, TraiterRemarqueSchema)
    assert data["utilisateur_id"] == "Awa Koné"
