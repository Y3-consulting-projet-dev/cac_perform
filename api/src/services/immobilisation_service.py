"""
Service d'import du fichier des immobilisations.
Nouveau périmètre V2 — voir docs/PLAN_import_refonte.md §1c et §2.

Passe par le MÊME mécanisme d'aperçu et de mapping que la balance générale
(mapping_apercu_service) au lieu d'un parsing fixe à 3 colonnes — voir
balance_auxiliaire_service.py pour le détail du mécanisme (format « balance
auxiliaire Y3 » reconnu par nom d'en-tête notamment).

Plomberie uniquement. AUCUNE règle de rapprochement IPE-3 ici (le verrou
IPE/Module 1 est hors périmètre de ce chantier, voir CLAUDE.md). Ne modifie
pas api/src/model.py.

TODO(spec: CAC-IPE-01 §3) — colonnes exactes attendues pour un fichier
d'immobilisations (valeur brute, amortissements cumulés, valeur nette
comptable, durée/taux d'amortissement, compte 2xxx concerné...) non
confirmées dans le dépôt au-delà du format à 11 colonnes partagé avec les
balances auxiliaires. La convention de montant signé ne s'applique qu'au
repli « fichier à montant unique » (pas de colonnes débit/crédit séparées).
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.database import get_database
from src.services import mapping_apercu_service as apercu_service
from src.services import mapping_memorise_service
from src.services import fichiers_complementaires_service as fc_service
from src.services import controle_preliminaire_service as cp_service
from src.services import verrou_ipe_service

# Un fichier des immobilisations liste des BIENS : plusieurs biens partagent
# le même compte, donc le code du bien passe en premier (sinon le contrôle
# de doublons signalerait à tort chaque compte utilisé par plusieurs biens).
CLES_IDENTIFIANTES_POSSIBLES = ("code_bien", "numero_compte", "numero")


def _resoudre_mapping(fichier, id_client: str, logiciel_comptable: Optional[str],
                       mapping_force: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Même priorité que balance_auxiliaire_service._resoudre_mapping : explicite > mémorisé > aperçu auto."""
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


def importer_immobilisations(
    fichier,
    id_client: str,
    mission_id: str,
    annee: str,
    logiciel_comptable: Optional[str] = None,
    mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Importe le fichier des immobilisations et le stocke dans la collection
    Balance avec `type="immobilisations"` + `mission_id` (voir
    docs/PLAN_import_refonte.md §2).

    Réutilisée à l'identique pour un import à la création de mission ET pour
    un import/remplacement depuis l'écran de consultation d'une mission
    existante (aucun doublon de logique).

    Remplacement : si une version active existe déjà pour ce mission_id, elle
    est archivée (`actif=False`), jamais supprimée.
    """
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

    lignes_stockees = [{k: v for k, v in l.items() if k != "_ligne_excel"} for l in lignes_valides]

    fc_service.archiver_version_active(mission_id, "immobilisations")
    version = fc_service.prochaine_version(mission_id, "immobilisations")

    db = get_database()
    result = db.Balance.insert_one({
        "id_client": id_client,
        "mission_id": mission_id,
        "annee_balance": annee,
        "type": "immobilisations",
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

    nouveau_fichier_id = str(result.inserted_id)
    # Invalidation automatique si ce type de fichier avait servi à une
    # validation IPE positive (docs/PLAN_verrou_IPE.md) — no-op sinon.
    verrou_ipe_service.invalider_si_fichier_remplace(mission_id, "immobilisations", nouveau_fichier_id)

    return {
        "_id": nouveau_fichier_id,
        "type": "immobilisations",
        "version": version,
        "nb_lignes": len(lignes_stockees),
        "nb_lignes_ecartees": len(lignes_ecartees),
        "format_detecte": resolu["apercu"].get("format_propose"),
    }
