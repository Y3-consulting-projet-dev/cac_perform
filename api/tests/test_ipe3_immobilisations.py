"""
Tests d'IPE-3 (immobilisations) — voir docs/PLAN_verrou_IPE.md.
Le fichier des immobilisations liste des BIENS (valeur brute, amortissements
cumulés, valeur nette), pas des tiers. Données FICTIVES construites en
mémoire, jamais un fichier réel de client.
"""
import io

import openpyxl

from src.services import mapping_apercu_service as apercu
from src.services import rapprochement_ipe_service as service

CONFIG_IPE3 = service.FAMILLES_IPE["ipe_3_immobilisations"]

# Balance générale fictive : immobilisations brutes (débit) et amortissements (crédit).
BALANCE_GENERALE = [
    {"numero_compte": "245100", "solde_reel": 30_000_000.0},   # matériel de transport
    {"numero_compte": "244100", "solde_reel": 5_000_000.0},    # matériel et mobilier de bureau
    {"numero_compte": "284500", "solde_reel": -12_000_000.0},  # amortissements 245
    {"numero_compte": "284400", "solde_reel": -2_000_000.0},   # amortissements 244
    {"numero_compte": "291000", "solde_reel": -500_000.0},     # dépréciation : exclue (TODO spec)
    {"numero_compte": "401100", "solde_reel": -1_000_000.0},   # hors périmètre
]


def _bien(code, compte, brut, amort, net=None):
    bien = {"code_bien": code, "libelle_bien": f"Bien {code}", "numero_compte": compte,
            "valeur_brute": brut, "amortissements_cumules": amort}
    if net is not None:
        bien["valeur_nette"] = net
    return bien


def _registre_coherent():
    return [
        _bien("V1", "245100", 20_000_000.0, 8_000_000.0, 12_000_000.0),
        _bien("V2", "245100", 10_000_000.0, 4_000_000.0, 6_000_000.0),
        _bien("B1", "244100", 5_000_000.0, 2_000_000.0, 3_000_000.0),
    ]


def test_comparaison_par_compte_quand_chaque_bien_a_un_compte():
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, _registre_coherent())
    assert resultat["mode_comparaison"] == "par_compte"
    par_compte = {(l["numero_compte"], l["nature"]): l for l in resultat["lignes"]}
    assert par_compte[("2451", "valeur_brute")]["montant_fichier"] == 30_000_000.0
    assert par_compte[("2451", "valeur_brute")]["nb_biens"] == 2
    # Amortissements d'un bien du compte 2451 rattachés au compte 2845 (convention 28 + compte sans le 2).
    assert par_compte[("2845", "amortissements")]["solde_balance_generale"] == 12_000_000.0
    assert par_compte[("2845", "amortissements")]["montant_fichier"] == 12_000_000.0
    assert resultat["ok"] is True


def test_comparaison_par_total_sans_compte_par_bien():
    biens = [{k: v for k, v in b.items() if k != "numero_compte"} for b in _registre_coherent()]
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, biens)
    assert resultat["mode_comparaison"] == "par_total"
    lignes = {l["numero_compte"]: l for l in resultat["lignes"]}
    assert lignes["20-27"]["solde_balance_generale"] == 35_000_000.0
    assert lignes["20-27"]["montant_fichier"] == 35_000_000.0
    assert lignes["28"]["solde_balance_generale"] == 14_000_000.0
    assert lignes["28"]["montant_fichier"] == 14_000_000.0
    assert resultat["ok"] is True


def test_categorie_numerique_vaut_compte():
    biens = _registre_coherent()
    for b in biens:
        b["categorie"] = b.pop("numero_compte")
    assert service.rapprocher_immobilisations(BALANCE_GENERALE, biens)["mode_comparaison"] == "par_compte"


def test_categorie_en_lettres_force_la_comparaison_par_total():
    biens = _registre_coherent()
    for b in biens:
        del b["numero_compte"]
        b["categorie"] = "Matériel de transport"
    assert service.rapprocher_immobilisations(BALANCE_GENERALE, biens)["mode_comparaison"] == "par_total"


def test_bien_manquant_produit_un_ecart_sur_le_compte():
    biens = _registre_coherent()[:2]  # le bien B1 (244100) n'est pas dans le fichier
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, biens)
    lignes = {(l["numero_compte"], l["nature"]): l for l in resultat["lignes"]}
    assert lignes[("2441", "valeur_brute")]["ecart"] == 5_000_000.0
    assert lignes[("2441", "valeur_brute")]["ok"] is False
    assert lignes[("2844", "amortissements")]["ok"] is False
    assert resultat["ok"] is False


def test_les_depreciations_29_ne_sont_pas_comparees():
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, _registre_coherent())
    assert not any(l["numero_compte"].startswith("29") for l in resultat["lignes"])
    assert resultat["totaux"]["amortissements"]["solde_balance_generale"] == 14_000_000.0


def test_controle_valeur_nette_bien_par_bien():
    biens = _registre_coherent()
    biens[0]["valeur_nette"] = 11_000_000.0  # devrait être 20 M - 8 M = 12 M
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, biens)
    assert resultat["controle_vnc"]["applicable"] is True
    assert [e["bien"] for e in resultat["controle_vnc"]["biens_en_ecart"]] == ["V1"]
    ligne_vnc = next(l for l in resultat["lignes"] if l["nature"] == "controle_vnc")
    assert ligne_vnc["ok"] is False and ligne_vnc["ecart"] == -1_000_000.0
    assert resultat["ok"] is False


def test_controle_valeur_nette_non_applicable_sans_colonne():
    biens = [{k: v for k, v in b.items() if k != "valeur_nette"} for b in _registre_coherent()]
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, biens)
    assert resultat["controle_vnc"]["applicable"] is False
    assert not any(l["nature"] == "controle_vnc" for l in resultat["lignes"])


def test_bien_sans_compte_correspondant_dans_la_balance():
    biens = _registre_coherent() + [_bien("T1", "231000", 1_000_000.0, 0.0)]
    resultat = service.rapprocher_immobilisations(BALANCE_GENERALE, biens)
    assert resultat["biens_sans_compte_correspondant"] == ["T1"]
    assert resultat["ok"] is False


def test_aucune_mention_de_tiers_pour_ipe3():
    module = service.evaluer_module(CONFIG_IPE3, BALANCE_GENERALE, _registre_coherent(), "2026-10-13T00:00:00+00:00")
    evaluation = module["derniere_evaluation"]
    assert evaluation["nature"] == "immobilisations"
    assert "tiers_orphelins" not in evaluation
    assert all("tiers" not in cle for ligne in evaluation["detail_collectifs"] for cle in ligne)
    assert module["statut"] == "ok"


def test_ipe3_non_evaluable_sans_fichier():
    module = service.evaluer_module(CONFIG_IPE3, BALANCE_GENERALE, [], "2026-10-13T00:00:00+00:00")
    assert module["statut"] == "non_evaluable"
    assert module["derniere_evaluation"]["motif_non_evaluable"] == "fichier_complementaire_absent"
    assert module["derniere_evaluation"]["ecart_global"] is None


def test_ipe3_en_ecart_quand_un_bien_manque():
    module = service.evaluer_module(CONFIG_IPE3, BALANCE_GENERALE, _registre_coherent()[:2], "2026-10-13T00:00:00+00:00")
    assert module["statut"] == "ecart"
    assert module["derniere_evaluation"]["ecart_global"] == 5_000_000.0


def test_format_immobilisations_reconnu_et_montants_numeriques():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["REGISTRE DES IMMOBILISATIONS"])
    ws.append(["Code bien", "Désignation", "Compte", "Valeur brute", "Amortissements cumulés", "VNC"])
    ws.append(["V1", "Véhicule", "245100", 20_000_000, 8_000_000, 12_000_000])
    tampon = io.BytesIO()
    wb.save(tampon)
    tampon.seek(0)

    apercu_resultat = apercu.generer_apercu_mapping(tampon)
    assert apercu_resultat["format_propose"] == "immobilisations"
    mapping = apercu_resultat["mapping_propose"]
    assert mapping["valeur_brute"] == "Valeur brute"
    assert mapping["amortissements_cumules"] == "Amortissements cumulés"
    assert mapping["valeur_nette"] == "VNC"
    assert mapping["numero_compte"] == "Compte"

    tampon.seek(0)
    lignes = apercu.lire_lignes_selon_mapping(tampon, mapping)
    assert lignes[0]["valeur_brute"] == 20_000_000.0
    assert lignes[0]["numero_compte"] == "245100"
