"""
Circularisation, sous-lot c (docs/PLAN_circularisation.md), maquette
5_Suivi_reponses : envois enregistrés par l'auditeur, relances selon
CADENCE_RELANCES, réponses, écarts constatés, procédures alternatives.

AUCUN envoi automatique : l'outil n'envoie ni courriel ni courrier (pas
d'authentification, pas de serveur d'envoi — PLAN §5). L'auditeur enregistre
l'envoi et chaque relance ; l'outil calcule les échéances et les statuts.

Collection `CirEnvoi` : une demande par (mission, type de tiers, tiers), avec
l'historique des relances, réponses (versions), analyses d'écart et
procédures alternatives ; pièces jointes en GridFS. Actions au journal
`CirJournal` (module « Suivi des réponses »). Rien n'est supprimé.
"""
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services import circularisation_service as cir
from src.services import courriers_service as courriers
from src.services.parametres_service import CADENCE_RELANCES

COLLECTION_ENVOI = "CirEnvoi"
MODULE_JOURNAL = "Suivi des réponses"
CANAUX = ("courriel", "postal")
TYPES_REPONSE = ("accord_total", "accord_partiel", "desaccord")
LIBELLES_REPONSE = {"accord_total": "accord total", "accord_partiel": "accord partiel", "desaccord": "désaccord"}
TAILLE_MAX_PIECE = 10 * 1024 * 1024  # TODO(décision) : limite provisoire
NB_RELANCES = sum(1 for c in CADENCE_RELANCES if c["cle"].startswith("relance"))


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db():
    return get_database()


def _journaliser(mission_id: str, utilisateur_id: Optional[str], action: str, detail: str, **reference) -> None:
    _db()[cir.COLLECTION_JOURNAL].insert_one({
        "mission_id": mission_id, "horodatage": _maintenant(), "utilisateur_id": utilisateur_id,
        "module": MODULE_JOURNAL, "action": action, "detail": detail, "reference": reference,
    })


def lire_date(valeur: Any, nom: str) -> date:
    try:
        return date.fromisoformat(str(valeur or "").strip())
    except ValueError:
        raise ValueError(f"Date « {nom} » invalide (attendu : AAAA-MM-JJ).")


# --- Calculs (fonctions pures) ---------------------------------------------------

def echeances(date_envoi: date, cadence=CADENCE_RELANCES) -> List[Dict[str, Any]]:
    """Échéances d'une demande, figées à l'envoi : J0, relances, alternative."""
    return [{"cle": c["cle"], "libelle": c["libelle"], "jour": c["jour"],
             "date": (date_envoi + timedelta(days=c["jour"])).isoformat()} for c in cadence]


def ecart(solde_comptable: float, type_reponse: str, solde_confirme: Optional[float]) -> float:
    """
    Écart = solde comptable (en valeur absolue) − solde confirmé par le tiers ;
    accord total : écart nul. TODO(spec: CAC-CIR-01) : convention de signe,
    tolérance (aucune ici), traitement d'un accord partiel.
    """
    if type_reponse == "accord_total":
        return 0.0
    return abs(solde_comptable or 0) - (solde_confirme or 0)


def statut(envoi: Dict[str, Any], aujourd_hui: date) -> Dict[str, Any]:
    """
    Statut affiché et prochaine étape (maquette) :
    réponse → « Réponse reçue » ou « Écart constaté » ; sinon, selon les
    échéances figées et les relances enregistrées : « Envoyé », « À relancer »,
    « Relance 1 », « Relance 2 », puis « Sans réponse » après l'échéance
    « Alternative ».
    """
    reponse = (envoi.get("reponses") or [None])[-1]
    if reponse:
        if reponse["ecart"] or reponse["type"] == "desaccord":
            analyse = (envoi.get("analyses_ecart") or [None])[-1]
            return {"cle": "ecart", "libelle": "Écart constaté",
                    "prochaine_etape": "Écart analysé" if analyse else "Feuille d'analyse à compléter"}
        return {"cle": "reponse_recue", "libelle": "Réponse reçue", "prochaine_etape": "—"}

    dates = {e["cle"]: date.fromisoformat(e["date"]) for e in envoi["echeances"]}
    relances = envoi.get("relances") or []
    if aujourd_hui >= dates["alternative"]:
        procedure = (envoi.get("procedures_alternatives") or [None])[-1]
        return {"cle": "sans_reponse", "libelle": "Sans réponse",
                "prochaine_etape": "Procédure alternative documentée" if procedure else "Procédure alternative"}
    rang_du = sum(1 for n in range(1, NB_RELANCES + 1) if aujourd_hui >= dates[f"relance_{n}"])
    if rang_du > len(relances):
        return {"cle": "a_relancer", "libelle": "À relancer", "rang_du": len(relances) + 1,
                "prochaine_etape": f"Relance {len(relances) + 1} due depuis le {dates[f'relance_{len(relances) + 1}'].strftime('%d/%m/%Y')}"}
    if relances:
        n = len(relances)
        suivante = dates[f"relance_{n + 1}"] if n < NB_RELANCES else dates["alternative"]
        quoi = f"Relance {n + 1}" if n < NB_RELANCES else "Procédure alternative"
        alerte = " · alerte du Manager à faire" if n == 2 else ""  # pas de canal de notification (PLAN §5)
        return {"cle": f"relance_{n}", "libelle": f"Relance {n}",
                "prochaine_etape": f"{quoi} le {suivante.strftime('%d/%m/%Y')}{alerte}"}
    return {"cle": "envoye", "libelle": "Envoyé",
            "prochaine_etape": f"Relance 1 le {dates['relance_1'].strftime('%d/%m/%Y')}"}


def indicateurs(demandes: List[Dict[str, Any]]) -> Dict[str, Any]:
    cles = [d["statut"]["cle"] for d in demandes]
    recues = sum(1 for c in cles if c in ("reponse_recue", "ecart"))
    return {
        "envoyes": len(demandes),
        "reponses_recues": recues,
        "taux_reponse": (recues / len(demandes) * 100) if demandes else None,
        "en_relance": sum(1 for c in cles if c == "a_relancer" or c.startswith("relance_")),
        "ecarts": cles.count("ecart"),
        "sans_reponse": cles.count("sans_reponse"),
    }


# --- Lectures --------------------------------------------------------------------

def _serialiser(envoi: Dict[str, Any], aujourd_hui: date) -> Dict[str, Any]:
    return {**{k: v for k, v in envoi.items() if k != "_id"}, "_id": str(envoi["_id"]),
            "statut": statut(envoi, aujourd_hui)}


def lire_suivi(mission_id: str, aujourd_hui: Optional[date] = None) -> Dict[str, Any]:
    """Demandes envoyées (statut du jour), indicateurs, tiers retenus sans envoi, cadence."""
    aujourd_hui = aujourd_hui or date.today()
    mission = courriers._mission(mission_id)
    id_client = str(mission.get("id_client"))
    envois = list(_db()[COLLECTION_ENVOI].find({"mission_id": mission_id}))
    deja = {(e["type_tiers"], e["numero"]) for e in envois}
    a_envoyer = []
    for config in cir.TYPES_TIERS:
        selection = cir._selection_active(mission_id, config["cle"])
        if not selection:
            continue
        courantes = cir.decisions_courantes(selection["decisions"])
        for t in selection["population"]["lignes"]:
            if courantes.get(t["numero"], {}).get("retenu") and (config["cle"], t["numero"]) not in deja:
                coord = courriers._coordonnees(id_client, config["cle"], t["numero"])
                a_envoyer.append({**t, "type_tiers": config["cle"], "type_libelle": config["libelle"],
                                  "courriel": (coord or {}).get("courriel"), "adresse": (coord or {}).get("adresse"),
                                  "raison_sociale": (coord or {}).get("raison_sociale")})
    demandes = sorted((_serialiser(e, aujourd_hui) for e in envois), key=lambda d: d["date_envoi"], reverse=True)
    return {
        "aujourd_hui": aujourd_hui.isoformat(),
        "cadence": [{k: c[k] for k in ("cle", "libelle", "jour", "description")} for c in CADENCE_RELANCES],
        "indicateurs": indicateurs(demandes),
        "demandes": demandes,
        "a_envoyer": a_envoyer,
        "types_reponse": LIBELLES_REPONSE,
    }


def _envoi(mission_id: str, envoi_id: str) -> Dict[str, Any]:
    try:
        envoi = _db()[COLLECTION_ENVOI].find_one({"_id": ObjectId(envoi_id), "mission_id": mission_id})
    except (InvalidId, TypeError):
        envoi = None
    if not envoi:
        raise ValueError("Demande de confirmation introuvable.")
    return envoi


def _piece(contenu: Optional[bytes], nom_fichier: Optional[str], mission_id: str, nature: str) -> Optional[Dict[str, Any]]:
    if not contenu:
        return None
    if len(contenu) > TAILLE_MAX_PIECE:
        raise ValueError("Pièce jointe trop volumineuse (10 Mo au plus).")
    fichier_id = courriers._gridfs().put(contenu, filename=nom_fichier, mission_id=mission_id, nature=nature)
    return {"fichier_id": str(fichier_id), "nom_fichier": nom_fichier}


# --- Actions ---------------------------------------------------------------------

def enregistrer_envoi(mission_id: str, type_tiers: str, numero: str, canal: str, date_envoi: Any,
                      destinataire: Optional[str], utilisateur_id: Optional[str],
                      aujourd_hui: Optional[date] = None) -> Dict[str, Any]:
    """Envoi d'une demande pour un tiers retenu : échéances calculées depuis CADENCE_RELANCES et figées."""
    aujourd_hui = aujourd_hui or date.today()
    courriers._mission(mission_id)
    config = cir._type(type_tiers)
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, "Enregistrement de l'envoi")
    if canal not in CANAUX:
        raise ValueError("Canal d'envoi inconnu (courriel ou postal).")
    jour = lire_date(date_envoi, "Envoyé le")
    if jour > aujourd_hui:
        raise ValueError("La date d'envoi ne peut pas être dans le futur.")
    destinataire = (destinataire or "").strip() or None
    if not destinataire:
        raise ValueError("Indiquez le destinataire (courriel ou adresse postale).")
    if canal == "courriel" and not courriers.COURRIEL.match(destinataire):
        raise ValueError("Adresse de courriel du destinataire invalide.")
    selection = cir._selection_active(mission_id, type_tiers)
    retenu = selection and cir.decisions_courantes(selection["decisions"]).get(numero, {}).get("retenu")
    tiers = next((t for t in (selection or {}).get("population", {}).get("lignes", []) if t["numero"] == numero), None)
    if not (retenu and tiers):
        raise ValueError(f"Le tiers {numero} n'est pas retenu dans la sélection {config['libelle'].lower()}.")
    if _db()[COLLECTION_ENVOI].find_one({"mission_id": mission_id, "type_tiers": type_tiers, "numero": numero}):
        raise ValueError(f"Une demande a déjà été envoyée au tiers {numero}.")
    _db()[COLLECTION_ENVOI].insert_one({
        "mission_id": mission_id, "type_tiers": type_tiers, "type_libelle": config["libelle"],
        "numero": numero, "libelle": tiers["libelle"], "solde_comptable": tiers["solde"],
        "selection_id": str(selection["_id"]), "statut_selection": selection["statut"],
        "canal": canal, "destinataire": destinataire, "date_envoi": jour.isoformat(),
        "echeances": echeances(jour), "envoye_par": utilisateur_id, "enregistre_le": _maintenant(),
        "relances": [], "reponses": [], "analyses_ecart": [], "procedures_alternatives": [],
    })
    _journaliser(mission_id, utilisateur_id, "Demande de confirmation envoyée",
                 f"{config['libelle']} · {numero} · {tiers['libelle']} · {canal} · le {jour.strftime('%d/%m/%Y')}",
                 type_tiers=type_tiers, numero=numero)
    return lire_suivi(mission_id, aujourd_hui)


def enregistrer_relance(mission_id: str, envoi_id: str, date_relance: Any, canal: str,
                        utilisateur_id: Optional[str], aujourd_hui: Optional[date] = None) -> Dict[str, Any]:
    """Relance faite par l'auditeur (rang suivant). Refusée après une réponse ou au-delà des relances prévues."""
    aujourd_hui = aujourd_hui or date.today()
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, "Enregistrement de la relance")
    envoi = _envoi(mission_id, envoi_id)
    if canal not in CANAUX:
        raise ValueError("Canal de relance inconnu (courriel ou postal).")
    if envoi["reponses"]:
        raise ValueError("Une réponse a été reçue : plus de relance.")
    if len(envoi["relances"]) >= NB_RELANCES:
        raise ValueError(f"Les {NB_RELANCES} relances prévues ont déjà été faites.")
    jour = lire_date(date_relance, "Relancé le")
    precedente = date.fromisoformat((envoi["relances"] or [{"date": envoi["date_envoi"]}])[-1]["date"])
    if jour < precedente or jour > aujourd_hui:
        raise ValueError("Date de relance incohérente (avant l'envoi ou la relance précédente, ou dans le futur).")
    rang = len(envoi["relances"]) + 1
    _db()[COLLECTION_ENVOI].update_one({"_id": envoi["_id"]}, {"$push": {"relances": {
        "rang": rang, "date": jour.isoformat(), "canal": canal, "utilisateur_id": utilisateur_id, "horodatage": _maintenant()}}})
    _journaliser(mission_id, utilisateur_id, f"Relance {rang} enregistrée",
                 f"{envoi['type_libelle']} · {envoi['numero']} · {envoi['libelle']} · {canal} · le {jour.strftime('%d/%m/%Y')}",
                 envoi_id=envoi_id)
    return lire_suivi(mission_id, aujourd_hui)


def enregistrer_reponse(mission_id: str, envoi_id: str, donnees: Dict[str, Any], piece: Optional[bytes],
                        nom_piece: Optional[str], utilisateur_id: Optional[str],
                        aujourd_hui: Optional[date] = None) -> Dict[str, Any]:
    """Réponse du tiers (nouvelle version si corrigée) : écart calculé, pièce signée facultative en GridFS."""
    aujourd_hui = aujourd_hui or date.today()
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, "Saisie de la réponse")
    envoi = _envoi(mission_id, envoi_id)
    type_reponse = donnees.get("type")
    if type_reponse not in TYPES_REPONSE:
        raise ValueError("Type de réponse inconnu (accord total, accord partiel, désaccord).")
    canal = donnees.get("canal")
    if canal not in CANAUX:
        raise ValueError("Canal de réception inconnu (courriel ou courrier).")
    jour = lire_date(donnees.get("recue_le"), "Reçue le")
    if jour < date.fromisoformat(envoi["date_envoi"]) or jour > aujourd_hui:
        raise ValueError("Date de réception incohérente (avant l'envoi ou dans le futur).")
    commentaire = cir._exiger_motif(donnees.get("commentaire"), "Le commentaire")
    solde_confirme = None
    if type_reponse != "accord_total":
        try:
            solde_confirme = float(str(donnees.get("solde_confirme")).replace(" ", "").replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("Indiquez le solde confirmé par le tiers (FCFA).")
    reponse = {
        "version": len(envoi["reponses"]) + 1, "type": type_reponse, "canal": canal, "recue_le": jour.isoformat(),
        "solde_confirme": solde_confirme, "ecart": ecart(envoi["solde_comptable"], type_reponse, solde_confirme),
        "commentaire": commentaire, "piece": _piece(piece, nom_piece, mission_id, "reponse_signee"),
        "utilisateur_id": utilisateur_id, "horodatage": _maintenant(),
    }
    _db()[COLLECTION_ENVOI].update_one({"_id": envoi["_id"]}, {"$push": {"reponses": reponse}})
    _journaliser(mission_id, utilisateur_id, "Réponse enregistrée" if reponse["version"] == 1 else "Réponse corrigée",
                 f"{envoi['type_libelle']} · {envoi['numero']} · {envoi['libelle']} · {LIBELLES_REPONSE[type_reponse]}"
                 f" · écart {reponse['ecart']:,.0f}".replace(",", " "), envoi_id=envoi_id)
    return lire_suivi(mission_id, aujourd_hui)


def _documenter(mission_id: str, envoi_id: str, champ: str, action: str, condition, refus: str,
                commentaire: Optional[str], piece: Optional[bytes], nom_piece: Optional[str],
                utilisateur_id: Optional[str], aujourd_hui: Optional[date]) -> Dict[str, Any]:
    aujourd_hui = aujourd_hui or date.today()
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, action)
    envoi = _envoi(mission_id, envoi_id)
    if not condition(statut(envoi, aujourd_hui)):
        raise ValueError(refus)
    commentaire = cir._exiger_motif(commentaire, "Le commentaire")
    _db()[COLLECTION_ENVOI].update_one({"_id": envoi["_id"]}, {"$push": {champ: {
        "commentaire": commentaire, "piece": _piece(piece, nom_piece, mission_id, champ),
        "utilisateur_id": utilisateur_id, "horodatage": _maintenant()}}})
    _journaliser(mission_id, utilisateur_id, action,
                 f"{envoi['type_libelle']} · {envoi['numero']} · {envoi['libelle']} · « {commentaire} »", envoi_id=envoi_id)
    return lire_suivi(mission_id, aujourd_hui)


def analyser_ecart(mission_id, envoi_id, commentaire, piece, nom_piece, utilisateur_id, aujourd_hui=None):
    """Analyse d'un écart constaté. TODO(spec: CAC-CIR-01) : contenu de la feuille d'analyse, revue."""
    return _documenter(mission_id, envoi_id, "analyses_ecart", "Analyse d'écart enregistrée",
                       lambda s: s["cle"] == "ecart", "Aucun écart constaté sur cette demande.",
                       commentaire, piece, nom_piece, utilisateur_id, aujourd_hui)


def documenter_procedure_alternative(mission_id, envoi_id, commentaire, piece, nom_piece, utilisateur_id, aujourd_hui=None):
    """Procédure alternative pour un tiers sans réponse. TODO(spec: CAC-CIR-01) : procédures admises."""
    return _documenter(mission_id, envoi_id, "procedures_alternatives", "Procédure alternative documentée",
                       lambda s: s["cle"] == "sans_reponse",
                       "Procédure alternative possible seulement pour un tiers sans réponse après la dernière échéance.",
                       commentaire, piece, nom_piece, utilisateur_id, aujourd_hui)


def lire_piece(mission_id: str, fichier_id: str) -> Dict[str, Any]:
    """Pièce jointe d'une demande de la mission (réponse signée, analyse, procédure)."""
    try:
        oid = ObjectId(fichier_id)
    except (InvalidId, TypeError):
        raise ValueError("Pièce introuvable.")
    fichier = courriers._gridfs().get(oid)
    if getattr(fichier, "mission_id", None) != mission_id:
        raise ValueError("Pièce introuvable.")
    return {"nom_fichier": fichier.filename, "contenu": fichier.read()}
