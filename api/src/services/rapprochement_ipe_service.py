"""
Rapprochements IPE-1/2/3 (clients↔411, fournisseurs↔40x, immobilisations↔2xxx)
et validation manager de la fiabilité IPE. Nouveau périmètre V2 — voir
docs/PLAN_verrou_IPE.md §4 et §5.

IPE-1 et IPE-2 (tiers) : la balance générale ne contient QUE des comptes
collectifs (ex. une ligne "411", ou plusieurs collectifs plus fins
"401"/"402"/"403"), jamais le détail par tiers. Le rapprochement se fait
donc collectif par collectif : solde du collectif (balance générale) comparé
à la somme des tiers de l'auxiliaire qui s'y rattachent — jamais une simple
somme globale balance-générale-contre-tout-l'auxiliaire.

IPE-3 (immobilisations) : le fichier liste des BIENS, pas des tiers —
valeurs brutes contre comptes 20 à 27, amortissements cumulés contre
comptes 28, par compte ou par total, et contrôle de la valeur nette bien par
bien (voir rapprocher_immobilisations).

Lecture de la balance générale : les documents Balance de la V1
(Mission.creation_balance(), api/src/model.py) n'ont ni mission_id ni type —
ils sont retrouvés via Mission1.balances (liste de 2 _id). La sélection ne se
fait JAMAIS par position (balances[0] n'est pas garanti être l'exercice N) :
on sélectionne le document dont `annee_balance` correspond à
`Mission1.annee_auditee` (exercice audité, N — jamais N-1). Introuvable ou
ambigu (plusieurs candidats) -> échec explicite (ValueError), aucune
évaluation n'est enregistrée dans ce cas. Champ fiable quel que soit le
format détecté : numero_compte + solde_reel (= debit_fin - credit_fin), voir
model.py.

TODO(spec: CAC-IPE-01 §2) — explicitement non inventés ici, voir le détail
dans chaque fonction : rattachement tiers↔collectif par préfixe le plus long
(hypothèse de travail), tolérance d'écart (0 par défaut), convention de signe
harmonisée entre balance générale et auxiliaire, traitement des orphelins,
conditions de passage à TRUE de ipe_fiabilite_validee. Pour IPE-3 :
TODO(spec: CAC-IPE-01 §3) — granularité de la comparaison, tolérance,
prise en compte des dépréciations (29).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services import balance_auxiliaire_service
from src.services import fichiers_complementaires_service as fc_service
from src.services import revue_ipe_service
from src.services import verrou_ipe_service

COLLECTION_MISSION = "Mission1"
COLLECTION_BALANCE = "Balance"

# Famille IPE -> type de fichier complémentaire correspondant dans la
# collection Balance, et nature du rapprochement. Voir CLAUDE.md pour IPE-1/2/3.
# - "tiers" (IPE-1, IPE-2) : compte collectif par compte collectif, tiers de
#   l'auxiliaire rattachés par préfixe (rapprocher_famille) ;
# - "immobilisations" (IPE-3) : un fichier de BIENS, sans tiers — valeurs
#   brutes contre comptes 20 à 27, amortissements cumulés contre comptes 28
#   (rapprocher_immobilisations).
# Racines des comptes collectifs rapprochés des balances auxiliaires — SEUL
# endroit où elles sont définies. Valeurs provisoires = paramètre par défaut
# du cahier des charges §2.4 (« 41 » clients, « 40 » fournisseurs) : une
# racine « 411 » seule ne trouvait pas le collectif clients d'un plan de
# comptes en 410000.
# TODO(spec: CAC-IPE-01 §2) : racines définitives, et exclusion éventuelle
# de sous-comptes (ex. 416 clients douteux, 419 avances reçues, 409).
RACINES_COLLECTIFS = {
    "clients": "41",
    "fournisseurs": "40",
}

FAMILLES_IPE: Dict[str, Dict[str, str]] = {
    "ipe_1_clients": {"nature": "tiers", "racine_collectif": RACINES_COLLECTIFS["clients"], "type_auxiliaire": "auxiliaire_client"},
    "ipe_2_fournisseurs": {"nature": "tiers", "racine_collectif": RACINES_COLLECTIFS["fournisseurs"], "type_auxiliaire": "auxiliaire_fournisseur"},
    "ipe_3_immobilisations": {"nature": "immobilisations", "type_auxiliaire": "immobilisations"},
}

# IPE-3 : comptes de la balance générale comparés au fichier des
# immobilisations. Les dépréciations (29) ne sont PAS prises en compte —
# TODO(spec: CAC-IPE-01 §3) : granularité de la comparaison, tolérance,
# prise en compte des dépréciations (29).
RACINES_IMMOBILISATIONS_BRUTES = ("20", "21", "22", "23", "24", "25", "26", "27")
RACINE_AMORTISSEMENTS = "28"

# Écart toléré entre la balance générale et le fichier complémentaire, en
# FCFA : aucun (tout écart non nul est un écart). Décision provisoire —
# TODO(spec: CAC-IPE-01 §2) : tolérance d'écart (seuil absolu et/ou en %).
TOLERANCE_ECART_IPE = 0.0


def _solde_ligne_balance_generale(ligne: Dict[str, Any]) -> Optional[float]:
    """solde_reel est fiable quel que soit le format détecté par model.py (= debit_fin - credit_fin)."""
    if "solde_reel" in ligne and ligne["solde_reel"] is not None:
        return ligne["solde_reel"]
    debit_fin, credit_fin = ligne.get("debit_fin"), ligne.get("credit_fin")
    if debit_fin is not None and credit_fin is not None:
        return (debit_fin or 0) - (credit_fin or 0)
    return None


def _solde_ligne_auxiliaire(ligne: Dict[str, Any]) -> Optional[float]:
    """
    Même logique de repli que fichiers_complementaires_service._calculer_totaux,
    mais ligne par ligne : paire solde_final_debit/credit si fournie, sinon
    montant signé. TODO(spec: CAC-IPE-01) — convention de signe du repli
    "montant unique" non confirmée.
    """
    if "solde_final_debit" in ligne and "solde_final_credit" in ligne:
        return (ligne.get("solde_final_debit") or 0) - (ligne.get("solde_final_credit") or 0)
    if "montant" in ligne:
        return ligne.get("montant") or 0
    return None


def _cle_identifiante(lignes: List[Dict[str, Any]]) -> Optional[str]:
    if not lignes:
        return None
    for cle in balance_auxiliaire_service.CLES_IDENTIFIANTES_POSSIBLES:
        if cle in lignes[0]:
            return cle
    return None


def normaliser_compte_collectif(numero: str) -> str:
    """
    Retire les zéros de fin d'un numéro de compte COLLECTIF de la balance
    générale (observé en pratique : comptes complétés à 8 chiffres par des
    zéros, ex. "40110000" / "41110000") avant le rattachement des tiers —
    sans quoi aucun tiers de l'auxiliaire (ex. "4011TO", jamais complété de
    la même façon) ne peut matcher par préfixe. Hypothèse de travail,
    TODO(spec: CAC-IPE-01 §2) : ne s'applique qu'aux comptes collectifs de la
    balance générale, jamais aux numéros de tiers de l'auxiliaire.
    """
    numero = numero.strip()
    normalise = numero.rstrip("0")
    return normalise or numero  # jamais une chaîne vide (cas limite "00000000")


def rapprocher_famille(
    lignes_balance_generale: List[Dict[str, Any]],
    lignes_auxiliaire: List[Dict[str, Any]],
    racine_collectif: str,
    cle_identifiante: Optional[str],
    tolerance: float = TOLERANCE_ECART_IPE,
) -> Dict[str, Any]:
    """
    Rapprochement compte collectif par compte collectif (voir docstring du
    module). Les comptes collectifs de la balance générale sont normalisés
    (zéros de fin retirés, normaliser_compte_collectif) avant tout
    regroupement/rattachement. Rattachement d'un tiers à un collectif
    normalisé : préfixe le plus long qui correspond — hypothèse de travail,
    TODO(spec: CAC-IPE-01 §2).
    """
    lignes_bg_famille = [
        l for l in lignes_balance_generale
        if str(l.get("numero_compte") or "").strip().startswith(racine_collectif)
    ]

    collectifs = sorted(
        {normaliser_compte_collectif(str(l.get("numero_compte") or "").strip()) for l in lignes_bg_famille},
        key=len,
        reverse=True,
    )

    def _collectif_du_tiers(numero_tiers: str) -> Optional[str]:
        for collectif in collectifs:
            if numero_tiers.startswith(collectif):
                return collectif
        return None

    tiers_par_collectif: Dict[str, List[Dict[str, Any]]] = {c: [] for c in collectifs}
    orphelins_auxiliaire: List[Dict[str, Any]] = []
    lignes_non_calculables: List[Dict[str, Any]] = []

    for ligne in lignes_auxiliaire:
        numero = str((ligne.get(cle_identifiante) if cle_identifiante else None) or "").strip()
        collectif = _collectif_du_tiers(numero) if numero else None
        if collectif is None:
            orphelins_auxiliaire.append({"numero": numero or None})
            continue
        solde = _solde_ligne_auxiliaire(ligne)
        if solde is None:
            lignes_non_calculables.append({"numero": numero})
            continue
        tiers_par_collectif[collectif].append({"numero": numero, "solde": solde})

    resultats_collectifs = []
    for collectif in collectifs:
        lignes_bg_collectif = [
            l for l in lignes_bg_famille
            if normaliser_compte_collectif(str(l.get("numero_compte") or "").strip()) == collectif
        ]
        solde_balance_generale = sum((_solde_ligne_balance_generale(l) or 0) for l in lignes_bg_collectif)
        tiers = tiers_par_collectif[collectif]
        solde_auxiliaire = sum(t["solde"] for t in tiers)
        ecart = solde_balance_generale - solde_auxiliaire
        resultats_collectifs.append({
            "numero_compte": collectif,
            # Numéros d'origine de la balance générale (affichage, ex. « 401000 ») ;
            # numero_compte reste le collectif normalisé utilisé pour le rattachement.
            "comptes_balance_generale": sorted({str(l.get("numero_compte") or "").strip() for l in lignes_bg_collectif}),
            "solde_balance_generale": solde_balance_generale,
            "solde_auxiliaire": solde_auxiliaire,
            "nb_tiers_rattaches": len(tiers),
            "ecart": ecart,
            "ok": abs(ecart) <= tolerance,
        })

    orphelins_balance_generale = [r["numero_compte"] for r in resultats_collectifs if r["nb_tiers_rattaches"] == 0]

    ok_global = (
        bool(resultats_collectifs)
        and all(r["ok"] for r in resultats_collectifs)
        and not orphelins_auxiliaire
        and not orphelins_balance_generale
        and not lignes_non_calculables
    )

    return {
        "tolerance": tolerance,
        "collectifs": resultats_collectifs,
        "orphelins_auxiliaire": orphelins_auxiliaire,
        "orphelins_balance_generale": orphelins_balance_generale,
        "lignes_non_calculables": lignes_non_calculables,
        "ok": ok_global,
    }


# ---------------------------------------------------------------------------
# IPE-3 — immobilisations : un fichier de biens, pas de tiers
# ---------------------------------------------------------------------------

def _compte_du_bien(bien: Dict[str, Any]) -> Optional[str]:
    """
    Compte d'immobilisation d'un bien : `numero_compte` s'il est renseigné,
    sinon la catégorie si c'est elle-même un numéro de compte de classe 2.
    Une catégorie en toutes lettres (« Matériel de transport ») n'est pas
    traduite en compte — TODO(spec: CAC-IPE-01 §3) : table de
    correspondance catégorie -> compte non fournie.
    """
    numero = str(bien.get("numero_compte") or "").strip()
    if numero:
        return numero
    categorie = str(bien.get("categorie") or "").strip()
    if categorie[:2].isdigit() and categorie.startswith("2"):
        return categorie
    return None


def _identifiant_bien(bien: Dict[str, Any]) -> str:
    return str(bien.get("code_bien") or bien.get("libelle_bien") or "bien sans code").strip()


def _ligne_comparaison(numero_compte, nature, solde_bg, montant_fichier, nb_biens, tolerance) -> Dict[str, Any]:
    ecart = solde_bg - montant_fichier
    return {
        "numero_compte": numero_compte,
        "nature": nature,
        "solde_balance_generale": solde_bg,
        "montant_fichier": montant_fichier,
        "nb_biens": nb_biens,
        "ecart": ecart,
        "ok": abs(ecart) <= tolerance,
    }


def rapprocher_immobilisations(
    lignes_balance_generale: List[Dict[str, Any]],
    biens: List[Dict[str, Any]],
    tolerance: float = TOLERANCE_ECART_IPE,
) -> Dict[str, Any]:
    """
    IPE-3 (docs/PLAN_verrou_IPE.md) : compare le fichier des immobilisations
    (un bien par ligne : valeur brute, amortissements cumulés, valeur nette)
    à la balance générale :
    - somme des valeurs brutes <-> comptes 20 à 27 (soldes débiteurs) ;
    - somme des amortissements cumulés <-> comptes 28 (soldes créditeurs :
      comparés en valeur positive, -solde_reel).
    Par compte si chaque bien porte un compte (ou une catégorie qui en est
    un), sinon par total. Par compte, l'amortissement d'un bien du compte
    2xyz est rattaché au compte 28xyz (convention SYSCOHADA, préfixe le plus
    long) — hypothèse de travail.

    Contrôle complémentaire, bien par bien quand la valeur nette est fournie :
    valeur nette = valeur brute − amortissements cumulés.

    TODO(spec: CAC-IPE-01 §3) : granularité de la comparaison, tolérance
    (0 par défaut), prise en compte des dépréciations (comptes 29, exclues
    ici).
    """
    def numero(ligne):
        return str(ligne.get("numero_compte") or "").strip()

    lignes_brut_bg = [l for l in lignes_balance_generale if numero(l).startswith(RACINES_IMMOBILISATIONS_BRUTES)]
    lignes_amort_bg = [l for l in lignes_balance_generale if numero(l).startswith(RACINE_AMORTISSEMENTS)]

    biens_calculables = [b for b in biens if isinstance(b.get("valeur_brute"), (int, float))]
    lignes_non_calculables = [
        {"bien": _identifiant_bien(b)} for b in biens if not isinstance(b.get("valeur_brute"), (int, float))
    ]

    def amortissement(bien):
        # Cellule vide = bien non amorti (ex. terrain) : 0.
        return bien.get("amortissements_cumules") or 0

    total_bg_brut = sum((_solde_ligne_balance_generale(l) or 0) for l in lignes_brut_bg)
    total_bg_amort = -sum((_solde_ligne_balance_generale(l) or 0) for l in lignes_amort_bg)
    total_fichier_brut = sum(b["valeur_brute"] for b in biens_calculables)
    total_fichier_amort = sum(amortissement(b) for b in biens_calculables)

    totaux = {
        "valeur_brute": _ligne_comparaison("20-27", "valeur_brute", total_bg_brut, total_fichier_brut,
                                           len(biens_calculables), tolerance),
        "amortissements": _ligne_comparaison("28", "amortissements", total_bg_amort, total_fichier_amort,
                                             len(biens_calculables), tolerance),
    }

    par_compte = bool(biens_calculables) and all(_compte_du_bien(b) for b in biens_calculables)
    biens_sans_compte_correspondant: List[str] = []
    biens_amortis_sans_compte_amortissement: List[str] = []

    if par_compte:
        comptes_brut = sorted({normaliser_compte_collectif(numero(l)) for l in lignes_brut_bg}, key=len, reverse=True)
        comptes_amort = sorted({normaliser_compte_collectif(numero(l)) for l in lignes_amort_bg}, key=len, reverse=True)
        biens_par_compte_brut: Dict[str, List[Dict[str, Any]]] = {c: [] for c in comptes_brut}
        biens_par_compte_amort: Dict[str, List[Dict[str, Any]]] = {c: [] for c in comptes_amort}

        for bien in biens_calculables:
            compte = normaliser_compte_collectif(_compte_du_bien(bien))
            compte_brut = next((c for c in comptes_brut if compte.startswith(c)), None)
            if compte_brut is None:
                biens_sans_compte_correspondant.append(_identifiant_bien(bien))
            else:
                biens_par_compte_brut[compte_brut].append(bien)

            compte_amort_attendu = RACINE_AMORTISSEMENTS + compte[1:]
            compte_amort = next((c for c in comptes_amort if compte_amort_attendu.startswith(c)), None)
            if compte_amort is not None:
                biens_par_compte_amort[compte_amort].append(bien)
            elif amortissement(bien):
                biens_amortis_sans_compte_amortissement.append(_identifiant_bien(bien))

        lignes = []
        for compte in sorted(comptes_brut):
            solde_bg = sum((_solde_ligne_balance_generale(l) or 0) for l in lignes_brut_bg
                           if normaliser_compte_collectif(numero(l)) == compte)
            biens_compte = biens_par_compte_brut[compte]
            lignes.append(_ligne_comparaison(compte, "valeur_brute", solde_bg,
                                             sum(b["valeur_brute"] for b in biens_compte), len(biens_compte), tolerance))
        for compte in sorted(comptes_amort):
            solde_bg = -sum((_solde_ligne_balance_generale(l) or 0) for l in lignes_amort_bg
                            if normaliser_compte_collectif(numero(l)) == compte)
            biens_compte = biens_par_compte_amort[compte]
            lignes.append(_ligne_comparaison(compte, "amortissements", solde_bg,
                                             sum(amortissement(b) for b in biens_compte), len(biens_compte), tolerance))
    else:
        lignes = [totaux["valeur_brute"], totaux["amortissements"]]

    # Valeur nette = valeur brute − amortissements, bien par bien.
    biens_avec_vnc = [b for b in biens_calculables if isinstance(b.get("valeur_nette"), (int, float))]
    biens_en_ecart_vnc = []
    for bien in biens_avec_vnc:
        ecart_vnc = bien["valeur_nette"] - (bien["valeur_brute"] - amortissement(bien))
        if abs(ecart_vnc) > tolerance:
            biens_en_ecart_vnc.append({
                "bien": _identifiant_bien(bien),
                "valeur_brute": bien["valeur_brute"],
                "amortissements_cumules": amortissement(bien),
                "valeur_nette": bien["valeur_nette"],
                "ecart": ecart_vnc,
            })
    controle_vnc = {
        "applicable": bool(biens_avec_vnc),
        "nb_biens_controles": len(biens_avec_vnc),
        "biens_en_ecart": biens_en_ecart_vnc,
    }
    if biens_avec_vnc:
        # Ligne qualifiable comme les autres (circuit de revue) si le fichier est incohérent.
        lignes.append({
            "numero_compte": "VNC",
            "nature": "controle_vnc",
            "solde_balance_generale": None,
            "montant_fichier": None,
            "nb_biens": len(biens_avec_vnc),
            "ecart": sum(e["ecart"] for e in biens_en_ecart_vnc),
            "ok": not biens_en_ecart_vnc,
        })

    ok = (
        bool(lignes)
        and all(l["ok"] for l in lignes)
        and not biens_sans_compte_correspondant
        and not biens_amortis_sans_compte_amortissement
        and not lignes_non_calculables
    )

    return {
        "tolerance": tolerance,
        "mode_comparaison": "par_compte" if par_compte else "par_total",
        "lignes": lignes,
        "totaux": totaux,
        "controle_vnc": controle_vnc,
        "biens_sans_compte_correspondant": biens_sans_compte_correspondant,
        "biens_amortis_sans_compte_amortissement": biens_amortis_sans_compte_amortissement,
        "lignes_non_calculables": lignes_non_calculables,
        "ok": ok,
    }


def resoudre_annee_auditee(annee_brute: Any) -> int:
    """Fonction pure : Mission1.annee_auditee -> int, ou échec clair si absente/invalide."""
    try:
        return int(annee_brute)
    except (TypeError, ValueError):
        raise ValueError(
            f"Année auditée invalide ou absente sur la mission ({annee_brute!r}) : "
            "impossible de sélectionner la balance générale de l'exercice N."
        )


def choisir_balance_generale(balances_candidates: List[Dict[str, Any]], annee_n: int) -> Dict[str, Any]:
    """
    Fonction pure : parmi des documents Balance déjà récupérés, choisit celui
    dont `annee_balance` correspond à l'exercice audité N — jamais N-1,
    jamais par position (docs/PLAN_verrou_IPE.md §4, correction). Échoue
    avec un message clair si introuvable ou ambigu : ne choisit jamais au
    hasard entre plusieurs candidats.
    """
    candidats = [d for d in balances_candidates if d and d.get("annee_balance") in (annee_n, str(annee_n))]

    if not candidats:
        raise ValueError(f"Balance générale introuvable pour l'exercice audité {annee_n}.")
    if len(candidats) > 1:
        raise ValueError(
            f"Sélection ambiguë : {len(candidats)} balances générales trouvées pour l'exercice {annee_n}."
        )
    return candidats[0]


def resoudre_balance_generale(mission_id: str) -> Dict[str, Any]:
    """
    Résout le document Balance générale de l'exercice audité en allant lire
    Mongo (Mission1.annee_auditee + Mission1.balances), puis délègue le choix
    à choisir_balance_generale (fonction pure, testée séparément). Publique
    (plus de `_`) : réutilisée par verrou_ipe_service.verifier_coherence_fichiers
    pour détecter un remplacement de la balance générale par le flux V1
    (api/src/model.py), qui ne déclenche aucune invalidation à l'écriture.
    """
    try:
        mission_object_id = ObjectId(mission_id)
    except InvalidId:
        raise ValueError(f"mission_id invalide : '{mission_id}'")

    db = get_database()
    mission_doc = db[COLLECTION_MISSION].find_one({"_id": mission_object_id}, {"balances": 1, "annee_auditee": 1})
    if not mission_doc:
        raise ValueError(f"Mission introuvable : '{mission_id}'.")

    balances_ids = mission_doc.get("balances") or []
    if not balances_ids:
        raise ValueError(f"Aucune balance générale associée à la mission '{mission_id}'.")

    annee_n = resoudre_annee_auditee(mission_doc.get("annee_auditee"))

    candidats = []
    for balance_id in balances_ids:
        try:
            balance_object_id = ObjectId(balance_id)
        except InvalidId:
            continue
        doc = db[COLLECTION_BALANCE].find_one({"_id": balance_object_id})
        if doc:
            candidats.append(doc)

    try:
        return choisir_balance_generale(candidats, annee_n)
    except ValueError as e:
        raise ValueError(f"{e} (mission '{mission_id}')")


def _lire_balance_generale(mission_id: str) -> List[Dict[str, Any]]:
    return resoudre_balance_generale(mission_id).get("balance", []) or []


def _lire_auxiliaire_actif(mission_id: str, type_auxiliaire: str) -> List[Dict[str, Any]]:
    doc = get_database()[COLLECTION_BALANCE].find_one({
        "mission_id": mission_id,
        "type": type_auxiliaire,
        "actif": True,
    })
    if not doc:
        return []
    return doc.get("balance", []) or []


def determiner_statut_module(resultat: Dict[str, Any], fichier_auxiliaire_absent: bool) -> Dict[str, Optional[str]]:
    """
    Fonction pure : détermine le statut d'un module IPE à partir du résultat
    de rapprocher_famille et de la présence (ou non) d'un fichier
    complémentaire actif. Ne renvoie JAMAIS "ecart" quand il n'y a rien de
    réel à comparer : "non_evaluable" avec un motif explicite si le fichier
    complémentaire actif est absent, ou si aucun compte collectif n'a été
    trouvé dans la balance générale pour cette famille.
    """
    if fichier_auxiliaire_absent:
        return {"statut": "non_evaluable", "motif_non_evaluable": "fichier_complementaire_absent"}
    if not resultat["collectifs"]:
        return {"statut": "non_evaluable", "motif_non_evaluable": "aucun_compte_collectif_trouve"}
    if resultat["ok"]:
        return {"statut": "ok", "motif_non_evaluable": None}
    return {"statut": "ecart", "motif_non_evaluable": None}


def evaluer_module(
    config: Dict[str, str],
    lignes_balance_generale: List[Dict[str, Any]],
    lignes_fichier: List[Dict[str, Any]],
    horodatage: str,
) -> Dict[str, Any]:
    """
    Fonction pure : statut + dernière évaluation d'un module IPE, selon sa
    nature (tiers ou immobilisations). Aucun fichier complémentaire actif ->
    "non_evaluable" (fichier absent), quelle que soit la nature.

    `detail_collectifs` reste le nom de stockage des lignes de comparaison
    pour tous les modules (lu par le circuit de revue pour la qualification
    des écarts) : pour IPE-3, ce sont des comptes d'immobilisations ou
    d'amortissements, jamais des tiers.
    """
    fichier_absent = not lignes_fichier

    if config["nature"] == "immobilisations":
        resultat = rapprocher_immobilisations(lignes_balance_generale, lignes_fichier)
        lignes = resultat["lignes"]
        decision_statut = determiner_statut_module({"collectifs": lignes, "ok": resultat["ok"]}, fichier_absent)
        statut = decision_statut["statut"]
        specifique = {
            # Écart global affiché en synthèse : celui des valeurs brutes (total).
            "ecart_global": None if fichier_absent else resultat["totaux"]["valeur_brute"]["ecart"],
            "mode_comparaison": resultat["mode_comparaison"],
            "totaux": resultat["totaux"],
            "controle_vnc": resultat["controle_vnc"],
            "biens_sans_compte_correspondant": resultat["biens_sans_compte_correspondant"],
            "biens_amortis_sans_compte_amortissement": resultat["biens_amortis_sans_compte_amortissement"],
        }
    else:
        resultat = rapprocher_famille(
            lignes_balance_generale, lignes_fichier,
            config["racine_collectif"], _cle_identifiante(lignes_fichier),
        )
        lignes = resultat["collectifs"]
        decision_statut = determiner_statut_module(resultat, fichier_absent)
        statut = decision_statut["statut"]
        specifique = {
            "ecart_global": sum(c["ecart"] for c in lignes) if lignes else None,
            "tiers_orphelins": {
                "balance_generale_seulement": resultat["orphelins_balance_generale"],
                "auxiliaire_seulement": [o["numero"] for o in resultat["orphelins_auxiliaire"]],
            },
        }

    return {
        "statut": statut,
        "derniere_evaluation": {
            "date_evaluation": horodatage,
            "nature": config["nature"],
            "motif_non_evaluable": decision_statut["motif_non_evaluable"],
            "detail_collectifs": lignes,
            "lignes_non_calculables": resultat["lignes_non_calculables"],
            **specifique,
            "qualification": {
                # TODO(spec: CAC-IPE-01) — valeurs possibles non confirmées.
                "etiquette": None,
                "statut": statut,
                "commentaire": None,
                "validation": {"validee": None, "par_utilisateur_id": None, "horodatage": None},
            },
        },
    }


def evaluer_ipe(mission_id: str) -> Dict[str, Any]:
    """
    Lance le rapprochement des 3 familles IPE pour une mission et enregistre
    le résultat dans Mission1.ipe.modules (+ entrée d'historique). Ne touche
    JAMAIS ipe_fiabilite_validee : cette décision reste un acte de validation
    manager séparé (valider_fiabilite ci-dessous, docs/PLAN_verrou_IPE.md §5).
    """
    lignes_balance_generale = _lire_balance_generale(mission_id)

    horodatage = datetime.now(timezone.utc).isoformat()
    modules_doc: Dict[str, Any] = {}
    resultat_par_module: Dict[str, str] = {}

    for module, config in FAMILLES_IPE.items():
        lignes_fichier = _lire_auxiliaire_actif(mission_id, config["type_auxiliaire"])
        modules_doc[module] = evaluer_module(config, lignes_balance_generale, lignes_fichier, horodatage)
        resultat_par_module[module] = modules_doc[module]["statut"]

    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": None,  # pas de contrôle d'accès existant, voir CLAUDE.md
        "action": "evaluation",
        "resultat": resultat_par_module,
        "commentaire": None,
    }

    # Fichiers effectivement utilisés (_id par type, None si absent) : la
    # soumission pour revue exige un rapprochement fait sur les versions
    # actuelles (revue_ipe_service.refus_rapprochement).
    fichiers_evalues = verrou_ipe_service.references_fichiers_actuelles(mission_id)

    get_database()[COLLECTION_MISSION].update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.modules": modules_doc, "ipe.fichiers_evalues": fichiers_evalues},
            "$push": {"ipe.historique": historique_entree},
        },
    )

    return verrou_ipe_service.lire_etat_ipe(mission_id)


def _fichiers_references_actuels(mission_id: str) -> Dict[str, Any]:
    """
    Références (_id, version) des fichiers effectivement utilisés au moment
    de la validation — balance générale (exercice N) + chaque fichier
    complémentaire actif présent. Sert à détecter, lors d'un futur import,
    si le fichier qui a servi à la validation a été remplacé (invalidation
    automatique, voir verrou_ipe_service.invalider_si_fichier_remplace).
    Propage l'échec de resoudre_balance_generale : on ne valide jamais avec
    une référence de balance générale introuvable/ambiguë.
    """
    balance_generale = resoudre_balance_generale(mission_id)
    references: Dict[str, Any] = {
        "balance_generale": {
            "_id": str(balance_generale["_id"]),
            "annee_balance": balance_generale.get("annee_balance"),
        },
    }

    fichiers = fc_service.lister_fichiers_complementaires(mission_id)
    for type_fichier, docs in fichiers.items():
        if docs:
            # Un seul actif par type garanti par archiver_version_active (import lot).
            references[type_fichier] = {"_id": docs[0]["_id"], "version": docs[0].get("version")}

    return references


# Délai minimal entre deux validations/invalidations IDENTIQUES (même valeur
# de `validee`) — garde-fou contre un double clic qui passerait malgré la
# désactivation du bouton côté frontend (docs/PLAN_verrou_IPE.md).
DELAI_MIN_VALIDATIONS_IDENTIQUES_SECONDES = 5.0


def validation_identique_trop_recente(
    historique: List[Dict[str, Any]],
    validee: bool,
    maintenant: Optional[Any] = None,
) -> bool:
    """
    Fonction pure : vraie si la dernière entrée d'historique est déjà une
    validation manager avec la MÊME valeur de `validee`, survenue il y a
    moins de DELAI_MIN_VALIDATIONS_IDENTIQUES_SECONDES — signe d'un double
    clic plutôt que de deux décisions distinctes (ex. valider puis
    invalider, volontaire, n'est jamais bloqué par cette règle).
    """
    if not historique:
        return False

    derniere = historique[-1]
    if derniere.get("action") != "validation_manager":
        return False
    if derniere.get("resultat", {}).get("validee") != validee:
        return False

    try:
        horodatage_derniere = datetime.fromisoformat(derniere["horodatage"])
    except (KeyError, TypeError, ValueError):
        return False

    maintenant = maintenant or datetime.now(timezone.utc)
    ecart_secondes = (maintenant - horodatage_derniere).total_seconds()
    return 0 <= ecart_secondes < DELAI_MIN_VALIDATIONS_IDENTIQUES_SECONDES


def modules_en_ecart_non_qualifie(modules: Optional[Dict[str, Any]]) -> List[str]:
    """
    Fonction pure : clés des modules dont le statut est "ecart" (un vrai
    écart, jamais "non_evaluable" — docs/PLAN_verrou_IPE.md) sans étiquette
    de qualification renseignée. Les modules "non_evaluable" ne sont jamais
    inclus : leur traitement reste TODO(spec: CAC-IPE-01) — signalés à
    l'écran, pas bloquants ici.

    Historique : n'est plus le mécanisme de blocage de valider_fiabilite
    (remplacé par le circuit de revue — revue_ipe_service.ecarts_non_qualifies,
    basé sur les remarques, seul mécanisme de qualification réellement
    utilisable tant que qualification.etiquette n'a aucun écrivain). Conservée
    (fonction + tests) comme utilitaire autonome, non appelée ailleurs.
    """
    non_qualifies = []
    for cle, module in (modules or {}).items():
        if module.get("statut") != "ecart":
            continue
        qualification = (module.get("derniere_evaluation") or {}).get("qualification") or {}
        if not qualification.get("etiquette"):
            non_qualifies.append(cle)
    return non_qualifies


def valider_fiabilite(
    mission_id: str,
    validee: bool,
    utilisateur_id: Optional[str] = None,
    commentaire: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validation manager de ipe_fiabilite_validee (docs/PLAN_verrou_IPE.md §5).
    Enregistrée sans contrôle de rôle : aucun système d'authentification/
    droits n'existe sur les missions aujourd'hui (CLAUDE.md, point de
    sécurité connu) — utilisateur_id reste nullable.

    Refuse explicitement (ValueError, rien n'est écrit) :
    - une validation/invalidation identique à la précédente il y a moins de
      DELAI_MIN_VALIDATIONS_IDENTIQUES_SECONDES (double clic) ;
    - une validation positive (validee=True) tant que le circuit de revue
      n'est pas au statut "soumis_pour_revue", ou tant qu'un écart n'est
      pas qualifié, qu'une demande de correction n'est pas traitée, ou
      qu'un module non évaluable n'a pas de justification écrite (voir
      revue_ipe_service.refus_validation) —
      TODO(décision : qui a le droit de valider n'est pas vérifié
      aujourd'hui, CLAUDE.md).

    Une validation positive fige les références des fichiers utilisés
    (balance générale + fichiers complémentaires actifs) : tout remplacement
    ultérieur d'un de ces fichiers invalide automatiquement cette validation
    (voir verrou_ipe_service.invalider_si_fichier_remplace, appelé depuis les
    services d'import). Une validation positive fait passer statut_circuit à
    "valide" ; une invalidation le remet à "en_cours" (les deux restent
    toujours cohérents avec ipe_fiabilite_validee).
    """
    etat_actuel = verrou_ipe_service.lire_etat_ipe(mission_id)

    if validation_identique_trop_recente(etat_actuel.get("historique") or [], validee):
        raise ValueError(
            "Validation refusée : une "
            + ("validation" if validee else "invalidation")
            + " identique vient déjà d'être enregistrée il y a moins de "
            f"{DELAI_MIN_VALIDATIONS_IDENTIQUES_SECONDES:.0f} secondes (double clic ?)."
        )

    if validee:
        statut_circuit_actuel = etat_actuel.get("statut_circuit") or "en_cours"
        if statut_circuit_actuel != "soumis_pour_revue":
            raise ValueError(
                "Validation refusée : le contrôle IPE doit d'abord être « Soumis pour revue » "
                f"(statut actuel : {statut_circuit_actuel}). L'auditeur doit soumettre le contrôle "
                "pour revue avant toute validation."
            )
        # Écarts qualifiés, demandes de correction traitées, modules non
        # évaluables justifiés (revue_ipe_service.refus_validation).
        refus = revue_ipe_service.refus_validation(etat_actuel)
        if refus:
            raise ValueError(refus)

    horodatage = datetime.now(timezone.utc).isoformat()
    updates: Dict[str, Any] = {
        "ipe.ipe_fiabilite_validee": validee,
        "ipe.statut_circuit": "valide" if validee else "en_cours",
    }
    if validee:
        updates["ipe.fichiers_references"] = _fichiers_references_actuels(mission_id)

    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": utilisateur_id,
        "action": "validation_manager",
        "resultat": {"validee": validee},
        "commentaire": commentaire,
    }

    get_database()[COLLECTION_MISSION].update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": updates,
            "$push": {"ipe.historique": historique_entree},
        },
    )

    return verrou_ipe_service.lire_etat_ipe(mission_id)
