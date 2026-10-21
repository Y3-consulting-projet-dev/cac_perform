"""
Circularisation, sous-lot c : envois enregistrés, échéances figées depuis
CADENCE_RELANCES, statuts selon la date du jour, relances, réponses et écarts,
analyse d'écart, procédure alternative. Données FICTIVES, base en mémoire.
"""
import io
from datetime import date

import pytest
from bson import ObjectId

from src.services import circularisation_service as cir
from src.services import courriers_service as courriers
from src.services import suivi_reponses_service as suivi
from tests.test_circularisation_service import BaseFactice
from tests.test_courriers_service import GridFSFactice

MOTIF = "Solde significatif au regard de la population"
J0 = date(2026, 1, 5)


@pytest.fixture
def base(monkeypatch):
    db = BaseFactice()
    mission_id, client_id, fichier_id = ObjectId(), ObjectId(), ObjectId()
    db["Client_db"].insert_one({"_id": client_id, "company_name": "CLIENT FICTIF"})
    db["Mission1"].insert_one({"_id": mission_id, "id_client": str(client_id), "annee_auditee": "2025"})
    db["Balance"].insert_one({"_id": fichier_id, "mission_id": str(mission_id), "type": "auxiliaire_fournisseur",
                              "nom_fichier": "aux_frs.xlsx", "version": 1,
                              "balance": [{"numero_compte": "4011A", "libelle_compte": "FOURNISSEUR A",
                                           "solde_final_debit": 0, "solde_final_credit": 600_000},
                                          {"numero_compte": "4011B", "libelle_compte": "FOURNISSEUR B",
                                           "solde_final_debit": 0, "solde_final_credit": 10_000}]})
    stockage = GridFSFactice()
    for module in (cir, courriers, suivi):
        monkeypatch.setattr(module, "_db", lambda: db)
    monkeypatch.setattr(courriers, "_gridfs", lambda: stockage)
    monkeypatch.setattr(cir, "_fichier_actif", lambda m, t: {"_id": str(fichier_id), "nom_fichier": "aux_frs.xlsx",
                                                              "version": 1} if t == "auxiliaire_fournisseur" else None)
    monkeypatch.setattr(cir, "_etat_ipe", lambda m: {"statut_affiche": "valide"})
    m = str(mission_id)
    cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    cir.decider_tiers(m, "fournisseurs", "4011A", True, MOTIF, "Auditeur Test")
    return {"db": db, "mission_id": m, "stockage": stockage}


def _envoyer(base, jour=J0):
    etat = suivi.enregistrer_envoi(base["mission_id"], "fournisseurs", "4011A", "courriel", jour.isoformat(),
                                   "compta@a.ci", "Auditeur Test", aujourd_hui=jour)
    return etat["demandes"][0]["_id"]


def test_echeances_figees_depuis_la_cadence():
    assert [(e["cle"], e["date"]) for e in suivi.echeances(J0)] == [
        ("envoi", "2026-01-05"), ("relance_1", "2026-01-20"), ("relance_2", "2026-02-04"), ("alternative", "2026-02-19")]


def test_tiers_a_envoyer_puis_envoi(base):
    m = base["mission_id"]
    etat = suivi.lire_suivi(m, J0)
    assert [t["numero"] for t in etat["a_envoyer"]] == ["4011A"]  # 4011B non retenu
    with pytest.raises(ValueError, match="dans le futur"):
        suivi.enregistrer_envoi(m, "fournisseurs", "4011A", "postal", "2026-01-06", "BP 1", "Auditeur Test", aujourd_hui=J0)
    with pytest.raises(ValueError, match="courriel du destinataire invalide"):
        suivi.enregistrer_envoi(m, "fournisseurs", "4011A", "courriel", "2026-01-05", "BP 1", "Auditeur Test", aujourd_hui=J0)
    with pytest.raises(ValueError, match="n'est pas retenu"):
        suivi.enregistrer_envoi(m, "fournisseurs", "4011B", "postal", "2026-01-05", "BP 1", "Auditeur Test", aujourd_hui=J0)
    _envoyer(base)
    etat = suivi.lire_suivi(m, J0)
    assert etat["a_envoyer"] == []
    d = etat["demandes"][0]
    assert (d["statut"]["cle"], d["statut"]["prochaine_etape"]) == ("envoye", "Relance 1 le 20/01/2026")
    assert d["solde_comptable"] == -600_000
    with pytest.raises(ValueError, match="déjà été envoyée"):
        _envoyer(base)


def test_statuts_selon_la_date_et_les_relances(base):
    m = base["mission_id"]
    e = _envoyer(base)
    lire = lambda jour: suivi.lire_suivi(m, jour)["demandes"][0]["statut"]
    assert lire(date(2026, 1, 20))["cle"] == "a_relancer"
    suivi.enregistrer_relance(m, e, "2026-01-21", "courriel", "Auditeur Test", aujourd_hui=date(2026, 1, 21))
    assert lire(date(2026, 1, 25))["libelle"] == "Relance 1"
    assert lire(date(2026, 2, 4))["prochaine_etape"].startswith("Relance 2 due")
    suivi.enregistrer_relance(m, e, "2026-02-04", "postal", "Auditeur Test", aujourd_hui=date(2026, 2, 4))
    statut = lire(date(2026, 2, 10))
    assert statut["libelle"] == "Relance 2" and "alerte du Manager" in statut["prochaine_etape"]
    with pytest.raises(ValueError, match="relances prévues"):
        suivi.enregistrer_relance(m, e, "2026-02-10", "postal", "Auditeur Test", aujourd_hui=date(2026, 2, 10))
    assert lire(date(2026, 2, 19))["cle"] == "sans_reponse"
    ind = suivi.lire_suivi(m, date(2026, 2, 19))["indicateurs"]
    assert (ind["envoyes"], ind["sans_reponse"], ind["en_relance"]) == (1, 1, 0)


def test_procedure_alternative_seulement_sans_reponse(base):
    m = base["mission_id"]
    e = _envoyer(base)
    with pytest.raises(ValueError, match="sans réponse"):
        suivi.documenter_procedure_alternative(m, e, "Règlements postérieurs vérifiés", None, None, "Auditeur Test",
                                               aujourd_hui=date(2026, 1, 10))
    etat = suivi.documenter_procedure_alternative(m, e, "Règlements postérieurs vérifiés sur relevés bancaires",
                                                  b"%PDF", "releve.pdf", "Auditeur Test", aujourd_hui=date(2026, 3, 1))
    d = etat["demandes"][0]
    assert d["statut"]["prochaine_etape"] == "Procédure alternative documentée"
    assert d["procedures_alternatives"][0]["piece"]["nom_fichier"] == "releve.pdf"


def test_reponse_ecart_et_analyse(base):
    m = base["mission_id"]
    e = _envoyer(base)
    jour = date(2026, 1, 12)
    with pytest.raises(ValueError, match="solde confirmé"):
        suivi.enregistrer_reponse(m, e, {"type": "accord_partiel", "canal": "courriel", "recue_le": "2026-01-12",
                                         "commentaire": "Réponse signée reçue par courriel"}, None, None, "Auditeur Test", jour)
    with pytest.raises(ValueError, match="incohérente"):
        suivi.enregistrer_reponse(m, e, {"type": "accord_total", "canal": "courriel", "recue_le": "2026-01-01",
                                         "commentaire": "Réponse signée reçue par courriel"}, None, None, "Auditeur Test", jour)
    etat = suivi.enregistrer_reponse(m, e, {"type": "accord_partiel", "canal": "courriel", "recue_le": "2026-01-12",
                                            "solde_confirme": "550 000", "commentaire": "Réponse signée reçue par courriel"},
                                     b"%PDF", "reponse.pdf", "Auditeur Test", jour)
    d = etat["demandes"][0]
    assert d["reponses"][0]["ecart"] == 50_000
    assert (d["statut"]["cle"], d["statut"]["prochaine_etape"]) == ("ecart", "Feuille d'analyse à compléter")
    assert etat["indicateurs"]["ecarts"] == 1 and etat["indicateurs"]["taux_reponse"] == 100
    with pytest.raises(ValueError, match="plus de relance"):
        suivi.enregistrer_relance(m, e, "2026-01-20", "courriel", "Auditeur Test", aujourd_hui=date(2026, 1, 20))
    etat = suivi.analyser_ecart(m, e, "Facture du 30/12 non comptabilisée par le tiers", None, None, "Auditeur Test", jour)
    assert etat["demandes"][0]["statut"]["prochaine_etape"] == "Écart analysé"
    # Correction : nouvelle version, l'historique reste.
    etat = suivi.enregistrer_reponse(m, e, {"type": "accord_total", "canal": "postal", "recue_le": "2026-01-12",
                                            "commentaire": "Réponse corrigée après rapprochement"}, None, None, "Auditeur Test", jour)
    d = etat["demandes"][0]
    assert [r["version"] for r in d["reponses"]] == [1, 2]
    assert d["statut"]["cle"] == "reponse_recue"
    actions = [j["action"] for j in base["db"]["CirJournal"].docs]
    assert {"Demande de confirmation envoyée", "Réponse enregistrée", "Analyse d'écart enregistrée", "Réponse corrigée"} <= set(actions)
    assert all(j["module"] == "Suivi des réponses" for j in base["db"]["CirJournal"].docs if "Réponse" in j["action"])


def test_piece_d_une_autre_mission_refusee(base):
    class Fichier(io.BytesIO):
        filename = "reponse.pdf"
        mission_id = "autre"
    i = ObjectId()
    base["stockage"].get = lambda oid: Fichier(b"%PDF")
    with pytest.raises(ValueError, match="introuvable"):
        suivi.lire_piece(base["mission_id"], str(i))
