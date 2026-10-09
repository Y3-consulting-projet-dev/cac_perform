"""
Tests de mapping_apercu_service.py — détection de la ligne d'en-tête et
lecture pilotée par mapping. Voir docs/PLAN_import_refonte.md.
"""
from src.services import mapping_apercu_service as apercu_service


def test_trouve_la_ligne_entete_apres_les_titres(classeur_balance_auxiliaire_fictif):
    """
    L'en-tête réel est en ligne 7 (lignes 1-6 = titre/métadonnées), comme sur
    le fichier réel qui a révélé ce besoin. _trouver_ligne_entete ne doit pas
    se contenter de la ligne 1.
    """
    import openpyxl
    wb = openpyxl.load_workbook(classeur_balance_auxiliaire_fictif, data_only=True)
    sheet = wb["DATA"]

    ligne_entete = apercu_service._trouver_ligne_entete(sheet)

    assert ligne_entete == 7


def test_apercu_reconnait_le_format_y3_par_les_noms_den_tete(classeur_balance_auxiliaire_fictif):
    resultat = apercu_service.generer_apercu_mapping(classeur_balance_auxiliaire_fictif)

    assert resultat["ligne_entete"] == 7
    assert resultat["format_propose"] == "balance_auxiliaire_detaillee"
    assert resultat["mapping_propose"]["numero_compte"] == "NUMERO_COMPTE"
    assert resultat["mapping_propose"]["libelle_compte"] == "LIBELLE_COMPTE"
    assert resultat["mapping_propose"]["solde_final_debit"] == "SOLDE_FINAL_DEBIT"


def test_lecture_selon_mapping_renvoie_toutes_les_lignes_avec_numero_excel(
    classeur_balance_auxiliaire_fictif, mapping_y3
):
    """
    lire_lignes_selon_mapping ne filtre QUE les lignes entièrement vides : les
    3 lignes de total (sans numéro de compte mais avec du contenu) sont
    encore présentes ici — leur exclusion est la responsabilité de
    separer_lignes_sans_identifiant (controle_preliminaire_service), pas de
    cette fonction de lecture générique.
    """
    lignes = apercu_service.lire_lignes_selon_mapping(classeur_balance_auxiliaire_fictif, mapping_y3)

    # 6 comptes + 3 lignes de total = 9
    assert len(lignes) == 9
    assert all("_ligne_excel" in l for l in lignes)
    # Les lignes sont dans l'ordre du fichier, à partir de la ligne 8 (juste après l'en-tête ligne 7)
    assert [l["_ligne_excel"] for l in lignes] == list(range(8, 17))


def test_cellule_vraiment_vide_reste_none_pas_zero(classeur_balance_auxiliaire_fictif, mapping_y3):
    """
    Sur la ligne de total "Totaux de la balance" (grand total), les colonnes
    MOUVEMENT_DEBIT/CREDIT sont laissées vides dans le classeur fictif (comme
    sur le vrai fichier). Elles doivent rester `None`, jamais devenir 0.0 —
    sinon le contrôle de bouclage ne peut pas distinguer "vide, non contrôlé"
    de "zéro saisi".
    """
    lignes = apercu_service.lire_lignes_selon_mapping(classeur_balance_auxiliaire_fictif, mapping_y3)

    ligne_grand_total = next(l for l in lignes if l.get("code_entite") == "Totaux de la balance :")

    assert ligne_grand_total["mouvement_debit"] is None
    assert ligne_grand_total["mouvement_credit"] is None
    # Les colonnes réellement renseignées sur cette ligne restent des nombres
    assert isinstance(ligne_grand_total["solde_ouverture_debit"], float)


def test_compte_avec_libelle_total_garde_son_numero(classeur_balance_auxiliaire_fictif, mapping_y3):
    """Piège volontaire : "TOTAL INDUSTRIES" (numéro 4011TOT) est un vrai compte, pas une ligne de total."""
    lignes = apercu_service.lire_lignes_selon_mapping(classeur_balance_auxiliaire_fictif, mapping_y3)

    ligne_total_industries = next(l for l in lignes if l.get("numero_compte") == "4011TOT")

    assert ligne_total_industries["libelle_compte"] == "TOTAL INDUSTRIES"
