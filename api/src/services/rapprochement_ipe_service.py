"""
Rapprochements IPE-1/2/3 (clients↔411, fournisseurs↔40x, immobilisations↔2xxx)
et validation manager de la fiabilité IPE. Nouveau périmètre V2 — voir
docs/PLAN_verrou_IPE.md §4 et §5.

Point clé (corrigé après relecture du plan) : la balance générale ne contient
QUE des comptes collectifs (ex. une ligne "411", ou plusieurs collectifs plus
fins "401"/"402"/"403"), jamais le détail par tiers. Le rapprochement se fait
donc collectif par collectif : solde du collectif (balance générale) comparé
à la somme des tiers de l'auxiliaire qui s'y rattachent — jamais une simple
somme globale balance-générale-contre-tout-l'auxiliaire.

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
harmonisée entre balance générale et auxiliaire, périmètre exact d'IPE-3
(inclusion ou non des comptes 28x/29x), traitement des orphelins, conditions
de passage à TRUE de ipe_fiabilite_validee.
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

# Famille IPE -> (racine du compte collectif ciblé, type de fichier auxiliaire
# correspondant dans la collection Balance). Voir CLAUDE.md pour IPE-1/2/3.
FAMILLES_IPE: Dict[str, Dict[str, str]] = {
    "ipe_1_clients": {"racine_collectif": "411", "type_auxiliaire": "auxiliaire_client"},
    "ipe_2_fournisseurs": {"racine_collectif": "40", "type_auxiliaire": "auxiliaire_fournisseur"},
    # TODO(spec: CAC-IPE-01 §2) — périmètre exact de "2xxx" : inclut-on les
    # comptes d'amortissement/provision (28x/29x) ? Pris au sens large de
    # CLAUDE.md pour l'instant (racine "2" seule).
    "ipe_3_immobilisations": {"racine_collectif": "2", "type_auxiliaire": "immobilisations"},
}


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
    tolerance: float = 0.0,
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
        lignes_auxiliaire = _lire_auxiliaire_actif(mission_id, config["type_auxiliaire"])
        fichier_absent = not lignes_auxiliaire
        cle_identifiante = _cle_identifiante(lignes_auxiliaire)
        resultat = rapprocher_famille(
            lignes_balance_generale, lignes_auxiliaire,
            config["racine_collectif"], cle_identifiante,
        )

        decision_statut = determiner_statut_module(resultat, fichier_absent)
        statut = decision_statut["statut"]

        ecart_global = sum(c["ecart"] for c in resultat["collectifs"]) if resultat["collectifs"] else None

        modules_doc[module] = {
            "statut": statut,
            "derniere_evaluation": {
                "date_evaluation": horodatage,
                "ecart_global": ecart_global,
                "motif_non_evaluable": decision_statut["motif_non_evaluable"],
                "tiers_orphelins": {
                    "balance_generale_seulement": resultat["orphelins_balance_generale"],
                    "auxiliaire_seulement": [o["numero"] for o in resultat["orphelins_auxiliaire"]],
                },
                "detail_collectifs": resultat["collectifs"],
                "lignes_non_calculables": resultat["lignes_non_calculables"],
                "qualification": {
                    # TODO(spec: CAC-IPE-01) — valeurs possibles non confirmées.
                    "etiquette": None,
                    "statut": statut,
                    "commentaire": None,
                    "validation": {"validee": None, "par_utilisateur_id": None, "horodatage": None},
                },
            },
        }
        resultat_par_module[module] = statut

    historique_entree = {
        "horodatage": horodatage,
        "utilisateur_id": None,  # pas de contrôle d'accès existant, voir CLAUDE.md
        "action": "evaluation",
        "resultat": resultat_par_module,
        "commentaire": None,
    }

    get_database()[COLLECTION_MISSION].update_one(
        {"_id": ObjectId(mission_id)},
        {
            "$set": {"ipe.modules": modules_doc},
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
