"""
Circularisation, sous-lot b (docs/PLAN_circularisation.md), maquette
4_Courriers : annuaire des coordonnées des tiers, bibliothèque de modèles
Word versionnés, état des tiers retenus et valeurs de fusion.

Sans nouvelle dépendance : les modèles sont rangés dans GridFS (pymongo) et
leurs champs `{{ champ }}` (syntaxe docxtpl) sont lus dans le XML du .docx.
La GÉNÉRATION des courriers (Word, PDF) et l'aperçu mis en page attendent la
décision sur les bibliothèques (PLAN §5, question transverse 3). L'envoi est
le sous-lot c.

Collections : `CirCoordonnees` (annuaire par client, une version par
modification), `CirModele` (versions de chaque modèle C1 à C5) ; actions au
journal `CirJournal` (module « Courriers »). Rien n'est supprimé.
"""
import io
import re
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services import circularisation_service as cir

COLLECTION_COORDONNEES = "CirCoordonnees"
COLLECTION_MODELE = "CirModele"
MODULE_JOURNAL = "Courriers"

# Modèles de la maquette 4_Courriers. TODO(spec: CAC-CIR-01) : modèles
# officiels du cabinet ; TODO(décision) : modèles communs au cabinet (choix
# provisoire) ou propres à chaque client ; qui peut les modifier (rôles).
MODELES = (
    {"code": "C1", "type_tiers": "clients", "libelle": "Clients"},
    {"code": "C2", "type_tiers": "fournisseurs", "libelle": "Fournisseurs"},
    {"code": "C3", "type_tiers": "avocats", "libelle": "Avocats"},
    {"code": "C4", "type_tiers": "bailleurs", "libelle": "Bailleurs"},
    {"code": "C5", "type_tiers": "banques", "libelle": "Banques"},
)
_MODELES = {m["code"]: m for m in MODELES}

# Champs de fusion que l'outil sait alimenter aujourd'hui, avec leur source.
# TODO(spec: CAC-CIR-01) : liste officielle des champs et de leur syntaxe.
# Manquent notamment : adresse de retour Y3, référence de mission, date du
# courrier, date d'arrêté, détail des postes (aucun grand livre importé).
CHAMPS_DISPONIBLES = {
    "entite": "Raison sociale de l'entité (fiche client)",
    "adresse_entite": "Adresse de l'entité (fiche client)",
    "exercice": "Exercice audité (mission)",
    "tiers_numero": "Numéro du tiers (balance auxiliaire)",
    "tiers_raison_sociale": "Raison sociale du tiers (annuaire, sinon libellé de la balance)",
    "tiers_adresse": "Adresse du tiers (annuaire)",
    "tiers_courriel": "Courriel du tiers (annuaire)",
    "tiers_contact": "Contact chez le tiers (annuaire)",
    "solde": "Solde du tiers dans les livres de l'entité (population photographiée)",
}

TAILLE_MAX_MODELE = 10 * 1024 * 1024  # TODO(décision) : limite provisoire
PARTIES_DOCX = re.compile(r"^word/(document|header\d*|footer\d*)\.xml$")
CHAMP_FUSION = re.compile(r"\{\{\s*([A-Za-z_][\w.]*)\s*\}\}")
COURRIEL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db():
    return get_database()


def _journaliser(mission_id: str, utilisateur_id: Optional[str], action: str, detail: str, **reference) -> None:
    _db()[cir.COLLECTION_JOURNAL].insert_one({
        "mission_id": mission_id, "horodatage": _maintenant(), "utilisateur_id": utilisateur_id,
        "module": MODULE_JOURNAL, "action": action, "detail": detail, "reference": reference,
    })


# --- Modèles (fonctions pures) ---------------------------------------------------

def champs_du_modele(contenu: bytes) -> List[str]:
    """
    Champs `{{ champ }}` d'un .docx, dans l'ordre d'apparition, sans doublon.
    Les balises XML sont retirées avant la recherche : Word découpe souvent un
    champ en plusieurs morceaux de texte. ValueError si le fichier n'est pas
    un document Word (.docx).
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(contenu))
    except zipfile.BadZipFile:
        raise ValueError("Le fichier n'est pas un document Word (.docx).")
    with archive:
        parties = sorted(n for n in archive.namelist() if PARTIES_DOCX.match(n))
        if "word/document.xml" not in parties:
            raise ValueError("Le fichier n'est pas un document Word (.docx).")
        texte = " ".join(re.sub(r"<[^>]+>", "", archive.read(n).decode("utf-8", "replace")) for n in parties)
    champs = []
    for champ in CHAMP_FUSION.findall(texte):
        if champ not in champs:
            champs.append(champ)
    return champs


def resume_modele(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    return {
        "_id": str(doc["_id"]), "version": doc["version"], "nom_fichier": doc["nom_fichier"],
        "importe_par": doc["importe_par"], "importe_le": doc["importe_le"], "champs": doc["champs"],
        "champs_inconnus": [c for c in doc["champs"] if c not in CHAMPS_DISPONIBLES],
    }


# --- Coordonnées et valeurs de fusion (fonctions pures) -----------------------------

def etat_tiers(coordonnees: Optional[Dict[str, Any]]) -> str:
    """« pret » (courriel), « courriel_manquant » (adresse seule), « coordonnees_manquantes »."""
    if coordonnees and coordonnees.get("courriel"):
        return "pret"
    if coordonnees and coordonnees.get("adresse"):
        return "courriel_manquant"
    return "coordonnees_manquantes"


def valeurs_fusion(entite: Dict[str, Any], tiers: Dict[str, Any], coordonnees: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Valeur de chaque champ disponible pour un tiers (None si inconnue)."""
    c = coordonnees or {}
    return {
        "entite": entite.get("entite"),
        "adresse_entite": entite.get("adresse"),
        "exercice": entite.get("exercice"),
        "tiers_numero": tiers["numero"],
        "tiers_raison_sociale": c.get("raison_sociale") or tiers.get("libelle"),
        "tiers_adresse": c.get("adresse"),
        "tiers_courriel": c.get("courriel"),
        "tiers_contact": c.get("contact"),
        "solde": tiers.get("solde"),
    }


# --- Lectures --------------------------------------------------------------------

def _mission(mission_id: str) -> Dict[str, Any]:
    try:
        oid = ObjectId(mission_id)
    except (InvalidId, TypeError):
        raise ValueError("Identifiant de mission invalide.")
    mission = _db()["Mission1"].find_one({"_id": oid}, {"id_client": 1, "annee_auditee": 1})
    if not mission:
        raise ValueError("Mission introuvable.")
    return mission


def _entite(mission: Dict[str, Any]) -> Dict[str, Any]:
    client = None
    try:
        client = _db()["Client_db"].find_one({"_id": ObjectId(str(mission.get("id_client")))},
                                             {"company_name": 1, "address": 1})
    except (InvalidId, TypeError):
        pass
    annee = mission.get("annee_auditee")
    if isinstance(annee, list):
        annee = annee[0] if annee else None
    return {"entite": (client or {}).get("company_name"), "adresse": (client or {}).get("address"), "exercice": annee}


def _modele_actif(code: str) -> Optional[Dict[str, Any]]:
    return _db()[COLLECTION_MODELE].find_one({"code": code, "actif": True})


def _coordonnees(id_client: str, type_tiers: str, numero: str) -> Optional[Dict[str, Any]]:
    return _db()[COLLECTION_COORDONNEES].find_one(
        {"id_client": id_client, "type_tiers": type_tiers, "numero": numero, "actif": True})


def lire_courriers(mission_id: str) -> Dict[str, Any]:
    """Bibliothèque des modèles, tiers retenus de chaque sélection active avec leur état et leurs valeurs de fusion."""
    mission = _mission(mission_id)
    entite = _entite(mission)
    id_client = str(mission.get("id_client"))
    modeles = [{**m, "actif": resume_modele(_modele_actif(m["code"]))} for m in MODELES]
    groupes = []
    for config in cir.TYPES_TIERS:
        selection = cir._selection_active(mission_id, config["cle"])
        if not selection:
            continue
        courantes = cir.decisions_courantes(selection["decisions"])
        tiers = []
        for t in selection["population"]["lignes"]:
            if not courantes.get(t["numero"], {}).get("retenu"):
                continue
            coord = _coordonnees(id_client, config["cle"], t["numero"])
            tiers.append({
                **t,
                "coordonnees": None if not coord else {k: coord.get(k) for k in (
                    "raison_sociale", "adresse", "courriel", "contact", "version", "modifie_par", "modifie_le")},
                "etat": etat_tiers(coord),
                "valeurs": valeurs_fusion(entite, t, coord),
            })
        modele = next(m for m in MODELES if m["type_tiers"] == config["cle"])
        groupes.append({"type_tiers": config["cle"], "libelle": config["libelle"], "code_modele": modele["code"],
                        "statut_selection": selection["statut"], "tiers": tiers})
    return {
        "entite": entite,
        "modeles": modeles,
        "champs_disponibles": CHAMPS_DISPONIBLES,
        "groupes": groupes,
        "generation_disponible": False,  # en attente des bibliothèques (PLAN §5)
    }


# --- Actions ---------------------------------------------------------------------

def enregistrer_coordonnees(mission_id: str, type_tiers: str, numero: str, donnees: Dict[str, Any],
                            utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """
    Coordonnées d'un tiers dans l'annuaire du client (réutilisées d'une
    mission à l'autre) : nouvelle version, la précédente est archivée.
    Le tiers doit appartenir à la population photographiée de la mission.
    """
    mission = _mission(mission_id)
    config = cir._type(type_tiers)
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, "Coordonnées du tiers")
    valeurs = {k: (str(donnees.get(k) or "").strip() or None) for k in ("raison_sociale", "adresse", "courriel", "contact")}
    if not valeurs["adresse"] and not valeurs["courriel"]:
        raise ValueError("Indiquez au moins une adresse postale ou un courriel.")
    if valeurs["courriel"] and not COURRIEL.match(valeurs["courriel"]):
        raise ValueError("Adresse de courriel invalide.")
    selection = cir._selection_active(mission_id, type_tiers)
    tiers = next((t for t in (selection or {}).get("population", {}).get("lignes", []) if t["numero"] == numero), None)
    if not tiers:
        raise ValueError(f"Tiers {numero} absent de la population {config['libelle'].lower()} de la mission.")
    id_client = str(mission.get("id_client"))
    db = _db()
    precedente = _coordonnees(id_client, type_tiers, numero)
    if precedente and all(precedente.get(k) == v for k, v in valeurs.items()):
        raise ValueError("Aucune modification.")
    if precedente:
        db[COLLECTION_COORDONNEES].update_one({"_id": precedente["_id"]}, {"$set": {"actif": False}})
    db[COLLECTION_COORDONNEES].insert_one({
        "id_client": id_client, "type_tiers": type_tiers, "numero": numero, **valeurs,
        "version": (precedente["version"] + 1) if precedente else 1, "actif": True,
        "modifie_par": utilisateur_id, "modifie_le": _maintenant(), "mission_id": mission_id,
    })
    _journaliser(mission_id, utilisateur_id, "Coordonnées du tiers enregistrées",
                 f"{config['libelle']} · {numero} · {tiers['libelle']}"
                 + (f" · {valeurs['courriel']}" if valeurs["courriel"] else " · sans courriel"),
                 type_tiers=type_tiers, numero=numero)
    return lire_courriers(mission_id)


def _gridfs():
    import gridfs
    return gridfs.GridFS(_db(), collection="cir_fichiers")


def importer_modele(mission_id: str, code: str, nom_fichier: Optional[str], contenu: bytes,
                    utilisateur_id: Optional[str]) -> Dict[str, Any]:
    """Nouvelle version d'un modèle Word : fichier dans GridFS, champs détectés, version précédente archivée."""
    _mission(mission_id)
    if code not in _MODELES:
        raise ValueError(f"Modèle inconnu : {code}.")
    utilisateur_id = cir._exiger_utilisateur(utilisateur_id, "Import d'un modèle")
    if not (nom_fichier or "").lower().endswith(".docx"):
        raise ValueError("Format attendu : document Word (.docx).")
    if len(contenu) > TAILLE_MAX_MODELE:
        raise ValueError("Fichier trop volumineux (10 Mo au plus).")
    champs = champs_du_modele(contenu)
    fichier_id = _gridfs().put(contenu, filename=nom_fichier, mission_id=mission_id, nature="modele_courrier")
    db = _db()
    precedent = _modele_actif(code)
    if precedent:
        db[COLLECTION_MODELE].update_one({"_id": precedent["_id"]}, {"$set": {"actif": False}})
    version = (precedent["version"] + 1) if precedent else 1
    db[COLLECTION_MODELE].insert_one({
        "code": code, "type_tiers": _MODELES[code]["type_tiers"], "version": version, "actif": True,
        "nom_fichier": nom_fichier, "fichier_id": fichier_id, "champs": champs,
        "importe_par": utilisateur_id, "importe_le": _maintenant(), "mission_id": mission_id,
    })
    inconnus = [c for c in champs if c not in CHAMPS_DISPONIBLES]
    _journaliser(mission_id, utilisateur_id, "Modèle importé",
                 f"{code} · {_MODELES[code]['libelle']} · {nom_fichier} · v{version} · {len(champs)} champ(s)"
                 + (f" dont inconnus : {', '.join(inconnus)}" if inconnus else ""), code=code)
    return lire_courriers(mission_id)


def lire_fichier_modele(modele_id: str) -> Dict[str, Any]:
    """Fichier Word d'une version de modèle (téléchargement)."""
    try:
        doc = _db()[COLLECTION_MODELE].find_one({"_id": ObjectId(modele_id)})
    except (InvalidId, TypeError):
        doc = None
    if not doc:
        raise ValueError("Modèle introuvable.")
    return {"nom_fichier": doc["nom_fichier"], "contenu": _gridfs().get(doc["fichier_id"]).read()}
