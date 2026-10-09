"""
Service d'aperçu et de lecture par mapping de colonnes.
Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md §1a et §3.

Ne modifie ni n'importe api/src/model.py (CLAUDE.md : le parsing historique
reste isolé). Utilisé par la balance générale (aperçu + mapping mémorisé,
sans remplacer le parsing historique de Mission.creation_balance()) ET,
depuis ce correctif, par les balances auxiliaires et le fichier des
immobilisations, qui passent désormais par le MÊME mécanisme au lieu d'un
parsing fixe à 3 colonnes.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import openpyxl

NOMS_FEUILLES_CONNUES = [
    "Balance des comptes", "Balance_des_comptes", "BALANCE_2023", "BALANCE_2024",
    "Sage", "Sheet1", "Feuil1", "Balance", "Comptes",
]

# Formats connus (balance générale) : nombre de colonnes -> (nom du format,
# champs cibles dans l'ordre). Même inventaire que Mission.creation_balance()
# (api/src/model.py), reconstruit indépendamment pour ne pas coupler ce
# service au fichier historique.
FORMATS_CONNUS: Dict[int, Tuple[str, List[str]]] = {
    8: ("standard", [
        "numero", "libelle",
        "debit_initial", "credit_initial",
        "debit_mvt", "credit_mvt",
        "debit_fin", "credit_fin",
    ]),
    6: ("balance_simple", [
        "numero", "libelle",
        "debit_initial", "credit_initial",
        "debit_fin", "credit_fin",
    ]),
    3: ("simple", ["numero", "libelle", "montant"]),
}
# Remarque : le format "sage" (6 colonnes) partage son nombre de colonnes avec
# "balance_simple" ; model.py les distingue via une heuristique plus fine sur
# le contenu des en-têtes, non reproduite ici.
# TODO(spec: confirmer si l'aperçu V2 doit distinguer sage/balance_simple
# automatiquement, ou si la correction manuelle par l'utilisateur suffit).

# Format "balance auxiliaire Y3" : reconnu PAR LE NOM des en-têtes (pas
# seulement par leur nombre), donc toujours détecté même si les colonnes sont
# dans un autre ordre ou entourées de colonnes supplémentaires. CODE_ENTITE et
# NUMERO_COMPTE sont conservés tels quels dans les données stockées (aucune
# décision prise ici sur ce qui identifie le tiers, voir TODO(spec) dans
# balance_auxiliaire_service.py).
CHAMPS_BALANCE_AUXILIAIRE_Y3 = [
    "code_entite", "numero_compte", "libelle_compte",
    "solde_ouverture_debit", "solde_ouverture_credit",
    "mouvement_debit", "mouvement_credit",
    "solde_mouvement_debit", "solde_mouvement_credit",
    "solde_final_debit", "solde_final_credit",
]

PAIRES_DEBIT_CREDIT = [
    ("solde_ouverture_debit", "solde_ouverture_credit"),
    ("mouvement_debit", "mouvement_credit"),
    ("solde_mouvement_debit", "solde_mouvement_credit"),
    ("solde_final_debit", "solde_final_credit"),
]

# Champs lus comme nombre (le reste est conservé tel quel, en texte).
CHAMPS_NUMERIQUES = {
    "debit_initial", "credit_initial", "debit_mvt", "credit_mvt", "debit_fin", "credit_fin",
    "montant",
    "solde_ouverture_debit", "solde_ouverture_credit",
    "mouvement_debit", "mouvement_credit",
    "solde_mouvement_debit", "solde_mouvement_credit",
    "solde_final_debit", "solde_final_credit",
}


def _normaliser_entete(texte: Any) -> str:
    """MAJUSCULES, sans accents, espaces/tirets -> underscore (ex. 'Code entité' -> 'CODE_ENTITE')."""
    texte = str(texte or "").strip().upper()
    texte = "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))
    texte = re.sub(r"[\s\-]+", "_", texte)
    return texte


def _choisir_feuille(workbook):
    for nom in NOMS_FEUILLES_CONNUES:
        if nom in workbook.sheetnames:
            return workbook[nom]
    return workbook[workbook.sheetnames[0]]


def _trouver_ligne_entete(sheet, max_lignes_scan: int = 20) -> int:
    """
    Trouve le numéro de la ligne d'en-tête réelle. Un fichier réel commence
    souvent par plusieurs lignes de titre/métadonnées avant l'en-tête (ex.
    « BALANCE COMPTABLE », « Entité : ... », « Période du ... »), qui n'ont
    presque toujours qu'une seule cellule remplie — contrairement à une ligne
    d'en-tête, qui en a plusieurs. Première ligne à ≥ 2 cellules non vides.
    """
    for index, row in enumerate(
        sheet.iter_rows(min_row=1, max_row=max_lignes_scan, values_only=True), start=1
    ):
        valeurs_non_vides = [v for v in row if v is not None and str(v).strip()]
        if len(valeurs_non_vides) >= 2:
            return index
    return 1


def _lire_entete(sheet) -> Tuple[int, List[str]]:
    """Renvoie (numéro de la ligne d'en-tête, colonnes détectées)."""
    ligne_entete = _trouver_ligne_entete(sheet)

    brute = list(next(
        sheet.iter_rows(min_row=ligne_entete, max_row=ligne_entete, values_only=True), ()
    ))
    # Les fichiers réels ont souvent des colonnes vides en fin de ligne
    # (mise en forme résiduelle) : on ne les compte pas comme des colonnes
    # de données, sinon le nombre de colonnes ne correspond plus à aucun
    # format connu.
    while brute and brute[-1] is None:
        brute.pop()

    colonnes = [
        str(c).strip() if c is not None else f"Colonne {i + 1}"
        for i, c in enumerate(brute)
    ]
    return ligne_entete, colonnes


def _detecter_format_balance_auxiliaire_y3(colonnes_detectees: List[str]) -> Optional[Dict[str, str]]:
    """
    Reconnaît le format « balance auxiliaire Y3 » par le NOM des en-têtes.
    Renvoie le mapping {champ_cible: colonne_source} si au moins
    l'identification du compte (NUMERO_COMPTE + LIBELLE_COMPTE) et une paire
    débit/crédit complète sont retrouvées, sinon None.
    """
    par_entete_normalisee = {_normaliser_entete(c): c for c in colonnes_detectees}

    mapping: Dict[str, str] = {}
    for champ in CHAMPS_BALANCE_AUXILIAIRE_Y3:
        cle = _normaliser_entete(champ)
        if cle in par_entete_normalisee:
            mapping[champ] = par_entete_normalisee[cle]

    a_identification = "numero_compte" in mapping and "libelle_compte" in mapping
    a_une_paire = any(
        champ_debit in mapping and champ_credit in mapping
        for champ_debit, champ_credit in PAIRES_DEBIT_CREDIT
    )

    return mapping if (a_identification and a_une_paire) else None


def generer_apercu_mapping(fichier) -> Dict[str, Any]:
    """
    Lit un fichier Excel et propose un mapping de colonnes par défaut.
    Ne modifie rien en base. `fichier` : objet compatible
    openpyxl.load_workbook (ex. werkzeug FileStorage).

    Priorité de détection : d'abord le format « balance auxiliaire Y3 » par
    nom d'en-tête (fonctionne quel que soit le nombre de colonnes réel du
    fichier), puis les formats connus de la balance générale par nombre de
    colonnes.
    """
    workbook = openpyxl.load_workbook(fichier, data_only=True)
    sheet = _choisir_feuille(workbook)

    ligne_entete, colonnes_detectees = _lire_entete(sheet)
    nb_lignes_detectees = max(sheet.max_row - ligne_entete, 0)

    mapping_y3 = _detecter_format_balance_auxiliaire_y3(colonnes_detectees)
    if mapping_y3:
        return {
            "colonnes_detectees": colonnes_detectees,
            "feuille": sheet.title,
            "ligne_entete": ligne_entete,
            "format_propose": "balance_auxiliaire_detaillee",
            "mapping_propose": mapping_y3,
            "nb_lignes_detectees": nb_lignes_detectees,
        }

    nb_colonnes = len(colonnes_detectees)
    format_connu: Optional[Tuple[str, List[str]]] = FORMATS_CONNUS.get(nb_colonnes)
    if format_connu:
        format_propose, champs = format_connu
    else:
        format_propose, champs = "inconnu", []

    mapping_propose: Dict[str, str] = {}
    for index, champ in enumerate(champs):
        if index < len(colonnes_detectees):
            mapping_propose[champ] = colonnes_detectees[index]

    return {
        "colonnes_detectees": colonnes_detectees,
        "feuille": sheet.title,
        "ligne_entete": ligne_entete,
        "format_propose": format_propose,
        "mapping_propose": mapping_propose,
        "nb_lignes_detectees": nb_lignes_detectees,
    }


def lire_lignes_selon_mapping(fichier, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Lit toutes les lignes de données d'un fichier Excel selon un mapping
    {champ_cible: nom_de_colonne_source} déjà résolu (proposé automatiquement,
    mémorisé, ou corrigé manuellement). Les colonnes absentes du mapping sont
    ignorées. Les champs numériques connus (CHAMPS_NUMERIQUES) sont convertis
    en nombre (une cellule vraiment vide reste `None`, distinct d'un 0 saisi
    — nécessaire pour le contrôle de bouclage, voir controle_preliminaire_service.py) ;
    les autres (ex. NUMERO_COMPTE, LIBELLE_COMPTE) restent du texte brut,
    inchangés.

    Chaque ligne porte aussi `_ligne_excel` (numéro de ligne réel dans le
    fichier), pour la traçabilité des lignes écartées en aval. Ce champ
    technique n'est pas une donnée métier : à retirer avant stockage final
    (voir balance_auxiliaire_service.py / immobilisation_service.py).

    Retrouve la ligne d'en-tête réelle (voir _trouver_ligne_entete) : les
    lignes de titre/métadonnées avant l'en-tête ne sont jamais lues comme des
    données.
    """
    workbook = openpyxl.load_workbook(fichier, data_only=True)
    sheet = _choisir_feuille(workbook)

    ligne_entete = _trouver_ligne_entete(sheet)
    entete = [str(c).strip() if c is not None else None for c in
              next(sheet.iter_rows(min_row=ligne_entete, max_row=ligne_entete, values_only=True), ())]

    index_par_champ: Dict[str, int] = {}
    for champ, nom_colonne in mapping.items():
        if nom_colonne in entete:
            index_par_champ[champ] = entete.index(nom_colonne)

    lignes: List[Dict[str, Any]] = []
    for decalage, row in enumerate(sheet.iter_rows(min_row=ligne_entete + 1, values_only=True)):
        numero_ligne_excel = ligne_entete + 1 + decalage
        if row is None or all(v is None for v in row):
            continue

        ligne: Dict[str, Any] = {}
        for champ, index in index_par_champ.items():
            valeur = row[index] if index < len(row) else None
            if champ in CHAMPS_NUMERIQUES:
                if valeur is None:
                    ligne[champ] = None
                elif isinstance(valeur, (int, float)):
                    ligne[champ] = float(valeur)
                else:
                    ligne[champ] = 0.0
            else:
                ligne[champ] = str(valeur).strip() if valeur is not None else ""

        if ligne:
            ligne["_ligne_excel"] = numero_ligne_excel
            lignes.append(ligne)

    return lignes
