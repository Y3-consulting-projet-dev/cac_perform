"""
Contrôles préliminaires à l'import. Nouveau périmètre V2 — voir
docs/PLAN_import_refonte.md §1d.

Implémentés (ne dépendent d'aucune spec externe) : intégrité du fichier,
colonnes requises présentes dans le mapping, doublons de numéro de compte,
cohérence stricte des dates de clôture entre fichiers.

Volontairement en stub (dépend d'une règle métier absente du dépôt) :
anomalie de sens par classe de compte. Ne pas inventer la règle — voir
TODO(spec: ...) ci-dessous, conformément à CLAUDE.md.
"""
from typing import Any, Dict, List, Optional


def controler_integrite(fichier) -> Dict[str, Any]:
    """Vérifie que le fichier est lisible, non vide, et au format .xlsx."""
    nom = getattr(fichier, "filename", None) or str(fichier)
    erreurs = []

    if not nom.lower().endswith(".xlsx"):
        erreurs.append(f"Format non supporté : '{nom}' (seul .xlsx est accepté)")

    taille = None
    try:
        fichier.seek(0, 2)  # positionne en fin de fichier
        taille = fichier.tell()
        fichier.seek(0)
    except Exception:
        pass

    if taille == 0:
        erreurs.append("Le fichier est vide")

    return {"ok": len(erreurs) == 0, "erreurs": erreurs}


def controler_colonnes_requises(mapping: Dict[str, str], champs_requis: List[str]) -> Dict[str, Any]:
    """Vérifie que chaque champ requis a bien une colonne associée dans le mapping."""
    manquants = [champ for champ in champs_requis if not mapping.get(champ)]
    return {"ok": len(manquants) == 0, "champs_manquants": manquants}


def controler_doublons(lignes: List[Dict[str, Any]], cle: str = "numero") -> Dict[str, Any]:
    """Détecte les valeurs de `cle` (numéro de compte) apparaissant plusieurs fois."""
    occurrences: Dict[Any, int] = {}
    for ligne in lignes:
        valeur = ligne.get(cle)
        if valeur is None:
            continue
        occurrences[valeur] = occurrences.get(valeur, 0) + 1

    doublons = [valeur for valeur, count in occurrences.items() if count > 1]
    return {"ok": len(doublons) == 0, "doublons": doublons}


def controler_coherence_dates(dates: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """
    Vérifie que les dates de clôture fournies pour les différents fichiers
    d'une même mission concordent. Contrôle minimal (égalité stricte) en
    attendant une règle de tolérance confirmée.

    TODO(spec: CAC-CIR-01) — tolérance exacte non confirmée (ex. même
    exercice mais dates de clôture légèrement différentes acceptées ?).
    """
    valeurs = [v for v in dates.values() if v]
    coherent = len(set(valeurs)) <= 1
    return {
        "ok": coherent,
        "dates": dates,
        "avertissement": None if coherent else "Dates de clôture différentes entre fichiers",
    }


def controler_anomalie_sens(lignes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    TODO(spec: CAC-CIR-01) — règle précise de sens attendu par classe de
    compte non confirmée dans le dépôt. Stub volontaire : ne calcule rien et
    le signale explicitement plutôt que d'inventer une règle.
    """
    return {
        "ok": None,
        "implemente": False,
        "message": "Contrôle non implémenté : règle de sens par classe de compte en attente de CAC-CIR-01.",
    }
