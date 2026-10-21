"""
Circularisation, sous-lot b : bibliothèque de modèles (champs détectés,
versions), annuaire des coordonnées (versions, état des tiers), valeurs de
fusion. Données FICTIVES, base et GridFS en mémoire.
"""
import io
import zipfile

import pytest
from bson import ObjectId

from src.services import circularisation_service as cir
from src.services import courriers_service as courriers
from tests.test_circularisation_service import BaseFactice

MOTIF = "Solde significatif au regard de la population"


def docx(texte_xml: str, en_tete: str = "") -> bytes:
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", f"<w:document><w:body>{texte_xml}</w:body></w:document>")
        if en_tete:
            z.writestr("word/header1.xml", f"<w:hdr>{en_tete}</w:hdr>")
    return flux.getvalue()


# Word découpe souvent un champ en plusieurs morceaux de texte.
MODELE = docx(
    "<w:p><w:r><w:t>Objet : confirmation de solde de </w:t></w:r><w:r><w:t>{{ ti</w:t></w:r>"
    "<w:r><w:t>ers_raison_sociale }}</w:t></w:r></w:p>"
    "<w:p><w:r><w:t>Solde : {{solde}} FCFA, réponse à {{ adresse_retour }} · {{ solde }}</w:t></w:r></w:p>",
    en_tete="<w:p><w:r><w:t>{{ entite }}</w:t></w:r></w:p>",
)


def test_champs_detectes_meme_decoupes_par_word():
    assert courriers.champs_du_modele(MODELE) == ["tiers_raison_sociale", "solde", "adresse_retour", "entite"]


def test_fichier_qui_n_est_pas_un_docx():
    with pytest.raises(ValueError, match="pas un document Word"):
        courriers.champs_du_modele(b"pas un zip")
    flux = io.BytesIO()
    with zipfile.ZipFile(flux, "w") as z:
        z.writestr("autre.xml", "<a/>")
    with pytest.raises(ValueError, match="pas un document Word"):
        courriers.champs_du_modele(flux.getvalue())


def test_etat_des_tiers():
    assert courriers.etat_tiers(None) == "coordonnees_manquantes"
    assert courriers.etat_tiers({"adresse": "BP 1 Abidjan"}) == "courriel_manquant"
    assert courriers.etat_tiers({"courriel": "compta@tiers.ci"}) == "pret"


class GridFSFactice:
    def __init__(self):
        self.fichiers = {}

    def put(self, contenu, **meta):
        i = ObjectId()
        self.fichiers[i] = (contenu, meta)
        return i

    def get(self, i):
        return io.BytesIO(self.fichiers[i][0])


@pytest.fixture
def base(monkeypatch):
    db = BaseFactice()
    mission_id, client_id = ObjectId(), ObjectId()
    db["Client_db"].insert_one({"_id": client_id, "company_name": "CLIENT FICTIF", "address": "Plateau, Abidjan"})
    db["Mission1"].insert_one({"_id": mission_id, "id_client": str(client_id), "annee_auditee": "2025"})
    fichier_id = ObjectId()
    db["Balance"].insert_one({"_id": fichier_id, "mission_id": str(mission_id), "type": "auxiliaire_fournisseur",
                              "nom_fichier": "aux_frs.xlsx", "version": 1, "date_import": "2026-10-15T10:00:00",
                              "balance": [{"numero_compte": "4011A", "libelle_compte": "FOURNISSEUR A",
                                           "solde_final_debit": 0, "solde_final_credit": 600_000},
                                          {"numero_compte": "4011B", "libelle_compte": "FOURNISSEUR B",
                                           "solde_final_debit": 0, "solde_final_credit": 10_000}]})
    stockage = GridFSFactice()
    for module in (cir, courriers):
        monkeypatch.setattr(module, "_db", lambda: db)
    monkeypatch.setattr(courriers, "_gridfs", lambda: stockage)
    monkeypatch.setattr(cir, "_fichier_actif", lambda m, t: {"_id": str(fichier_id), "nom_fichier": "aux_frs.xlsx",
                                                              "version": 1} if t == "auxiliaire_fournisseur" else None)
    monkeypatch.setattr(cir, "_etat_ipe", lambda m: {"statut_affiche": "valide"})
    m = str(mission_id)
    cir.constituer_population(m, "fournisseurs", "Auditeur Test")
    cir.decider_tiers(m, "fournisseurs", "4011A", True, MOTIF, "Auditeur Test")
    return {"db": db, "mission_id": m, "client_id": str(client_id), "stockage": stockage}


def test_tiers_retenus_avec_etat_et_valeurs_de_fusion(base):
    etat = courriers.lire_courriers(base["mission_id"])
    (groupe,) = etat["groupes"]
    assert groupe["code_modele"] == "C2"
    (tiers,) = groupe["tiers"]  # 4011B non retenu : absent
    assert tiers["etat"] == "coordonnees_manquantes"
    assert tiers["valeurs"]["tiers_raison_sociale"] == "FOURNISSEUR A"  # libellé de la balance à défaut d'annuaire
    assert tiers["valeurs"]["solde"] == -600_000
    assert tiers["valeurs"]["entite"] == "CLIENT FICTIF" and tiers["valeurs"]["adresse_entite"] == "Plateau, Abidjan"
    assert etat["generation_disponible"] is False


def test_coordonnees_versionnees_dans_l_annuaire_du_client(base):
    m = base["mission_id"]
    with pytest.raises(ValueError, match="au moins une adresse"):
        courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A", {"contact": "M. X"}, "Auditeur Test")
    with pytest.raises(ValueError, match="courriel invalide"):
        courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A", {"courriel": "pas-un-courriel"}, "Auditeur Test")
    with pytest.raises(ValueError, match="absent de la population"):
        courriers.enregistrer_coordonnees(m, "fournisseurs", "9999", {"adresse": "BP 1"}, "Auditeur Test")
    with pytest.raises(ValueError, match="utilisateur non identifié"):
        courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A", {"adresse": "BP 1"}, None)

    etat = courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A", {"adresse": "BP 1 Abidjan"}, "Auditeur Test")
    assert etat["groupes"][0]["tiers"][0]["etat"] == "courriel_manquant"
    with pytest.raises(ValueError, match="Aucune modification"):
        courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A", {"adresse": "BP 1 Abidjan"}, "Auditeur Test")
    etat = courriers.enregistrer_coordonnees(m, "fournisseurs", "4011A",
                                             {"adresse": "BP 1 Abidjan", "courriel": "compta@a.ci"}, "Auditeur Test")
    tiers = etat["groupes"][0]["tiers"][0]
    assert (tiers["etat"], tiers["coordonnees"]["version"]) == ("pret", 2)
    docs = base["db"]["CirCoordonnees"].docs
    assert [d["actif"] for d in docs] == [False, True]
    assert all(d["id_client"] == base["client_id"] for d in docs)
    assert base["db"]["CirJournal"].docs[-1]["module"] == "Courriers"


def test_import_de_modele_versionne(base):
    m = base["mission_id"]
    with pytest.raises(ValueError, match="Modèle inconnu"):
        courriers.importer_modele(m, "C9", "modele.docx", MODELE, "Auditeur Test")
    with pytest.raises(ValueError, match="Format attendu"):
        courriers.importer_modele(m, "C2", "modele.pdf", MODELE, "Auditeur Test")
    etat = courriers.importer_modele(m, "C2", "c2_v1.docx", MODELE, "Auditeur Test")
    c2 = next(x for x in etat["modeles"] if x["code"] == "C2")["actif"]
    assert (c2["version"], c2["champs_inconnus"]) == (1, ["adresse_retour"])
    etat = courriers.importer_modele(m, "C2", "c2_v2.docx", docx("<w:t>{{ entite }}</w:t>"), "Auditeur Test")
    c2 = next(x for x in etat["modeles"] if x["code"] == "C2")["actif"]
    assert (c2["version"], c2["champs"], c2["champs_inconnus"]) == (2, ["entite"], [])
    assert [d["actif"] for d in base["db"]["CirModele"].docs] == [False, True]
    fichier = courriers.lire_fichier_modele(c2["_id"])
    assert fichier["nom_fichier"] == "c2_v2.docx" and courriers.champs_du_modele(fichier["contenu"]) == ["entite"]
    assert "dont inconnus : adresse_retour" in base["db"]["CirJournal"].docs[-2]["detail"]
