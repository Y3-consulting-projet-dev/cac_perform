"""
Lecture et gestion de version des fichiers complémentaires d'une mission
(balances auxiliaires clients/fournisseurs, immobilisations).
Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md.

Ce module ne calcule AUCUN rapprochement avec la balance générale (comptes
411, 40x, 2xxx) : c'est le verrou IPE (Module 1, lot suivant), explicitement
hors périmètre ici (CLAUDE.md).

Versionnement : un remplacement ne supprime rien. La version précédente est
marquée `actif=False` (archivée) plutôt que supprimée ; `lister_*` ne renvoie
que la version active, `lister_historique` renvoie tout.
"""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database

TYPES_FICHIERS_COMPLEMENTAIRES = ["auxiliaire_client", "auxiliaire_fournisseur", "immobilisations"]


def _collection():
    return get_database()["Balance"]


def prochaine_version(mission_id: str, type_fichier: str) -> int:
    """Numéro de version suivant pour (mission_id, type_fichier)."""
    dernier = _collection().find_one(
        {"mission_id": mission_id, "type": type_fichier},
        sort=[("version", -1)],
    )
    return (dernier.get("version", 0) + 1) if dernier else 1


def archiver_version_active(mission_id: str, type_fichier: str) -> None:
    """
    Marque comme inactive toute version actuellement active pour
    (mission_id, type_fichier). Ne supprime rien : l'historique reste
    consultable via `lister_historique`.
    """
    _collection().update_many(
        {"mission_id": mission_id, "type": type_fichier, "actif": True},
        {"$set": {"actif": False}},
    )


def lister_fichiers_complementaires(mission_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Liste les fichiers complémentaires ACTIFS d'une mission, regroupés par
    type. Filtre strictement par `mission_id` (base du cloisonnement) : un
    fichier d'une autre mission n'est jamais renvoyé.
    """
    resultat: Dict[str, List[Dict[str, Any]]] = {t: [] for t in TYPES_FICHIERS_COMPLEMENTAIRES}

    documents = _collection().find({
        "mission_id": mission_id,
        "type": {"$in": TYPES_FICHIERS_COMPLEMENTAIRES},
        "actif": True,
    })

    for doc in documents:
        type_fichier = doc.get("type")
        resultat.setdefault(type_fichier, []).append(_resume(doc))

    return resultat


def lister_historique(mission_id: str, type_fichier: str) -> List[Dict[str, Any]]:
    """Historique complet (actif + archivé) pour (mission_id, type_fichier), le plus récent d'abord."""
    documents = _collection().find(
        {"mission_id": mission_id, "type": type_fichier}
    ).sort("version", -1)
    return [_resume(doc) for doc in documents]


def _resume(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_id": str(doc["_id"]),
        "type": doc.get("type"),
        "nom_fichier": doc.get("nom_fichier"),
        "date_import": doc.get("date_import"),
        "version": doc.get("version", 1),
        "actif": doc.get("actif", True),
        "nb_lignes": len(doc.get("balance", []) or []),
    }


# Paires débit/crédit reconnues (format "balance auxiliaire Y3") : quand un
# fichier les fournit telles quelles, elles sont utilisées directement, sans
# aucune convention de signe à deviner.
PAIRES_DEBIT_CREDIT = [
    ("solde_ouverture_debit", "solde_ouverture_credit", "ouverture"),
    ("mouvement_debit", "mouvement_credit", "mouvements"),
    ("solde_mouvement_debit", "solde_mouvement_credit", "solde_mouvement"),
    ("solde_final_debit", "solde_final_credit", "solde_final"),
]


def _calculer_totaux(lignes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Totaux débit/crédit par paire (ouverture, mouvements, solde mouvement,
    solde final) quand le fichier fournit des colonnes débit/crédit séparées
    (ex. format "balance auxiliaire Y3").

    Repli (mode "montant_signe") uniquement pour les fichiers à montant
    unique, qui n'ont pas de colonnes débit/crédit séparées : positif =
    débit, négatif = crédit. TODO(spec: CAC-IPE-01) — convention à confirmer
    pour ce cas de repli ; ne s'applique jamais quand des colonnes débit/
    crédit distinctes existent.
    """
    if not lignes:
        return {"mode": "vide", "totaux": {}}

    premiere_ligne = lignes[0]

    # Fichier des immobilisations : des biens, pas de débit/crédit — sommes
    # des valeurs brutes, amortissements cumulés et valeurs nettes.
    if "valeur_brute" in premiere_ligne:
        return {
            "mode": "immobilisations",
            "totaux": {},
            "sommes": {
                champ: sum((l.get(champ) or 0) for l in lignes)
                for champ in ("valeur_brute", "amortissements_cumules", "valeur_nette")
                if champ in premiere_ligne
            },
        }
    paires_presentes = [
        (champ_debit, champ_credit, libelle)
        for champ_debit, champ_credit, libelle in PAIRES_DEBIT_CREDIT
        if champ_debit in premiere_ligne and champ_credit in premiere_ligne
    ]

    if paires_presentes:
        totaux = {}
        for champ_debit, champ_credit, libelle in paires_presentes:
            totaux[libelle] = {
                "debit": sum((l.get(champ_debit) or 0) for l in lignes),
                "credit": sum((l.get(champ_credit) or 0) for l in lignes),
            }
        return {"mode": "paires_debit_credit", "totaux": totaux}

    total_debit = sum(l.get("montant", 0) for l in lignes if (l.get("montant") or 0) >= 0)
    total_credit = sum(-(l.get("montant") or 0) for l in lignes if (l.get("montant") or 0) < 0)
    return {"mode": "montant_signe", "totaux": {"global": {"debit": total_debit, "credit": total_credit}}}


def lire_detail_fichier(mission_id: str, fichier_id: str) -> Optional[Dict[str, Any]]:
    """
    Détail d'un fichier complémentaire : lignes, mapping utilisé, totaux,
    date d'import, contrôles préliminaires.

    Cloisonnement : si le fichier n'appartient pas à `mission_id`, renvoie
    None (comme s'il n'existait pas) — ne jamais révéler l'existence d'un
    fichier d'une autre mission.
    """
    try:
        object_id = ObjectId(fichier_id)
    except InvalidId:
        return None

    doc = _collection().find_one({"_id": object_id})
    if not doc or doc.get("mission_id") != mission_id:
        return None
    if doc.get("type") not in TYPES_FICHIERS_COMPLEMENTAIRES:
        return None

    lignes = doc.get("balance", []) or []

    return {
        "_id": str(doc["_id"]),
        "type": doc.get("type"),
        "nom_fichier": doc.get("nom_fichier"),
        "date_import": doc.get("date_import"),
        "version": doc.get("version", 1),
        "actif": doc.get("actif", True),
        "mapping_utilise": doc.get("mapping_utilise"),
        "controles_preliminaires": doc.get("controles_preliminaires"),
        "lignes": lignes,
        "totaux": _calculer_totaux(lignes),
    }
