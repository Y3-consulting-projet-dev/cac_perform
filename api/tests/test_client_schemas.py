"""
Champs facultatifs N°CC (numero_cc) et capital social (capital_social) du
client. Données FICTIVES : aucun appel à la base.
"""
import pytest
from marshmallow import ValidationError

from src.schemas.client_schemas import (
    ClientCreateSchema, ClientUpdateSchema, serialize_client, validate_client_data,
)

CLIENT_EXISTANT = {
    "company_name": "SOCIETE FICTIVE TEST", "sector": "Commerce de gros", "address": "Abidjan",
    "referentiel": "SYSCOHADA", "legal_form": "SA", "responsable_name": "Responsable Test",
    "civility": "M", "responsable_function": "DG", "RCCM": "CI-ABJ-03-2015-B14-01234",
    "country": "Côte d'Ivoire", "creation_date": "2015-03-15",
}


def test_client_existant_sans_les_nouveaux_champs_reste_valide():
    charge = validate_client_data(CLIENT_EXISTANT, ClientCreateSchema)
    assert "numero_cc" not in charge and "capital_social" not in charge
    assert charge["RCCM"] == "CI-ABJ-03-2015-B14-01234"


def test_nouveaux_champs_enregistres():
    charge = validate_client_data({**CLIENT_EXISTANT, "numero_cc": " 1512345 A ", "capital_social": 100_000_000},
                                  ClientCreateSchema)
    assert charge["numero_cc"] == "1512345 A"
    assert charge["capital_social"] == 100_000_000


def test_capital_saisi_avec_espaces_de_milliers():
    charge = validate_client_data({**CLIENT_EXISTANT, "capital_social": "100 000 000"}, ClientCreateSchema)
    assert charge["capital_social"] == 100_000_000


def test_champs_vides_ignores_et_jamais_ecrases_a_la_modification():
    charge = validate_client_data({"_id": "x", "numero_cc": "", "capital_social": ""}, ClientUpdateSchema)
    assert "numero_cc" not in charge and "capital_social" not in charge


def test_format_du_ncc_non_bloquant():
    # Le format (7 chiffres + lettre) n'est qu'un avertissement à l'écran.
    charge = validate_client_data({**CLIENT_EXISTANT, "numero_cc": "ABC"}, ClientCreateSchema)
    assert charge["numero_cc"] == "ABC"


@pytest.mark.parametrize("capital", ["cent millions", -1])
def test_capital_invalide_refuse(capital):
    with pytest.raises(ValidationError):
        validate_client_data({**CLIENT_EXISTANT, "capital_social": capital}, ClientCreateSchema)


def test_reponse_expose_les_nouveaux_champs():
    sortie = serialize_client({**CLIENT_EXISTANT, "_id": "abc", "numero_cc": "1512345 A", "capital_social": 1e8})
    assert sortie["numero_cc"] == "1512345 A" and sortie["capital_social"] == 1e8
