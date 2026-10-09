"""
Service d'import des balances auxiliaires (clients / fournisseurs).
Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md §1b et §2.

Passe par le MÊME mécanisme d'aperçu et de mapping que la balance générale
(mapping_apercu_service) au lieu d'un parsing fixe à 3 colonnes : reconnaît
notamment le format « balance auxiliaire Y3 » à 11 colonnes par le NOM de ses
en-têtes (CODE_ENTITE, NUMERO_COMPTE, LIBELLE_COMPTE, puis les paires
ouverture/mouvement/solde mouvement/solde final en débit et crédit).

Plomberie uniquement. AUCUNE règle de rapprochement IPE ici (le verrou
IPE/Module 1 est hors périmètre de ce chantier, voir CLAUDE.md). Ne modifie
pas api/src/model.py ni les documents Balance de type "generale" existants.

TODO(spec: CAC-IPE-01) — identifiant réel du tiers (NUMERO_COMPTE seul ?
CODE_ENTITE + NUMERO_COMPTE ?) non confirmé : les deux sont stockés tels quels,
sans décision prise ici. La convention de montant signé (positif=débit,
négatif=crédit) ne s'applique qu'au repli « fichier à montant unique » (pas
de colonnes débit/crédit séparées) — voir fichiers_complementaires_service.py.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.database import get_database
from src.services import mapping_apercu_service as apercu_service
from src.services import mapping_memorise_service
from src.services import fichiers_complementaires_service as fc_service
from src.services import controle_preliminaire_service as cp_service

TYPES_VALIDES = ("client", "fournisseur")

# Ordre de préférence pour identifier une ligne (détection de doublons) :
# le premier champ présent dans les lignes est utilisé.
CLES_IDENTIFIANTES_POSSIBLES = ("numero_compte", "numero_tiers", "numero")


def _resoudre_mapping(fichier, id_client: str, logiciel_comptable: Optional[str],
                       mapping_force: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """
    Résout le mapping à utiliser, par ordre de priorité :
    1. mapping explicitement fourni par l'appelant ;
    2. mapping mémorisé pour (id_client, logiciel_comptable), s'il existe ;
    3. mapping proposé automatiquement par l'aperçu (détection par nom
       d'en-tête, voir mapping_apercu_service).
    Renvoie aussi l'aperçu (colonnes détectées) pour trace/contrôles.
    """
    apercu = apercu_service.generer_apercu_mapping(fichier)

    if mapping_force:
        return {"mapping": mapping_force, "apercu": apercu}

    if logiciel_comptable:
        memorise = mapping_memorise_service.recuperer_mapping(id_client, logiciel_comptable)
        if memorise and memorise.get("mapping"):
            return {"mapping": memorise["mapping"], "apercu": apercu}

    return {"mapping": apercu["mapping_propose"], "apercu": apercu}


def _cle_identifiante(lignes: List[Dict[str, Any]]) -> Optional[str]:
    if not lignes:
        return None
    for cle in CLES_IDENTIFIANTES_POSSIBLES:
        if cle in lignes[0]:
            return cle
    return None


def importer_balance_auxiliaire(
    fichier,
    type_auxiliaire: str,
    id_client: str,
    mission_id: str,
    annee: str,
    logiciel_comptable: Optional[str] = None,
    mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Importe une balance auxiliaire (clients ou fournisseurs) et la stocke
    dans la collection Balance avec un champ `type` dédié + `mission_id`
    (voir docs/PLAN_import_refonte.md §2). N'altère aucun document Balance
    existant de type "generale".

    Réutilisée à l'identique pour un import à la création de mission ET pour
    un import/remplacement depuis l'écran de consultation d'une mission
    existante (aucun doublon de logique).

    `logiciel_comptable` / `mapping` sont optionnels : sans eux, le mapping
    proposé automatiquement par l'aperçu est utilisé (voir `_resoudre_mapping`).

    Remplacement : si une version active existe déjà pour
    (mission_id, type_auxiliaire), elle est archivée (`actif=False`), jamais
    supprimée — l'historique reste consultable via
    fichiers_complementaires_service.lister_historique.
    """
    if type_auxiliaire not in TYPES_VALIDES:
        raise ValueError(f"type_auxiliaire doit être 'client' ou 'fournisseur' (reçu: '{type_auxiliaire}')")

    integrite = cp_service.controler_integrite(fichier)
    if not integrite["ok"]:
        raise ValueError("; ".join(integrite["erreurs"]) or "Fichier invalide")

    resolu = _resoudre_mapping(fichier, id_client, logiciel_comptable, mapping)
    mapping_utilise = resolu["mapping"]

    lignes_brutes = apercu_service.lire_lignes_selon_mapping(fichier, mapping_utilise)
    if not lignes_brutes:
        raise ValueError("Aucune ligne exploitable trouvée dans le fichier (vérifiez le mapping de colonnes)")

    cle_identifiante = _cle_identifiante(lignes_brutes)
    lignes_valides, lignes_ecartees = cp_service.separer_lignes_sans_identifiant(lignes_brutes, cle_identifiante)
    if not lignes_valides:
        raise ValueError("Aucune ligne avec un identifiant de compte trouvée dans le fichier")

    doublons = cp_service.controler_doublons(lignes_valides, cle=cle_identifiante) if cle_identifiante else {"ok": True, "doublons": []}
    bouclage_total = cp_service.controler_bouclage_total(lignes_valides, lignes_ecartees, cle_identifiante)
    bouclage_ligne = cp_service.controler_bouclage_ligne(lignes_valides)

    # _ligne_excel est un champ technique de traçabilité (voir
    # mapping_apercu_service.lire_lignes_selon_mapping) : il ne fait pas
    # partie des données métier stockées.
    lignes_stockees = [{k: v for k, v in l.items() if k != "_ligne_excel"} for l in lignes_valides]

    type_stocke = f"auxiliaire_{type_auxiliaire}"
    fc_service.archiver_version_active(mission_id, type_stocke)
    version = fc_service.prochaine_version(mission_id, type_stocke)

    db = get_database()
    result = db.Balance.insert_one({
        "id_client": id_client,
        "mission_id": mission_id,
        "annee_balance": annee,
        "type": type_stocke,
        "balance": lignes_stockees,
        "nom_fichier": getattr(fichier, "filename", None),
        "date_import": datetime.utcnow().isoformat(),
        "version": version,
        "actif": True,
        "mapping_utilise": mapping_utilise,
        "format_detecte": resolu["apercu"].get("format_propose"),
        "controles_preliminaires": {
            "integrite": integrite,
            "doublons": doublons,
            "lignes_ecartees": {"nb": len(lignes_ecartees), "lignes": lignes_ecartees},
            "bouclage_total": bouclage_total,
            "bouclage_ligne": bouclage_ligne,
        },
    })
    return {
        "_id": str(result.inserted_id),
        "type": type_stocke,
        "version": version,
        "nb_lignes": len(lignes_stockees),
        "nb_lignes_ecartees": len(lignes_ecartees),
        "format_detecte": resolu["apercu"].get("format_propose"),
    }
