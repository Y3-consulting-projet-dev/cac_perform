"""
Tests de verrou_ipe_service.py : décision de blocage IPE-GLOBAL-01 et statut
affiché pour l'indicateur « Fiabilité IPE » de la barre latérale.
Voir docs/PLAN_verrou_IPE.md §3, §6, §7.

Fonctions pures testées directement, sans contexte Flask/DB (verifier_verrou_ipe
et capturer_verrou_applicable_a_la_creation, qui ont besoin de Flask/Mongo, ne
sont pas testés ici).
"""
from src.services import verrou_ipe_service as service


def test_verrou_desactive_est_un_noop():
    """IPE_VERROU_ACTIF désactivé : verrou_actif() est False par défaut (pas de variable d'env positionnée)."""
    assert service.verrou_actif() is False


def test_mission_anterieure_au_verrou_jamais_bloquee():
    etat = {"verrou_applicable": False, "ipe_fiabilite_validee": False}
    assert service.mission_est_bloquee(etat) is False


def test_mission_anterieure_au_verrou_jamais_bloquee_meme_sans_sous_document():
    """Sous-document Mission1.ipe absent (ancienne mission) -> jamais bloquée."""
    etat = service._etat_par_defaut()
    assert service.mission_est_bloquee(etat) is False


def test_mission_verrou_applicable_etat_inconnu_est_bloquante():
    """verrou_applicable=True et ipe_fiabilite_validee jamais évalué (None) -> bloquée (prudence par défaut)."""
    etat = {"verrou_applicable": True, "ipe_fiabilite_validee": None}
    assert service.mission_est_bloquee(etat) is True


def test_mission_verrou_applicable_fausse_est_bloquante():
    etat = {"verrou_applicable": True, "ipe_fiabilite_validee": False}
    assert service.mission_est_bloquee(etat) is True


def test_mission_verrou_applicable_validee_nest_pas_bloquante():
    etat = {"verrou_applicable": True, "ipe_fiabilite_validee": True}
    assert service.mission_est_bloquee(etat) is False


def test_endpoint_hors_liste_nest_jamais_verrouillable():
    assert service.endpoint_est_verrouillable("mission.controle_coherence_route") is False
    assert service.endpoint_est_verrouillable("mission.new_assign") is False
    assert service.endpoint_est_verrouillable(None) is False


def test_endpoint_de_la_liste_est_verrouillable():
    assert service.endpoint_est_verrouillable("mission.materialite_route") is True
    assert service.endpoint_est_verrouillable("mission.revue_analytique_finale_route") is True


def test_statut_affiche_anterieure_au_verrou():
    etat = service._etat_par_defaut()
    assert service.statut_affiche(etat) == "anterieure_au_verrou"


def test_statut_affiche_non_commence():
    etat = {"verrou_applicable": True, "ipe_fiabilite_validee": None, "modules": {}}
    assert service.statut_affiche(etat) == "non_commence"


def test_statut_affiche_en_cours():
    etat = {
        "verrou_applicable": True,
        "ipe_fiabilite_validee": None,
        "modules": {"ipe_1_clients": {"statut": "ecart"}},
    }
    assert service.statut_affiche(etat) == "en_cours"


def test_statut_affiche_valide():
    """statut_affiche est dérivé de statut_circuit (jamais de ipe_fiabilite_validee directement)."""
    etat = {"verrou_applicable": True, "statut_circuit": "valide", "modules": {}}
    assert service.statut_affiche(etat) == "valide"


def test_statut_affiche_soumis_pour_revue():
    etat = {"verrou_applicable": True, "statut_circuit": "soumis_pour_revue", "modules": {}}
    assert service.statut_affiche(etat) == "soumis_pour_revue"


def test_statut_affiche_en_attente_correction():
    etat = {"verrou_applicable": True, "statut_circuit": "en_attente_correction", "modules": {}}
    assert service.statut_affiche(etat) == "en_attente_correction"


# ---------------------------------------------------------------------------
# detecter_fichiers_modifies — vérification à la lecture : détecte un
# remplacement de fichier (notamment la balance générale, importée par le
# flux V1 / model.py, qui ne déclenche aucune invalidation à l'écriture).
# ---------------------------------------------------------------------------

def test_detecter_fichiers_modifies_aucun_changement():
    references = {
        "balance_generale": {"_id": "bal_n", "annee_balance": 2025},
        "auxiliaire_fournisseur": {"_id": "aux_v1", "version": 1},
    }
    actuelles = {"balance_generale": "bal_n", "auxiliaire_fournisseur": "aux_v1"}
    assert service.detecter_fichiers_modifies(references, actuelles) == []


def test_detecter_fichiers_modifies_balance_generale_remplacee_hors_hook():
    """
    La balance générale (flux V1, api/src/model.py) n'a pas de hook
    d'invalidation à l'écriture : c'est bien ce cas que la vérification à la
    lecture doit détecter, via un _id qui a changé.
    """
    references = {"balance_generale": {"_id": "bal_n_ancienne", "annee_balance": 2025}}
    actuelles = {"balance_generale": "bal_n_nouvelle"}

    changements = service.detecter_fichiers_modifies(references, actuelles)

    assert len(changements) == 1
    assert changements[0]["type_fichier"] == "balance_generale"
    assert changements[0]["id_reference"] == "bal_n_ancienne"
    assert changements[0]["id_actuel"] == "bal_n_nouvelle"


def test_detecter_fichiers_modifies_fichier_devenu_introuvable():
    """Un fichier référencé qui n'est plus résolvable (None) est bien un changement, jamais ignoré."""
    references = {"immobilisations": {"_id": "immo_v1", "version": 1}}
    actuelles = {"immobilisations": None}
    changements = service.detecter_fichiers_modifies(references, actuelles)
    assert len(changements) == 1
    assert changements[0]["id_actuel"] is None


def test_detecter_fichiers_modifies_ignore_les_types_non_references():
    """Un type présent dans les références actuelles mais jamais figé par la validation n'est jamais signalé."""
    references = {"balance_generale": {"_id": "bal_n", "annee_balance": 2025}}
    actuelles = {"balance_generale": "bal_n", "auxiliaire_client": "aux_v1"}
    assert service.detecter_fichiers_modifies(references, actuelles) == []


def test_lire_etat_ipe_renvoie_les_fichiers_du_dernier_rapprochement(monkeypatch):
    # Régression : sans ce champ, refus_rapprochement croyait toujours le
    # rapprochement inconnu et toute soumission pour revue était refusée.
    from bson import ObjectId
    from src.services import verrou_ipe_service

    fichiers = {"balance_generale": "bg1", "auxiliaire_fournisseur": "frs1"}

    class CollectionFactice:
        def find_one(self, *args, **kwargs):
            return {"ipe": {"modules": {"ipe_2_fournisseurs": {"statut": "ok"}}, "fichiers_evalues": fichiers}}

    monkeypatch.setattr(verrou_ipe_service, "_collection", lambda: CollectionFactice())
    etat = verrou_ipe_service.lire_etat_ipe(str(ObjectId()))
    assert etat["fichiers_evalues"] == fichiers

    from src.services import revue_ipe_service
    assert revue_ipe_service.refus_rapprochement(etat, dict(fichiers)) is None
