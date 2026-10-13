"""
Contrôles avant import (type de comptes, exercice) et action « Retirer » des
fichiers complémentaires. Données FICTIVES construites en mémoire.
"""
import io
from datetime import datetime

import openpyxl
import pytest
from marshmallow import ValidationError
from werkzeug.datastructures import FileStorage

from src.schemas.import_schemas import RetraitFichierSchema
from src.services import fichiers_complementaires_service as fc_service
from src.services import verification_fichier_service as verif
from src.services import verrou_ipe_service
from tests.conftest import ENTETES_Y3


# --- Cohérence du type -------------------------------------------------------

def test_famille_du_compte():
    assert verif.famille_du_compte("4011000") == "auxiliaire_fournisseur"
    assert verif.famille_du_compte("411200") == "auxiliaire_client"
    assert verif.famille_du_compte("245100") == "immobilisations"
    assert verif.famille_du_compte("601000") == "autres"
    assert verif.famille_du_compte("FRS001") is None
    assert verif.famille_du_compte(None) is None


def test_fichier_fournisseurs_sur_la_carte_immobilisations_alerte():
    resultat = verif.controler_type("immobilisations", ["401100", "401200", "408000"])
    assert resultat["alerte"]["code"] == "type_incoherent"
    message = resultat["alerte"]["message"]
    assert "comptes fournisseurs" in message
    assert "il ne semble pas être un fichier des immobilisations" in message


def test_fichier_clients_sur_la_carte_fournisseurs_alerte():
    resultat = verif.controler_type("auxiliaire_fournisseur", ["411001", "411002", "401000"])
    assert "comptes clients" in resultat["alerte"]["message"]
    assert "balance auxiliaire fournisseurs" in resultat["alerte"]["message"]


def test_type_coherent_sans_alerte():
    assert verif.controler_type("auxiliaire_client", ["411001", "411002", "416000"])["alerte"] is None
    assert verif.controler_type("immobilisations", ["245100", "284500", "231000"])["alerte"] is None


def test_codes_tiers_alphanumeriques_non_verifiables():
    resultat = verif.controler_type("auxiliaire_client", ["CLI001", "CLI002"])
    assert resultat["alerte"] is None
    assert "non vérifiable" in resultat["information"]


# --- Cohérence de l'exercice ---------------------------------------------------

def test_annees_lues_dans_le_nom_et_le_titre():
    lignes_titre = [["BALANCE AUXILIAIRE"], ["Periode Du : 01/01/2024 Au : 31/12/2024"], [datetime(2024, 12, 31)]]
    assert verif.annees_detectees("aux_clients_2024.xlsx", lignes_titre) == [2024]
    assert verif.annees_detectees("export_20251231.xlsx", []) == []  # pas d'année isolée


def test_exercice_different_alerte():
    resultat = verif.controler_exercice("2025", [2024])
    assert resultat["alerte"]["code"] == "exercice_incoherent"
    assert "2024" in resultat["alerte"]["message"] and "2025" in resultat["alerte"]["message"]


def test_exercice_present_parmi_les_annees_sans_alerte():
    # Exercice à cheval (hypothèse de travail, TODO(spec)) : pas d'alerte.
    assert verif.controler_exercice("2025", [2024, 2025])["alerte"] is None


def test_aucune_annee_trouvee_information_seulement():
    resultat = verif.controler_exercice("2025", [])
    assert resultat["alerte"] is None
    assert "exercice non vérifié" in resultat["information"]


def _fichier_y3(nom, comptes, titre_periode):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["BALANCE AUXILIAIRE"])
    ws.append([titre_periode])
    ws.append(ENTETES_Y3)
    for i, compte in enumerate(comptes):
        ws.append(["E1", compte, f"TIERS FICTIF {i}", 0, 0, 100, 0, 100, 0, 100, 0])
    tampon = io.BytesIO()
    wb.save(tampon)
    tampon.seek(0)
    return FileStorage(stream=tampon, filename=nom)


def test_verifier_fichier_cumule_les_deux_alertes():
    fichier = _fichier_y3("fournisseurs.xlsx", ["401001", "401002"], "Periode Du : 01/01/2024 Au : 31/12/2024")
    resultat = verif.verifier_fichier(fichier, "auxiliaire_client", "2025")
    assert {a["code"] for a in resultat["alertes"]} == {"type_incoherent", "exercice_incoherent"}
    assert resultat["repartition_comptes"] == {"auxiliaire_fournisseur": 2}
    assert resultat["annees_detectees"] == [2024]


def test_verifier_fichier_coherent_sans_alerte():
    fichier = _fichier_y3("clients_2025.xlsx", ["411001", "411002"], "Periode Du : 01/01/2025 Au : 31/12/2025")
    assert verif.verifier_fichier(fichier, "auxiliaire_client", "2025")["alertes"] == []


def test_verifier_fichier_type_inconnu():
    with pytest.raises(ValueError):
        verif.verifier_fichier(_fichier_y3("x.xlsx", ["411001"], ""), "balance_generale", "2025")


# --- Action « Retirer » --------------------------------------------------------

def test_retrait_refuse_hors_mission_ou_deja_archive():
    doc = {"mission_id": "m1", "type": "auxiliaire_client", "actif": True}
    assert fc_service.refus_retrait(doc, "m1") is None
    assert fc_service.refus_retrait(doc, "autre_mission") == "Fichier introuvable pour cette mission."
    assert fc_service.refus_retrait(None, "m1") == "Fichier introuvable pour cette mission."
    assert "déjà archivé" in fc_service.refus_retrait({**doc, "actif": False}, "m1")
    assert fc_service.refus_retrait({**doc, "type": "balance_generale"}, "m1") is not None


def test_retrait_invalide_une_validation_ipe_qui_utilisait_le_fichier():
    etat = {"fichiers_references": {"auxiliaire_client": {"_id": "aux_v1"}}}
    decision = verrou_ipe_service.decider_invalidation(etat, "auxiliaire_client", None)
    assert decision["updates"]["ipe.ipe_fiabilite_validee"] is False
    assert "retiré" in decision["commentaire"]


def test_retrait_sans_validation_ipe_rien_a_invalider():
    assert verrou_ipe_service.decider_invalidation({"fichiers_references": {}}, "auxiliaire_client", None) is None


def test_schema_retrait_exige_utilisateur_et_commentaire():
    schema = RetraitFichierSchema()
    assert schema.load({"utilisateur_id": "A. Auditeur", "commentaire": "Importé sur la mauvaise carte"})
    with pytest.raises(ValidationError, match="Utilisateur non identifié"):
        schema.load({"utilisateur_id": "", "commentaire": "Importé sur la mauvaise carte"})
    with pytest.raises(ValidationError, match="Utilisateur non identifié"):
        schema.load({"commentaire": "Importé sur la mauvaise carte"})
    with pytest.raises(ValidationError, match="au moins 15 caractères"):
        schema.load({"utilisateur_id": "A. Auditeur", "commentaire": "   erreur      "})
