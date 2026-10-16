"""
Import V2 de la balance générale : règle des sous-totaux et conversion vers
la forme des documents de l'import V1. Données FICTIVES (montants repris de
la structure du cas KDG 2025, sans fichier réel).
"""
import io

import openpyxl

from src.services import balance_generale_service as service
from src.services import mapping_apercu_service as apercu
from src.services import rapprochement_ipe_service as ipe


def _l(numero, debit_fin=0.0, credit_fin=0.0, debit_initial=0.0, credit_initial=0.0, debit_mvt=0.0, credit_mvt=0.0, libelle=""):
    return {"numero_compte": numero, "libelle": libelle, "debit_initial": debit_initial, "credit_initial": credit_initial,
            "debit_mvt": debit_mvt, "credit_mvt": credit_mvt, "debit_fin": debit_fin, "credit_fin": credit_fin}


def _numeros(lignes):
    return [l["numero_compte"] for l in lignes]


def test_sous_totaux_imbriques_ecartes_sans_double_comptage():
    lignes = [
        _l("283800", credit_fin=169_722), _l("284100", credit_fin=345_000),
        _l("284400", credit_fin=341_949), _l("284410", credit_fin=2_378_635),
        _l("284", credit_fin=3_065_584), _l("28", credit_fin=3_235_306),
    ]
    comptes, sous_totaux, _ = service.detecter_sous_totaux(lignes)
    assert _numeros(comptes) == ["283800", "284100", "284400", "284410"]
    assert _numeros(sous_totaux) == ["284", "28"]
    # « 28 » ne résume que les 4 comptes, pas le sous-total « 284 » en plus.
    assert {s["numero_compte"]: s["nb_comptes_detail"] for s in sous_totaux} == {"284": 3, "28": 4}
    assert sum(c["credit_fin"] for c in comptes) == 3_235_306


def test_le_libelle_n_est_jamais_lu():
    # Libellé « total » mais montant différent de la somme : jamais écartée d'office.
    lignes = [_l("4011", credit_fin=100, libelle="total fournisseurs"), _l("40111", credit_fin=60)]
    comptes, sous_totaux, ambigus = service.detecter_sous_totaux(lignes)
    assert _numeros(comptes) == ["4011", "40111"] and sous_totaux == []
    assert [a["numero_compte"] for a in ambigus] == ["4011"]


def test_compte_sans_sous_compte_conserve():
    lignes = [_l("410000", debit_fin=386_297_775), _l("401000", credit_fin=3_665_000)]
    comptes, sous_totaux, _ = service.detecter_sous_totaux(lignes)
    assert len(comptes) == 2 and sous_totaux == []


def test_les_trois_paires_doivent_correspondre_sinon_ligne_ambigue():
    # Même solde final, mais ouverture différente : ni écartée ni gardée en silence.
    lignes = [_l("43", credit_fin=110, credit_initial=5), _l("430000", credit_fin=10), _l("431300", credit_fin=100)]
    comptes, sous_totaux, ambigus = service.detecter_sous_totaux(lignes)
    assert sous_totaux == [] and len(comptes) == 3
    assert [a["numero_compte"] for a in ambigus] == ["43"]
    assert ambigus[0]["decision"] is None
    assert ambigus[0]["ecarts"]["ouverture"]["correspond"] is False
    assert ambigus[0]["ecarts"]["solde_final"]["correspond"] is True


def test_ecart_d_arrondi_tolere():
    lignes = [_l("52", debit_fin=74_540.004), _l("521104", debit_fin=74_540.0)]
    assert _numeros(service.detecter_sous_totaux(lignes)[1]) == ["52"]


def test_conversion_forme_v1_depuis_les_noms_de_la_balance_generale():
    ligne = service.convertir_en_forme_v1({"numero": "401000", "libelle": "FOURNISS.LOCAUX", "debit_initial": 5_723_000,
                                           "credit_initial": 6_438_000, "debit_mvt": 0, "credit_mvt": 2_950_000,
                                           "debit_fin": 0, "credit_fin": 3_665_000})
    assert ligne == {"numero_compte": "401000", "libelle": "FOURNISS.LOCAUX", "debit_initial": 5_723_000.0,
                     "credit_initial": 6_438_000.0, "debit_mvt": 0.0, "credit_mvt": 2_950_000.0, "debit_fin": 0.0,
                     "credit_fin": 3_665_000.0, "solde_reel": -3_665_000.0, "solde": 3_665_000.0, "sign_solde": "C"}


def test_conversion_depuis_le_format_y3_et_solde_final_deduit():
    ligne = service.convertir_en_forme_v1({"numero_compte": "411100", "libelle_compte": "CLIENT", "solde_ouverture_debit": 100,
                                           "solde_ouverture_credit": 0, "mouvement_debit": 50, "mouvement_credit": 30})
    assert (ligne["debit_fin"], ligne["credit_fin"], ligne["sign_solde"]) == (120.0, 0.0, "D")


def test_conversion_montant_unique():
    ligne = service.convertir_en_forme_v1({"numero": "401", "libelle": "F", "montant": -250})
    assert (ligne["debit_fin"], ligne["credit_fin"], ligne["solde_reel"]) == (0.0, 250.0, -250.0)


def test_lecture_d_un_fichier_8_colonnes_avec_lignes_de_titre():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["BALANCE GENERALE FICTIVE"])
    ws.append(["Exercice 2025"])
    ws.append(["Compte", "Intitulé", "Débit ouverture", "Crédit ouverture", "Débit mvt", "Crédit mvt", "Débit fin", "Crédit fin"])
    ws.append(["284100", "AMORT", 0, 345_000, 0, 0, 0, 345_000])
    ws.append(["284410", "AMORT INFO", 0, 1_487_383, 0, 891_252, 0, 2_378_635])
    ws.append(["284", "total 284", 0, 1_832_383, 0, 891_252, 0, 2_723_635])
    tampon = io.BytesIO()
    wb.save(tampon)
    tampon.seek(0)
    resultat = apercu.generer_apercu_mapping(tampon)
    assert resultat["format_propose"] == "standard" and resultat["ligne_entete"] == 3
    tampon.seek(0)
    lignes = [service.convertir_en_forme_v1(l) for l in apercu.lire_lignes_selon_mapping(tampon, resultat["mapping_propose"])]
    comptes, sous_totaux, _ = service.detecter_sous_totaux(lignes)
    assert _numeros(comptes) == ["284100", "284410"] and _numeros(sous_totaux) == ["284"]


def test_racines_des_collectifs_definies_a_un_seul_endroit():
    assert ipe.RACINES_COLLECTIFS == {"clients": "41", "fournisseurs": "40"}
    assert ipe.FAMILLES_IPE["ipe_1_clients"]["racine_collectif"] == "41"
    assert ipe.FAMILLES_IPE["ipe_2_fournisseurs"]["racine_collectif"] == "40"


def test_collectif_clients_en_410000_rattache_les_tiers_4111():
    lignes_bg = [{"numero_compte": "410000", "solde_reel": 300.0}]
    lignes_aux = [{"numero_compte": "4111AV", "solde_final_debit": 200.0, "solde_final_credit": 0.0},
                  {"numero_compte": "4111KD", "solde_final_debit": 100.0, "solde_final_credit": 0.0}]
    resultat = ipe.rapprocher_famille(lignes_bg, lignes_aux, ipe.RACINES_COLLECTIFS["clients"], "numero_compte")
    assert resultat["collectifs"][0]["nb_tiers_rattaches"] == 2
    assert resultat["collectifs"][0]["ok"] is True


def test_remplacement_de_la_balance_generale_invalide_une_validation_ipe():
    from src.services import verrou_ipe_service
    etat = {"ipe_fiabilite_validee": True, "fichiers_references": {"balance_generale": {"_id": "bg_v1"}}}
    decision = verrou_ipe_service.decider_invalidation(etat, service.TYPE_FICHIER, "bg_v2")
    assert decision["updates"]["ipe.ipe_fiabilite_validee"] is False
    assert decision["updates"]["ipe.statut_circuit"] == "en_cours"
    assert decision["resultat"] == {"type_fichier": "balance_generale", "module": None}



def test_sous_total_en_solde_net_reconnu():
    # Structure du cas KDG, ligne 661 : le sous-total compense débit et crédit.
    lignes = [_l("661", debit_fin=10_105_939), _l("661100", debit_fin=10_389_962), _l("661400", credit_fin=284_023)]
    comptes, sous_totaux, ambigus = service.detecter_sous_totaux(lignes)
    assert _numeros(sous_totaux) == ["661"] and ambigus == []


def test_choix_de_l_auditeur_sur_une_ligne_ambigue():
    # Structure du cas KDG, ligne 63 : 2 500 000 de mouvements créditeurs absents des comptes.
    # Mouvements reconnus en net, mais solde final différent de la somme : ambiguë.
    lignes = [_l("63", debit_mvt=9_823_378, credit_mvt=2_500_000, debit_fin=9_823_378),
              _l("631800", debit_mvt=7_323_378, debit_fin=7_323_378)]
    _, sous_totaux, ambigus = service.detecter_sous_totaux(lignes)
    assert sous_totaux == [] and [a["numero_compte"] for a in ambigus] == ["63"]
    comptes, sous_totaux, ambigus = service.detecter_sous_totaux(lignes, {"63": "ecarter"})
    assert _numeros(sous_totaux) == ["63"] and sous_totaux[0]["motif"] == "sous_total_ecarte_par_l_auditeur"
    assert _numeros(comptes) == ["631800"] and ambigus[0]["decision"] == "ecarter"
    comptes, sous_totaux, ambigus = service.detecter_sous_totaux(lignes, {"63": "garder"})
    assert sous_totaux == [] and len(comptes) == 2 and ambigus[0]["decision"] == "garder"


def test_le_choix_sur_une_ligne_ambigue_est_reporte_sur_son_parent():
    # 621 est ambiguë (mouvements absents de son compte). Écartée, son parent 62
    # correspond à 621100 + 622100 ; gardée, elle s'ajoute à la somme et 62 devient ambigu.
    lignes = [_l("621", debit_fin=100, debit_mvt=50), _l("621100", debit_fin=100),
              _l("622100", debit_fin=40), _l("62", debit_fin=140)]
    _, sous_totaux, ambigus = service.detecter_sous_totaux(lignes, {"621": "ecarter"})
    assert _numeros(sous_totaux) == ["621", "62"] and [a["numero_compte"] for a in ambigus] == ["621"]
    _, sous_totaux, ambigus = service.detecter_sous_totaux(lignes, {"621": "garder"})
    assert sous_totaux == [] and {a["numero_compte"] for a in ambigus} == {"621", "62"}


def test_decision_invalide_ignoree():
    lignes = [_l("43", credit_fin=110, credit_initial=5), _l("430000", credit_fin=110)]
    _, _, ambigus = service.detecter_sous_totaux(lignes, {"43": "supprimer"})
    assert ambigus[0]["decision"] is None


def test_equilibre_par_paire():
    equilibree = service.controler_equilibre([_l("101", credit_fin=100, credit_initial=100), _l("521", debit_fin=100, debit_initial=100)])
    assert equilibree["ok"] is True
    desequilibree = service.controler_equilibre([_l("101", credit_fin=100), _l("521", debit_fin=70)])
    assert desequilibree["ok"] is False
    assert desequilibree["paires"]["solde_final"]["ecart"] == -30
    assert desequilibree["paires"]["ouverture"]["ok"] is True


def test_analyse_du_fichier_signale_lignes_ambigues_et_desequilibre():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["BALANCE GENERALE FICTIVE"])
    ws.append(["Compte", "Intitulé", "Débit ouverture", "Crédit ouverture", "Débit mvt", "Crédit mvt", "Débit fin", "Crédit fin"])
    ws.append(["631800", "FRAIS", 0, 0, 7_323_378, 0, 7_323_378, 0])
    ws.append(["63", "total 63", 0, 0, 9_823_378, 2_500_000, 9_823_378, 0])
    ws.append(["101000", "CAPITAL", 0, 0, 0, 7_000_000, 0, 7_000_000])
    tampon = io.BytesIO()
    wb.save(tampon)
    tampon.filename = "bg_fictive.xlsx"
    analyse = service.analyser_fichier(tampon, "client_fictif")
    assert [a["code"] for a in service.alertes_analyse(analyse)] == ["sous_total_ambigu", "desequilibre"]
    tampon.seek(0)
    analyse = service.analyser_fichier(tampon, "client_fictif", decisions={"63": "ecarter"})
    assert [a["code"] for a in service.alertes_analyse(analyse)] == ["desequilibre"]
    assert analyse["controles"]["sous_totaux"]["lignes"][0]["motif"] == "sous_total_ecarte_par_l_auditeur"


def _mission_remplacee(**donnees):
    """Mission fictive : balance remplacée une fois (v1 -> v2) le 16/10/2026."""
    empreintes = {d: service._empreinte(donnees.get(d)) for d in service.DONNEES_V1_DERIVEES}
    return {**donnees, "balance_generale_remplacements": [
        {"version_remplacee": 1, "horodatage": "2026-10-16T09:00:00", "empreintes": empreintes}]}


def test_fraicheur_sans_remplacement_tout_est_a_jour():
    assert all(v is None for v in service.fraicheur_par_etape({"balance_variation": [1], "efi": {}}).values())


def test_fraicheur_apres_remplacement_donnees_perimees():
    fraicheur = service.fraicheur_par_etape(_mission_remplacee(balance_variation=[1], grouping=[2], efi={"a": 1}))
    assert fraicheur["materialite"] == {"version": 1, "remplacee_le": "2026-10-16T09:00:00"}
    assert fraicheur["quantitatif"]["version"] == 1 and fraicheur["efi"]["version"] == 1


def test_fraicheur_apres_recalcul_par_l_etape_9():
    mission = _mission_remplacee(balance_variation=[1], grouping=[2], efi={"a": 1})
    # L'étape 9 recalcule balance_variation et grouping depuis les balances (efi jamais).
    mission["balance_variation"], mission["grouping"] = [9], [9]
    fraicheur = service.fraicheur_par_etape(mission)
    assert fraicheur["quantitatif"] is None and fraicheur["efi"] is None
    assert fraicheur["materialite"]["version"] == 1
    assert fraicheur["revue"]["version"] == 1


def test_script_de_mesure_d_impact_en_lecture_seule():
    import mesure_impact_sous_totaux as script

    class CollectionFactice:
        def __init__(self, docs):
            self.docs = docs

        def find(self, *a, **k):
            return list(self.docs)

        def find_one(self, filtre, *a, **k):
            return next((d for d in self.docs if d["_id"] == filtre["_id"]), None)

        def insert_one(self, *a, **k):
            raise AssertionError("écriture interdite")

    acces = script.LectureSeule(CollectionFactice([]))
    assert not any(hasattr(acces, m) for m in ("insert_one", "update_one", "delete_one", "replace_one", "bulk_write"))

    from bson import ObjectId
    bg = ObjectId()
    balances = CollectionFactice([{"_id": bg, "annee_balance": 2025, "balance": [
        _l("284100", credit_fin=100), _l("284", credit_fin=100), _l("521", debit_fin=100)]}])
    missions = CollectionFactice([{"_id": ObjectId(), "id_client": "c", "annee_auditee": "2025", "balances": [str(bg)]}])
    clients = CollectionFactice([])
    nb_missions, nb_balances, touchees, lignes = script.mesurer(
        script.LectureSeule(missions), script.LectureSeule(balances), script.LectureSeule(clients))
    assert (nb_missions, nb_balances, len(touchees)) == (1, 1, 1)
    assert lignes[0][6] == 1 and lignes[0][-1] == "équilibrée"
    assert script.uri_masquee("mongodb://alice:secret@hote:27017/base") == "mongodb://alice:***@hote:27017/base"
