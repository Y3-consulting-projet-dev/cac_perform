"""
Circularisation, sous-lot a : population, sélection manuelle avec motif,
mode de confirmation, mémo et son circuit. Données FICTIVES, base en mémoire.
"""
import copy

import pytest
from bson import ObjectId

from src.services import circularisation_service as cir

MOTIF = "Solde significatif au regard de la population"


class CollectionFactice:
    def __init__(self):
        self.docs = []

    @staticmethod
    def _correspond(doc, filtre):
        return all(doc.get(k) == v for k, v in filtre.items())

    def find_one(self, filtre, projection=None, sort=None):
        docs = [d for d in self.docs if self._correspond(d, filtre)]
        if sort:
            cle, sens = sort[0]
            docs.sort(key=lambda d: d.get(cle), reverse=sens < 0)
        return copy.deepcopy(docs[0]) if docs else None

    def find(self, filtre, projection=None):
        return [copy.deepcopy(d) for d in self.docs if self._correspond(d, filtre)]

    def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        doc.setdefault("_id", ObjectId())

        class Resultat:
            inserted_id = doc["_id"]
        self.docs.append(doc)
        return Resultat()

    def update_one(self, filtre, maj):
        for d in self.docs:
            if self._correspond(d, filtre):
                d.update(copy.deepcopy(maj.get("$set", {})))
                for cle, valeur in maj.get("$push", {}).items():
                    d.setdefault(cle, []).append(copy.deepcopy(valeur))
                return


class BaseFactice(dict):
    def __missing__(self, nom):
        self[nom] = CollectionFactice()
        return self[nom]


@pytest.fixture
def base(monkeypatch):
    db = BaseFactice()
    mission_id = ObjectId()
    client_id = ObjectId()
    fichier_id = ObjectId()
    db["Client_db"].insert_one({"_id": client_id, "company_name": "CLIENT FICTIF"})
    db["Mission1"].insert_one({"_id": mission_id, "id_client": str(client_id), "annee_auditee": ["2025"],
                               "materiality": [{"benchmark": "revenue", "choice": True, "materiality": 1_000_000,
                                                "performance_materiality": 800_000, "trivial_misstatements": 50_000}]})
    db["Balance"].insert_one({"_id": fichier_id, "mission_id": str(mission_id), "type": "auxiliaire_fournisseur",
                              "nom_fichier": "aux_frs.xlsx", "version": 1, "date_import": "2026-10-15T10:00:00",
                              "balance": [
                                  {"numero_compte": "4011A", "libelle_compte": "FOURNISSEUR A", "solde_final_debit": 0,
                                   "solde_final_credit": 600_000},
                                  {"numero_compte": "4011B", "libelle_compte": "FOURNISSEUR B", "solde_final_debit": 100_000,
                                   "solde_final_credit": 0},
                                  {"numero_compte": "", "libelle_compte": "TOTAL", "solde_final_debit": 0,
                                   "solde_final_credit": 500_000},
                              ]})
    actif = {"fichier": {"_id": str(fichier_id), "nom_fichier": "aux_frs.xlsx", "version": 1, "nb_lignes": 3}}
    monkeypatch.setattr(cir, "_db", lambda: db)
    monkeypatch.setattr(cir, "_fichier_actif", lambda m, t: actif["fichier"] if t == "auxiliaire_fournisseur" else None)
    monkeypatch.setattr(cir, "_etat_ipe", lambda m: {"statut_affiche": "en_cours", "ipe_fiabilite_validee": None})
    return {"db": db, "mission_id": str(mission_id), "actif": actif}


def test_population_photographiee_avec_l_etat_ipe(base):
    etat = cir.constituer_population(base["mission_id"], "fournisseurs", "Auditeur Test")
    selection = etat["selection"]
    assert [t["numero"] for t in selection["tiers"]] == ["4011A", "4011B"]  # ligne sans numéro ignorée
    assert [t["solde"] for t in selection["tiers"]] == [-600_000, 100_000]
    assert selection["population"]["ipe"]["statut_affiche"] == "en_cours"
    assert selection["population"]["source"]["nom_fichier"] == "aux_frs.xlsx"
    assert selection["indicateurs"]["valeur_population"] == 700_000
    assert selection["statut"] == "en_cours"
    assert base["db"]["CirJournal"].docs[-1]["action"] == "Population constituée"


def test_types_sans_population_et_utilisateur_obligatoire(base):
    with pytest.raises(ValueError, match="source à confirmer"):
        cir.constituer_population(base["mission_id"], "avocats", "Auditeur Test")
    with pytest.raises(ValueError, match="Aucune balance auxiliaire clients active"):
        cir.constituer_population(base["mission_id"], "clients", "Auditeur Test")
    with pytest.raises(ValueError, match="utilisateur non identifié"):
        cir.constituer_population(base["mission_id"], "fournisseurs", None)


def test_decision_avec_motif_obligatoire_et_tracee(base):
    cir.constituer_population(base["mission_id"], "fournisseurs", "Auditeur Test")
    with pytest.raises(ValueError, match="au moins 15 caractères"):
        cir.decider_tiers(base["mission_id"], "fournisseurs", "4011A", True, "trop court", "Auditeur Test")
    with pytest.raises(ValueError, match="absent de la population"):
        cir.decider_tiers(base["mission_id"], "fournisseurs", "9999", True, MOTIF, "Auditeur Test")
    etat = cir.decider_tiers(base["mission_id"], "fournisseurs", "4011A", True, MOTIF, "Auditeur Test")
    ligne = etat["selection"]["tiers"][0]
    assert (ligne["retenu"], ligne["origine"], ligne["motif"], ligne["utilisateur_id"]) == \
        (True, "ajout_manuel", MOTIF, "Auditeur Test")
    ind = etat["selection"]["indicateurs"]
    assert (ind["nb_retenus"], ind["valeur_couverte"]) == (1, 600_000)
    assert round(ind["taux_couverture"], 2) == 85.71
    with pytest.raises(ValueError, match="déjà retenu"):
        cir.decider_tiers(base["mission_id"], "fournisseurs", "4011A", True, MOTIF, "Auditeur Test")
    # Exclusion : nouvelle décision, l'historique garde les deux.
    etat = cir.decider_tiers(base["mission_id"], "fournisseurs", "4011A", False, "Finalement couvert par une autre procédure", "Auditeur Test")
    assert etat["selection"]["tiers"][0]["origine"] == "exclusion_manuelle"
    assert len(base["db"]["CirSelection"].docs[0]["decisions"]) == 2


def test_mode_negatif_exige_un_motif(base):
    cir.constituer_population(base["mission_id"], "fournisseurs", "Auditeur Test")
    with pytest.raises(ValueError, match="confirmation négative"):
        cir.definir_mode(base["mission_id"], "fournisseurs", "negatif", None, "Manager Test")
    etat = cir.definir_mode(base["mission_id"], "fournisseurs", "negatif", "Population nombreuse de faibles soldes", "Manager Test")
    assert etat["selection"]["mode"]["valeur"] == "negatif"
    assert etat["selection"]["mode"]["utilisateur_id"] == "Manager Test"


def test_circuit_du_memo(base):
    m = base["mission_id"]
    cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    cir.decider_tiers(m, "fournisseurs", "4011A", True, MOTIF, "Auditeur Test")
    apercu = cir.lire_memo(m, "fournisseurs")
    assert apercu["statut"] == "brouillon"
    assert apercu["contenu"]["entite"] == "CLIENT FICTIF" and apercu["contenu"]["exercice"] == "2025"
    assert apercu["contenu"]["decisions"][0]["libelle"] == "FOURNISSEUR A"

    etat = cir.soumettre_memo(m, "fournisseurs", "Auditeur Test")
    assert etat["selection"]["statut"] == "soumis_pour_revue"
    assert etat["selection"]["memo"]["version"] == 1
    # Sélection figée après la soumission.
    with pytest.raises(ValueError, match="Sélection figée"):
        cir.decider_tiers(m, "fournisseurs", "4011B", True, MOTIF, "Auditeur Test")
    with pytest.raises(ValueError, match="soumis pour revue"):
        cir.constituer_population(m, "fournisseurs", "Auditeur Test")

    etat = cir.demander_correction_memo(m, "fournisseurs", "Ajouter le fournisseur B, solde débiteur", "Manager Test")
    assert etat["selection"]["statut"] == "en_attente_correction"
    cir.decider_tiers(m, "fournisseurs", "4011B", True, MOTIF, "Auditeur Test")
    etat = cir.soumettre_memo(m, "fournisseurs", "Auditeur Test")
    assert etat["selection"]["memo"]["version"] == 2
    # Le mémo figé ne bouge plus.
    assert cir.lire_memo(m, "fournisseurs")["contenu"]["resultat"]["nb_retenus"] == 2
    with pytest.raises(ValueError, match="au moins 15 caractères"):
        cir.valider_memo(m, "fournisseurs", "ok", "Manager Test")
    etat = cir.valider_memo(m, "fournisseurs", "Sélection revue et conforme au plan", "Manager Test")
    assert etat["selection"]["statut"] == "valide"
    assert etat["selection"]["memo"]["decision"]["utilisateur_id"] == "Manager Test"
    actions = [j["action"] for j in base["db"]["CirJournal"].docs]
    assert actions[-1] == "Mémo validé" and "Correction du mémo demandée" in actions


def test_fichier_remplace_selection_a_refaire_et_soumission_refusee(base):
    m = base["mission_id"]
    cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    base["actif"]["fichier"] = {"_id": str(ObjectId()), "nom_fichier": "aux_frs_v2.xlsx", "version": 2}
    etat = cir.etat_type(m, "fournisseurs")
    assert "a été remplacé" in etat["selection"]["a_refaire"]
    with pytest.raises(ValueError, match="a été remplacé"):
        cir.soumettre_memo(m, "fournisseurs", "Auditeur Test")


def test_nouvelle_population_archive_la_precedente(base):
    m = base["mission_id"]
    cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    etat = cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    assert etat["selection"]["version"] == 2
    assert [d["actif"] for d in base["db"]["CirSelection"].docs] == [False, True]


def test_seuils_etape_5_lus_sans_correspondance_affirmee():
    seuils = cir.seuils_etape_5({"materiality": [{"choice": "", "materiality": 1}, {
        "choice": True, "benchmark": "revenue", "materiality": 900, "performance_materiality": 720,
        "trivial_misstatements": 45}]})
    assert [v["valeur"] for v in seuils["valeurs"]] == [900, 720, 45]
    assert "à confirmer par CAC-SEUILS-01" in seuils["correspondance"]
    assert cir.seuils_etape_5({"materiality": []})["disponible"] is False
