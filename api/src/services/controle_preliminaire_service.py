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
        # Une cellule vide ("" ou None, ex. une ligne de sous-total sans
        # numéro de compte) n'est pas un identifiant : plusieurs lignes vides
        # ne sont jamais un vrai doublon.
        if valeur is None or valeur == "":
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


def separer_lignes_sans_identifiant(lignes: List[Dict[str, Any]], cle_identifiante: Optional[str]) -> "tuple[List[Dict[str, Any]], List[Dict[str, Any]]]":
    """
    Sépare les lignes dont le champ identifiant (`cle_identifiante`, ex.
    NUMERO_COMPTE) est vide — typiquement des lignes de total/sous-total
    Excel — des lignes de données réelles.

    Ne filtre JAMAIS sur le texte du libellé : un fournisseur peut légitimement
    s'appeler « TOTAL ... » (rencontré en pratique : « TOTAL CI », compte
    4011TO, un vrai fournisseur). Seul un identifiant de compte vide est
    utilisé comme critère.

    Ne supprime rien en silence : les lignes écartées sont renvoyées avec
    leur numéro de ligne Excel (`_ligne_excel`) et leur contenu complet, pour
    traçabilité dans les contrôles préliminaires.
    """
    if not cle_identifiante:
        return lignes, []

    valides: List[Dict[str, Any]] = []
    ecartees: List[Dict[str, Any]] = []
    for ligne in lignes:
        valeur = ligne.get(cle_identifiante)
        if valeur is None or str(valeur).strip() == "":
            ecartees.append({
                "ligne_excel": ligne.get("_ligne_excel"),
                "contenu": {k: v for k, v in ligne.items() if k != "_ligne_excel"},
            })
        else:
            valides.append(ligne)
    return valides, ecartees


def _classe_compte(numero: Any) -> Optional[str]:
    """
    Classe comptable déduite du premier caractère du numéro de compte :
    « bilan » (classes 1-5) ou « gestion » (classes 6-8). Jamais basé sur un
    libellé. Renvoie None si le numéro est vide ou hors de ces classes.
    """
    if numero is None:
        return None
    premier = str(numero).strip()[:1]
    if premier in "12345":
        return "bilan"
    if premier in "678":
        return "gestion"
    return None


def controler_bouclage_total(
    lignes_valides: List[Dict[str, Any]],
    lignes_ecartees: List[Dict[str, Any]],
    cle_identifiante: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Si une ligne écartée (sans identifiant, voir separer_lignes_sans_identifiant)
    porte des montants, la compare à TROIS périmètres de lignes valides, sans
    jamais lire le libellé de la ligne de total (un sous-total "comptes de
    gestion" n'est jamais identifié par son texte, seulement par le résultat
    numérique) :
      - toutes les lignes valides ;
      - comptes de bilan (identifiant commençant par 1 à 5) ;
      - comptes de gestion (identifiant commençant par 6 à 8).
    Une colonne est comparée seulement si elle est RENSEIGNÉE (valeur
    numérique, y compris 0) sur la ligne de total — une colonne vide (None)
    n'est jamais contrôlée (ni OK, ni écart).

    Statut de la ligne de total : OK si AU MOINS UN des 3 périmètres fait
    correspondre toutes ses colonnes renseignées (périmètre indiqué) ; écart
    seulement si aucun des 3 ne correspond.
    """
    perimetres: Dict[str, List[Dict[str, Any]]] = {"toutes_les_lignes": lignes_valides}
    if cle_identifiante:
        perimetres["comptes_bilan"] = [
            l for l in lignes_valides if _classe_compte(l.get(cle_identifiante)) == "bilan"
        ]
        perimetres["comptes_gestion"] = [
            l for l in lignes_valides if _classe_compte(l.get(cle_identifiante)) == "gestion"
        ]

    resultats = []
    for candidate in lignes_ecartees:
        contenu = candidate["contenu"]
        champs_montant = {k: v for k, v in contenu.items() if isinstance(v, (int, float))}
        if not champs_montant:
            continue  # ligne écartée sans aucun montant : pas une ligne de total

        par_perimetre: Dict[str, Dict[str, Any]] = {}
        for nom_perimetre, lignes_perimetre in perimetres.items():
            comparaisons = {}
            for champ, valeur_fichier in champs_montant.items():
                somme_calculee = sum((l.get(champ) or 0) for l in lignes_perimetre)
                comparaisons[champ] = {
                    "valeur_fichier": valeur_fichier,
                    "somme_calculee": somme_calculee,
                    "ok": abs(valeur_fichier - somme_calculee) < 0.01,
                }
            par_perimetre[nom_perimetre] = {
                "ok": all(c["ok"] for c in comparaisons.values()),
                "comparaisons": comparaisons,
            }

        perimetre_correspondant = next((nom for nom, res in par_perimetre.items() if res["ok"]), None)

        resultats.append({
            "ligne_excel": candidate["ligne_excel"],
            "libelle": contenu.get("code_entite") or contenu.get("libelle_compte"),  # affichage uniquement
            "ok": perimetre_correspondant is not None,
            "perimetre_correspondant": perimetre_correspondant,
            "par_perimetre": par_perimetre,
        })

    return {
        "nb_lignes_de_total_detectees": len(resultats),
        "resultats": resultats,
    }


# Paires débit/crédit nécessaires au contrôle de bouclage ligne par ligne
# (format « balance auxiliaire Y3 » notamment).
CHAMPS_BOUCLAGE_LIGNE = [
    "solde_ouverture_debit", "solde_ouverture_credit",
    "mouvement_debit", "mouvement_credit",
    "solde_final_debit", "solde_final_credit",
]


def controler_bouclage_ligne(lignes_valides: List[Dict[str, Any]], tolerance: float = 0.0) -> Dict[str, Any]:
    """
    Contrôle arithmétique ligne par ligne :
    (ouv_D - ouv_C) + (mvt_D - mvt_C) - (final_D - final_C) = 0.

    Applicable seulement si le mapping utilisé fournit les 6 colonnes
    nécessaires (ex. format « balance auxiliaire Y3 ») ; sinon non applicable
    (ex. format à montant unique, qui n'a pas ces colonnes séparées).

    TODO(spec: CAC-IPE-01) — tolérance d'écart non confirmée ; 0 par défaut
    (aucun écart accepté).
    """
    if not lignes_valides or not all(champ in lignes_valides[0] for champ in CHAMPS_BOUCLAGE_LIGNE):
        return {"applicable": False, "tolerance": tolerance, "lignes_en_ecart": []}

    lignes_en_ecart = []
    for ligne in lignes_valides:
        ouv_d = ligne.get("solde_ouverture_debit") or 0
        ouv_c = ligne.get("solde_ouverture_credit") or 0
        mvt_d = ligne.get("mouvement_debit") or 0
        mvt_c = ligne.get("mouvement_credit") or 0
        fin_d = ligne.get("solde_final_debit") or 0
        fin_c = ligne.get("solde_final_credit") or 0

        ecart = (ouv_d - ouv_c) + (mvt_d - mvt_c) - (fin_d - fin_c)
        if abs(ecart) > tolerance:
            lignes_en_ecart.append({
                "ligne_excel": ligne.get("_ligne_excel"),
                "numero_compte": ligne.get("numero_compte") or ligne.get("numero"),
                "libelle_compte": ligne.get("libelle_compte") or ligne.get("libelle"),
                "ecart": ecart,
            })

    return {
        "applicable": True,
        "tolerance": tolerance,
        "nb_lignes_en_ecart": len(lignes_en_ecart),
        "lignes_en_ecart": lignes_en_ecart,
    }
