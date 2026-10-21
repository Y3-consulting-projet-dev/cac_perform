"""
Journal d'audit d'une mission (maquette docs/maquettes/6_Journal_audit.html) :
LECTURE SEULE. Assemble l'historique déjà enregistré par les autres services,
sans rien écrire ni recalculer :

- `Balance` (mission_id, type) : imports et retraits des fichiers
  complémentaires (balances auxiliaires, immobilisations) ;
- `Mission1.balance_generale_remplacements` : remplacements de la balance
  générale N et décisions sur les lignes de forme sous-total ;
- `Mission1.ipe.historique` : rapprochements, circuit de revue, remarques,
  qualifications, justifications, invalidations automatiques.

Ce qui n'est tracé nulle part (auteur d'un import de fichier complémentaire,
création de la mission, import V1, « importer quand même »…) n'est pas
reconstitué : voir le plan de la page B. Un utilisateur absent est affiché
« Non identifié ».

Seule `lire_journal` accède à la base (find_one/find) ; tout le reste est pur.
"""
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId

from src.utils.database import get_database
from src.services.revue_ipe_service import LIBELLES_FICHIERS
from src.services.balance_generale_service import TYPE_FICHIER as TYPE_BALANCE_GENERALE

MODULE_IMPORT = "Import"
MODULE_IPE = "Fiabilité IPE"
# Seuls les modules qui existent aujourd'hui (Sélection des tiers, Courriers,
# Suivi des réponses : à ajouter quand leurs écrans tracent leurs actions).
MODULE_SELECTION = "Sélection des tiers"  # = circularisation_service.MODULE_JOURNAL
MODULE_COURRIERS = "Courriers"  # = courriers_service.MODULE_JOURNAL
MODULE_SUIVI = "Suivi des réponses"  # = suivi_reponses_service.MODULE_JOURNAL
MODULES = (MODULE_IMPORT, MODULE_IPE, MODULE_SELECTION, MODULE_COURRIERS, MODULE_SUIVI)

NON_IDENTIFIE = "Non identifié"
# Valeur du filtre « Utilisateur » pour les entrées sans utilisateur enregistré.
FILTRE_NON_IDENTIFIE = "__non_identifie__"

TYPES_FICHIERS_COMPLEMENTAIRES = ("auxiliaire_client", "auxiliaire_fournisseur", "immobilisations")

LIBELLES_MODULES_IPE = {
    "ipe_1_clients": "IPE-1",
    "ipe_2_fournisseurs": "IPE-2",
    "ipe_3_immobilisations": "IPE-3",
}
LIBELLES_STATUTS_IPE = {
    "ok": "OK",
    "ecart": "écart",
    "non_evaluable": "non évaluable",
    "non_evalue": "non évalué",
}
LIBELLES_DECISIONS_SOUS_TOTAL = {"ecarter": "écartée", "garder": "gardée"}

COLONNES = ("Date", "Utilisateur", "Module", "Action", "Détail")
TAILLE_PAGE = 25


# --- Dates -------------------------------------------------------------------

def lire_horodatage(valeur: Any) -> Optional[datetime]:
    """ISO 8601 -> datetime UTC. Les horodatages sans fuseau (datetime.utcnow) sont en UTC."""
    if not valeur:
        return None
    try:
        dt = valeur if isinstance(valeur, datetime) else datetime.fromisoformat(str(valeur))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def heure_locale(dt: datetime, decalage_minutes: int) -> datetime:
    """Heure de l'utilisateur (décalage envoyé par le navigateur), sans fuseau."""
    return (dt + timedelta(minutes=decalage_minutes)).replace(tzinfo=None)


# --- Construction des entrées (fonctions pures) -------------------------------

def _entree(horodatage: Any, utilisateur: Any, module: str, action: str, detail: str) -> Dict[str, Any]:
    dt = lire_horodatage(horodatage)
    return {
        "horodatage": dt.isoformat() if dt else None,
        "utilisateur": (str(utilisateur).strip() or None) if utilisateur else None,
        "module": module,
        "action": action,
        "detail": detail,
    }


def _cite(texte: Any) -> Optional[str]:
    return f"« {texte} »" if texte else None


def _joindre(*morceaux: Optional[str]) -> str:
    return " · ".join(m for m in morceaux if m)


def entrees_fichiers(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Imports et retraits des fichiers complémentaires. La balance générale V2
    est traitée par `entrees_remplacements_balance_generale` (sa trace porte
    l'auteur et les décisions) : ignorée ici pour ne pas la compter deux fois.
    """
    entrees = []
    for doc in documents:
        if doc.get("type") not in TYPES_FICHIERS_COMPLEMENTAIRES:
            continue
        type_libelle = LIBELLES_FICHIERS.get(doc["type"], doc["type"])
        nom = doc.get("nom_fichier") or type_libelle
        version = f"v{doc['version']}" if doc.get("version") is not None else None
        nb_lignes = len(doc.get("balance") or [])
        entrees.append(_entree(
            doc.get("date_import"),
            doc.get("utilisateur_id"),  # absent aujourd'hui pour ces imports : « Non identifié »
            MODULE_IMPORT,
            "Fichier importé",
            _joindre(type_libelle[:1].upper() + type_libelle[1:], nom, version,
                     f"{nb_lignes} ligne{'s' if nb_lignes > 1 else ''}"),
        ))
        retrait = doc.get("retrait")
        if retrait:
            entrees.append(_entree(
                retrait.get("horodatage"),
                retrait.get("utilisateur_id"),
                MODULE_IMPORT,
                "Fichier retiré",
                _joindre(nom, version, _cite(retrait.get("commentaire"))),
            ))
    return entrees


def entrees_remplacements_balance_generale(remplacements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remplacements de la balance générale N et décisions sur les lignes de forme sous-total."""
    entrees = []
    for r in remplacements:
        entrees.append(_entree(
            r.get("horodatage"),
            r.get("utilisateur_id"),
            MODULE_IMPORT,
            "Balance générale remplacée",
            _joindre(r.get("nom_fichier"), f"version {r.get('version_remplacee')} → {r.get('nouvelle_version')}"),
        ))
        for d in r.get("decisions_sous_totaux") or []:
            entrees.append(_entree(
                r.get("horodatage"),
                r.get("utilisateur_id"),
                MODULE_IMPORT,
                "Décision sur un sous-total",
                _joindre(
                    f"compte {d.get('numero_compte')}",
                    d.get("libelle"),
                    f"ligne {LIBELLES_DECISIONS_SOUS_TOTAL.get(d.get('decision'), d.get('decision'))}",
                ),
            ))
    return entrees


def _compte(numero: Any) -> Optional[str]:
    return f"compte {numero}" if numero else None


def _detail_ipe(entree: Dict[str, Any], remarques: Dict[str, Dict[str, Any]]) -> Tuple[str, str]:
    """(action, détail) affichés pour une entrée de Mission1.ipe.historique."""
    action = entree.get("action")
    resultat = entree.get("resultat") or {}
    commentaire = _cite(entree.get("commentaire"))
    # Détail réduit au commentaire : « Commentaire « … » », comme la maquette.
    seul_commentaire = f"Commentaire {commentaire}" if commentaire else ""
    module = LIBELLES_MODULES_IPE.get(resultat.get("module")) if isinstance(resultat, dict) else None

    if action == "evaluation":
        statuts = [
            f"{LIBELLES_MODULES_IPE.get(m, m)} : {LIBELLES_STATUTS_IPE.get(s, s)}"
            for m, s in sorted((resultat or {}).items())
        ]
        return "Rapprochement lancé", _joindre(*statuts)
    if action == "validation_manager":
        return ("Validation" if resultat.get("validee") else "Invalidation"), seul_commentaire
    if action == "soumission_revue":
        return "Soumission pour revue", seul_commentaire
    if action == "demande_correction":
        return "Demande de correction", seul_commentaire
    if action == "qualification_ecart":
        return "Qualification d'un écart", _joindre(
            module, _compte(resultat.get("numero_compte")), resultat.get("cause"), commentaire)
    if action == "justification_non_evaluable":
        return "Justification d'un module non évaluable", _joindre(module, commentaire)
    if action == "remarque_ajoutee":
        libelle = "Demande de correction ajoutée" if resultat.get("type") == "demande_correction" else "Remarque ajoutée"
        return libelle, _joindre(module, _compte(resultat.get("numero_compte")), commentaire)
    if action == "remarque_repondue":
        reponse = f"réponse {commentaire}" if commentaire else None
        return "Réponse à une remarque", _joindre(_remarque_citee(resultat, remarques), reponse)
    if action in ("remarque_traitee", "remarque_rouverte"):
        libelle = "Remarque marquée traitée" if action == "remarque_traitee" else "Remarque rouverte"
        return libelle, _joindre(_remarque_citee(resultat, remarques))
    if action in ("invalidation_automatique", "invalidation_detectee_a_la_lecture"):
        return "Invalidation automatique", _joindre(entree.get("commentaire"))
    # Action inconnue de ce journal : affichée telle quelle plutôt que masquée.
    return str(action), seul_commentaire


def _remarque_citee(resultat: Dict[str, Any], remarques: Dict[str, Dict[str, Any]]) -> Optional[str]:
    remarque = remarques.get(str(resultat.get("remarque_id")))
    if not remarque:
        return None
    texte = remarque.get("commentaire") or ""
    court = texte if len(texte) <= 60 else texte[:57].rstrip() + "…"
    return _joindre(LIBELLES_MODULES_IPE.get(remarque.get("module")), _compte(remarque.get("numero_compte")),
                    f"remarque {_cite(court)}")


def entrees_ipe(historique: List[Dict[str, Any]], remarques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Entrées de Mission1.ipe.historique (rapprochements, circuit de revue, remarques…)."""
    par_id = {str(r.get("_id")): r for r in remarques or []}
    entrees = []
    for h in historique or []:
        action, detail = _detail_ipe(h, par_id)
        entrees.append(_entree(h.get("horodatage"), h.get("utilisateur_id"), MODULE_IPE, action, detail))
    return entrees


def entrees_circularisation(journal: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Journal de la circularisation (CirJournal) : action et détail déjà rédigés à l'enregistrement."""
    return [_entree(j.get("horodatage"), j.get("utilisateur_id"), j.get("module") or MODULE_SELECTION,
                    j.get("action"), j.get("detail")) for j in journal or []]


def assembler(mission: Dict[str, Any], documents: List[Dict[str, Any]],
              journal_circularisation: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Toutes les entrées de la mission, la plus récente d'abord."""
    ipe = mission.get("ipe") or {}
    entrees = (
        entrees_fichiers(documents)
        + entrees_remplacements_balance_generale(mission.get("balance_generale_remplacements") or [])
        + entrees_ipe(ipe.get("historique") or [], ipe.get("remarques") or [])
        + entrees_circularisation(journal_circularisation)
    )
    # Tri stable : à horodatage égal, l'ordre d'enregistrement est conservé.
    return sorted(entrees, key=lambda e: e["horodatage"] or "", reverse=True)


# --- Filtres et pagination (fonctions pures) -----------------------------------

def utilisateurs(entrees: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Options du filtre « Utilisateur » : utilisateurs présents, puis « Non identifié » s'il y a lieu."""
    noms = sorted({e["utilisateur"] for e in entrees if e["utilisateur"]}, key=str.lower)
    options = [{"valeur": n, "libelle": n} for n in noms]
    if any(not e["utilisateur"] for e in entrees):
        options.append({"valeur": FILTRE_NON_IDENTIFIE, "libelle": NON_IDENTIFIE})
    return options


def filtrer(
    entrees: List[Dict[str, Any]],
    module: Optional[str] = None,
    utilisateur: Optional[str] = None,
    du: Optional[date] = None,
    au: Optional[date] = None,
    decalage_minutes: int = 0,
) -> List[Dict[str, Any]]:
    """Filtres de la maquette ; « du » et « au » inclus, en date locale de l'utilisateur."""
    resultat = []
    for e in entrees:
        if module and e["module"] != module:
            continue
        if utilisateur == FILTRE_NON_IDENTIFIE and e["utilisateur"]:
            continue
        if utilisateur and utilisateur != FILTRE_NON_IDENTIFIE and e["utilisateur"] != utilisateur:
            continue
        if du or au:
            dt = lire_horodatage(e["horodatage"])
            if dt is None:
                continue
            jour = heure_locale(dt, decalage_minutes).date()
            if (du and jour < du) or (au and jour > au):
                continue
        resultat.append(e)
    return resultat


def paginer(entrees: List[Dict[str, Any]], page: int, taille: int = TAILLE_PAGE) -> Dict[str, Any]:
    nb_pages = max(1, -(-len(entrees) // taille))
    page = min(max(1, page), nb_pages)
    return {
        "entrees": entrees[(page - 1) * taille: page * taille],
        "page": page,
        "nb_pages": nb_pages,
        "nb_entrees": len(entrees),
    }


# --- Accès base (lecture seule) ------------------------------------------------

def lire_journal(mission_id: str) -> List[Dict[str, Any]]:
    """Toutes les entrées de la mission. Lecture seule : find_one / find uniquement."""
    try:
        oid = ObjectId(mission_id)
    except (InvalidId, TypeError):
        raise ValueError("Identifiant de mission invalide.")
    db = get_database()
    mission = db["Mission1"].find_one(
        {"_id": oid}, {"ipe.historique": 1, "ipe.remarques": 1, "balance_generale_remplacements": 1}
    )
    if not mission:
        raise ValueError("Mission introuvable.")
    documents = list(db["Balance"].find(
        {"mission_id": mission_id, "type": {"$in": list(TYPES_FICHIERS_COMPLEMENTAIRES)}},
        {"balance": 1, "type": 1, "nom_fichier": 1, "version": 1, "date_import": 1, "utilisateur_id": 1, "retrait": 1},
    ))
    journal_circularisation = list(db["CirJournal"].find({"mission_id": mission_id}))
    return assembler(mission, documents, journal_circularisation)


# --- Export Excel ------------------------------------------------------------

def exporter_excel(entrees: List[Dict[str, Any]], decalage_minutes: int = 0) -> bytes:
    """Classeur .xlsx des entrées données (déjà filtrées), dans l'ordre du journal."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Journal d'audit"
    ws.append(list(COLONNES))
    for cellule in ws[1]:
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = PatternFill("solid", fgColor="043C5D")  # blue-ycube (charte)
    for e in entrees:
        dt = lire_horodatage(e["horodatage"])
        ws.append([
            heure_locale(dt, decalage_minutes) if dt else None,
            e["utilisateur"] or NON_IDENTIFIE,
            e["module"],
            e["action"],
            e["detail"],
        ])
    for ligne in ws.iter_rows(min_row=2, max_col=1):
        ligne[0].number_format = "DD/MM/YYYY HH:MM"
    for colonne, largeur in zip("ABCDE", (18, 26, 16, 36, 90)):
        ws.column_dimensions[colonne].width = largeur
    for ligne in ws.iter_rows(min_row=2, min_col=5, max_col=5):
        ligne[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"

    flux = BytesIO()
    wb.save(flux)
    return flux.getvalue()
