"""
Paramètres communs (page C) : consultation seule, valeurs lues là où le code
les définit (une seule source), regroupement des endpoints verrouillables
sans changement de la liste.
"""
import inspect

from src.resources import parametres_resources
from src.services import parametres_service
from src.services import rapprochement_ipe_service as rapprochement
from src.services import revue_ipe_service as revue
from src.services import verrou_ipe_service as verrou


def test_valeurs_lues_a_la_source(monkeypatch):
    monkeypatch.setitem(rapprochement.RACINES_COLLECTIFS, "clients", "411")
    monkeypatch.setattr(revue, "CAUSES_ECART", ("Cause A",))
    monkeypatch.setattr(rapprochement, "TOLERANCE_ECART_IPE", 1.5)
    p = parametres_service.lire_parametres()
    assert p["rapprochements"]["racines"][0]["valeur"] == "411"
    assert p["causes_ecart"]["valeurs"] == ["Cause A"]
    assert p["rapprochements"]["seuils"][0]["valeur"] == 1.5


def test_valeurs_actuelles():
    p = parametres_service.lire_parametres()
    assert p["modifiable"] is False
    assert [r["valeur"] for r in p["rapprochements"]["racines"]] == ["41", "40"]
    assert p["rapprochements"]["immobilisations"]["valeur"] == "20 à 28"
    assert p["rapprochements"]["immobilisations"]["detail"] == "20 à 27 : valeurs brutes · 28 : amortissements"
    assert p["rapprochements"]["seuils"][0]["valeur"] == 0.0
    assert p["rapprochements"]["seuils"][1] == {"libelle": "Seuil d'écart significatif (%)", "valeur": None, "applique": False}
    assert [c["valeur"] for c in p["circularisation"]["cadence"]] == ["J0", "J+15", "J+30", "J+45"]
    assert [e["etape"] for e in p["etapes_verrou"]["bloquees"]] == [5, 6, 7, 8, 9, 10, 11]
    assert {s["categorie"] for s in (p["verrou"]["source"], p["causes_ecart"]["source"], p["circularisation"]["source"])} \
        <= {parametres_service.CAHIER_DES_CHARGES, parametres_service.SPEC_A_CONFIRMER, parametres_service.DECISION_PROVISOIRE}


def test_etat_du_verrou_lu_dans_l_environnement(monkeypatch):
    monkeypatch.delenv("IPE_VERROU_ACTIF", raising=False)
    assert parametres_service.lire_parametres()["verrou"]["actif"] is False
    monkeypatch.setenv("IPE_VERROU_ACTIF", "true")
    assert parametres_service.lire_parametres()["verrou"]["actif"] is True


def test_regroupement_par_etape_ne_change_pas_la_liste_verrouillee():
    # Liste d'avant le regroupement par étape (page C) : strictement identique.
    assert verrou.ENDPOINTS_VERROUILLABLES == {
        "mission.materialite_route", "mission.get_benchmarks", "mission.save_materiality",
        "mission.validate_materiality", "mission.get_materiality",
        "mission.analyse_quantitative_route", "mission.save_quantitative_threshold_mode",
        "mission.save_quantitative_threshold_mode_alias", "mission.make_quantitative_analysis",
        "mission.download_analyse_quantitative",
        "mission.analyse_qualitative_route", "mission.init_qualitative_responses_route",
        "mission.save_qualitative_responses_route", "mission.make_qualitative_analysis",
        "mission.download_analyse_qualitative",
        "mission.presentation_comptes_significatifs_route",
        "mission.get_grouping_with_qualitative", "mission.make_final", "mission.download_grouping",
        "mission.etats_financiers_preliminaires_route", "mission.classement_bilan_route",
        "mission.revue_analytique_route", "mission.update_commentaire_route",
        "mission.revue_analytique_finale_route", "mission.save_revue_analytique_route",
        "mission.download_revue_analytique",
    }


def test_tolerance_par_defaut_des_rapprochements_inchangee():
    for fonction in (rapprochement.rapprocher_famille, rapprochement.rapprocher_immobilisations):
        assert inspect.signature(fonction).parameters["tolerance"].default == 0.0


def test_consultation_seule():
    assert [n for n, _ in inspect.getmembers(parametres_resources.ParametresResource, inspect.isfunction)] == ["lire"]
    source = inspect.getsource(parametres_service)
    for ecriture in ("get_database", "insert_", "update_", "delete_", "os.environ["):
        assert ecriture not in source
