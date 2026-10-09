"""
Tests de controle_preliminaire_service.py :
- separer_lignes_sans_identifiant (jamais sur le texte du libellé) ;
- controler_bouclage_total (comparaison à 3 périmètres) ;
- controler_bouclage_ligne (ouv + mvt - final = 0).

Voir docs/PLAN_import_refonte.md. Le classeur fictif vient de tests/conftest.py.
"""
from src.services import mapping_apercu_service as apercu_service
from src.services import controle_preliminaire_service as cp_service


def _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3):
    return apercu_service.lire_lignes_selon_mapping(classeur_balance_auxiliaire_fictif, mapping_y3)


# ---------------------------------------------------------------------------
# separer_lignes_sans_identifiant
# ---------------------------------------------------------------------------

def test_separe_les_3_lignes_de_total_sans_numero(classeur_balance_auxiliaire_fictif, mapping_y3):
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)

    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    assert len(valides) == 6
    assert len(ecartees) == 3
    assert {e["ligne_excel"] for e in ecartees} == {14, 15, 16}


def test_ne_filtre_jamais_sur_le_libelle_total(classeur_balance_auxiliaire_fictif, mapping_y3):
    """Le compte "TOTAL INDUSTRIES" (numéro 4011TOT) doit rester parmi les lignes VALIDES."""
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)

    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    numeros_valides = {l["numero_compte"] for l in valides}
    assert "4011TOT" in numeros_valides
    assert all(e["contenu"].get("libelle_compte", "") != "" or True for e in ecartees)  # pas de crash sur contenu


def test_sans_cle_identifiante_ne_separe_rien(classeur_balance_auxiliaire_fictif, mapping_y3):
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)

    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, None)

    assert valides == lignes
    assert ecartees == []


# ---------------------------------------------------------------------------
# controler_bouclage_total — comparaison à 3 périmètres
# ---------------------------------------------------------------------------

def test_bouclage_total_les_3_lignes_sont_ok(classeur_balance_auxiliaire_fictif, mapping_y3):
    """
    Reproduit le cas réel corrigé : les 3 lignes de total doivent toutes être
    OK, chacune sur le périmètre qui lui correspond réellement (jamais deviné
    depuis son libellé).
    """
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)
    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    resultat = cp_service.controler_bouclage_total(valides, ecartees, "numero_compte")

    assert resultat["nb_lignes_de_total_detectees"] == 3
    par_ligne = {r["ligne_excel"]: r for r in resultat["resultats"]}

    assert par_ligne[14]["ok"] is True
    assert par_ligne[14]["perimetre_correspondant"] == "comptes_bilan"

    assert par_ligne[15]["ok"] is True
    assert par_ligne[15]["perimetre_correspondant"] == "comptes_gestion"

    assert par_ligne[16]["ok"] is True
    assert par_ligne[16]["perimetre_correspondant"] == "toutes_les_lignes"


def test_bouclage_total_colonne_vide_non_controlee(classeur_balance_auxiliaire_fictif, mapping_y3):
    """
    La ligne "Totaux de la balance" (16) n'a pas de MOUVEMENT_DEBIT/CREDIT :
    ces colonnes ne doivent apparaître dans AUCUNE comparaison (ni OK, ni
    écart), pas être traitées comme valant 0.
    """
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)
    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    resultat = cp_service.controler_bouclage_total(valides, ecartees, "numero_compte")
    ligne_16 = next(r for r in resultat["resultats"] if r["ligne_excel"] == 16)

    for perimetre in ligne_16["par_perimetre"].values():
        assert "mouvement_debit" not in perimetre["comparaisons"]
        assert "mouvement_credit" not in perimetre["comparaisons"]


def test_bouclage_total_ecart_si_aucun_perimetre_ne_correspond(classeur_balance_auxiliaire_fictif, mapping_y3):
    """Une ligne de total avec un montant erroné ne doit correspondre à AUCUN des 3 périmètres."""
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)
    valides, ecartees = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    ecartees_corrompues = [dict(e) for e in ecartees]
    ligne_bilan = next(e for e in ecartees_corrompues if e["ligne_excel"] == 14)
    ligne_bilan["contenu"] = dict(ligne_bilan["contenu"])
    ligne_bilan["contenu"]["mouvement_debit"] = 999999.0  # valeur fausse

    resultat = cp_service.controler_bouclage_total(valides, ecartees_corrompues, "numero_compte")
    ligne_14 = next(r for r in resultat["resultats"] if r["ligne_excel"] == 14)

    assert ligne_14["ok"] is False
    assert ligne_14["perimetre_correspondant"] is None


# ---------------------------------------------------------------------------
# controler_bouclage_ligne
# ---------------------------------------------------------------------------

def test_bouclage_ligne_aucun_ecart_sur_donnees_coherentes(classeur_balance_auxiliaire_fictif, mapping_y3):
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)
    valides, _ = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    resultat = cp_service.controler_bouclage_ligne(valides)

    assert resultat["applicable"] is True
    assert resultat["tolerance"] == 0.0
    assert resultat["nb_lignes_en_ecart"] == 0


def test_bouclage_ligne_detecte_un_ecart_introduit(classeur_balance_auxiliaire_fictif, mapping_y3):
    lignes = _lignes_du_classeur_fictif(classeur_balance_auxiliaire_fictif, mapping_y3)
    valides, _ = cp_service.separer_lignes_sans_identifiant(lignes, "numero_compte")

    valides_corrompues = [dict(l) for l in valides]
    valides_corrompues[0]["solde_final_debit"] = (valides_corrompues[0]["solde_final_debit"] or 0) + 1

    resultat = cp_service.controler_bouclage_ligne(valides_corrompues)

    assert resultat["nb_lignes_en_ecart"] == 1
    assert resultat["lignes_en_ecart"][0]["numero_compte"] == valides_corrompues[0]["numero_compte"]


def test_bouclage_ligne_non_applicable_sans_les_6_colonnes():
    lignes_format_simple = [{"numero": "1", "libelle": "x", "montant": 10.0}]

    resultat = cp_service.controler_bouclage_ligne(lignes_format_simple)

    assert resultat["applicable"] is False
    assert resultat["lignes_en_ecart"] == []
