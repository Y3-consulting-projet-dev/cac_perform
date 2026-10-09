"""
Fixtures partagées pour les tests de la refonte de l'import.
Voir docs/PLAN_import_refonte.md.

Le classeur construit ici est FICTIF et ANONYMISÉ (société, comptes et
montants inventés pour l'occasion) — jamais un fichier réel de client. Il
reproduit la structure réellement observée sur un fichier "balance
auxiliaire Y3" : lignes de titre/métadonnées avant l'en-tête (en-tête en
ligne 7, pas en ligne 1), et 3 lignes de total en bas de fichier sans
NUMERO_COMPTE.
"""
import io

import openpyxl
import pytest

ENTETES_Y3 = [
    "CODE_ENTITE", "NUMERO_COMPTE", "LIBELLE_COMPTE",
    "SOLDE_OUVERTURE_DEBIT", "SOLDE_OUVERTURE_CREDIT",
    "MOUVEMENT_DEBIT", "MOUVEMENT_CREDIT",
    "SOLDE_MOUVEMENT_DEBIT", "SOLDE_MOUVEMENT_CREDIT",
    "SOLDE_FINAL_DEBIT", "SOLDE_FINAL_CREDIT",
]

# (code, numero, libelle, ouv_debit, ouv_credit, mvt_debit, mvt_credit)
# Un compte au libellé contenant "TOTAL" (piège volontaire, cf. le vrai cas
# "TOTAL CI" rencontré en production) : il a un NUMERO_COMPTE valide, donc ne
# doit JAMAIS être traité comme une ligne de total.
COMPTES_FICTIFS = [
    ("FIC", "4011AAA", "Fournisseur Alpha", 0, 0, 100, 0),
    ("FIC", "4011BBB", "Fournisseur Beta", 0, 50, 0, 0),
    ("FIC", "4011TOT", "TOTAL INDUSTRIES", 0, 0, 200, 200),
    ("FIC", "6011AAA", "Charge Gamma", 0, 0, 0, 30),
    ("FIC", "4011CCC", "Fournisseur Delta", 10, 0, 0, 5),
    ("FIC", "7011AAA", "Produit Epsilon", 0, 0, 40, 0),
]


def _est_bilan(ligne):
    return ligne["numero_compte"][:1] in "12345"


def _est_gestion(ligne):
    return ligne["numero_compte"][:1] in "678"


def _construire_lignes_comptes():
    lignes = []
    for code, numero, libelle, ouv_d, ouv_c, mvt_d, mvt_c in COMPTES_FICTIFS:
        net = (ouv_d - ouv_c) + (mvt_d - mvt_c)
        fin_d = net if net >= 0 else 0
        fin_c = -net if net < 0 else 0
        lignes.append({
            "code_entite": code, "numero_compte": numero, "libelle_compte": libelle,
            "solde_ouverture_debit": ouv_d, "solde_ouverture_credit": ouv_c,
            "mouvement_debit": mvt_d, "mouvement_credit": mvt_c,
            "solde_mouvement_debit": fin_d, "solde_mouvement_credit": fin_c,
            "solde_final_debit": fin_d, "solde_final_credit": fin_c,
        })
    return lignes


def _somme(lignes, champ, filtre=None):
    return sum(l[champ] for l in lignes if (filtre is None or filtre(l)))


@pytest.fixture
def lignes_comptes_fictifs():
    """Les 6 lignes de comptes fictifs, telles que calculées (avant écriture Excel)."""
    return _construire_lignes_comptes()


@pytest.fixture
def classeur_balance_auxiliaire_fictif(lignes_comptes_fictifs):
    """
    Classeur xlsx fictif en mémoire (BytesIO), format "balance auxiliaire Y3" :
    - lignes 1-6 : titre/métadonnées (comme le vrai fichier)
    - ligne 7 : en-tête à 11 colonnes
    - lignes 8-13 : 6 comptes fictifs (dont un libellé contenant "TOTAL")
    - lignes 14-16 : 3 lignes de total SANS numéro de compte (bilan, gestion,
      grand total), avec des colonnes volontairement vides comme le vrai
      fichier (Final toujours vide ; mouvements vides sur le grand total).
    """
    lignes = lignes_comptes_fictifs
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DATA"

    ws.append(["BALANCE COMPTABLE"])
    ws.append(["Balance generale"])
    ws.append([])
    ws.append(["Entite : SOCIETE FICTIVE TEST"])
    ws.append(["Periode Du : 01/01/2025 Au : 31/12/2025"])
    ws.append([])
    ws.append(ENTETES_Y3)  # ligne 7

    for l in lignes:
        ws.append([
            l["code_entite"], l["numero_compte"], l["libelle_compte"],
            l["solde_ouverture_debit"], l["solde_ouverture_credit"],
            l["mouvement_debit"], l["mouvement_credit"],
            l["solde_mouvement_debit"], l["solde_mouvement_credit"],
            l["solde_final_debit"], l["solde_final_credit"],
        ])

    # Ligne 14 : Totaux comptes de bilan (Final laissé vide, comme le vrai fichier)
    ws.append([
        "Totaux comptes de bilan :", None, None,
        _somme(lignes, "solde_ouverture_debit", _est_bilan), _somme(lignes, "solde_ouverture_credit", _est_bilan),
        _somme(lignes, "mouvement_debit", _est_bilan), _somme(lignes, "mouvement_credit", _est_bilan),
        _somme(lignes, "solde_mouvement_debit", _est_bilan), _somme(lignes, "solde_mouvement_credit", _est_bilan),
        None, None,
    ])
    # Ligne 15 : Totaux comptes de gestion
    ws.append([
        "Totaux comptes de gestion :", None, None,
        _somme(lignes, "solde_ouverture_debit", _est_gestion), _somme(lignes, "solde_ouverture_credit", _est_gestion),
        _somme(lignes, "mouvement_debit", _est_gestion), _somme(lignes, "mouvement_credit", _est_gestion),
        _somme(lignes, "solde_mouvement_debit", _est_gestion), _somme(lignes, "solde_mouvement_credit", _est_gestion),
        None, None,
    ])
    # Ligne 16 : Totaux de la balance (grand total) ; mouvements laissés vides,
    # comme sur le vrai fichier — ne doivent jamais être contrôlés.
    ws.append([
        "Totaux de la balance :", None, None,
        _somme(lignes, "solde_ouverture_debit"), _somme(lignes, "solde_ouverture_credit"),
        None, None,
        _somme(lignes, "solde_mouvement_debit"), _somme(lignes, "solde_mouvement_credit"),
        None, None,
    ])

    tampon = io.BytesIO()
    wb.save(tampon)
    tampon.seek(0)
    return tampon


@pytest.fixture
def mapping_y3():
    """Mapping {champ_cible: nom_de_colonne} correspondant à ENTETES_Y3."""
    champs = [
        "code_entite", "numero_compte", "libelle_compte",
        "solde_ouverture_debit", "solde_ouverture_credit",
        "mouvement_debit", "mouvement_credit",
        "solde_mouvement_debit", "solde_mouvement_credit",
        "solde_final_debit", "solde_final_credit",
    ]
    return dict(zip(champs, ENTETES_Y3))
