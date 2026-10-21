"""
Paramètres communs à toutes les missions (page C, maquette
docs/maquettes/7_Parametres.html) : CONSULTATION SEULE. Aucune valeur n'est
recopiée ici : chacune est lue là où le code la définit et l'utilise, avec
sa source (cahier des charges, spec à confirmer, décision provisoire).

Pas de modification possible tant qu'il n'y a pas d'authentification
(CLAUDE.md, point de sécurité connu) : aucune fonction d'écriture.

TODO(décision) : chaque rapprochement devra mémoriser les paramètres utilisés
(racines, tolérance, causes), pour qu'un changement de réglage ne modifie pas
les résultats des missions déjà traitées.
"""
from typing import Any, Dict

from src.services import rapprochement_ipe_service as rapprochement
from src.services import revue_ipe_service as revue
from src.services import verrou_ipe_service as verrou

# Catégories de source affichées à côté de chaque réglage.
CAHIER_DES_CHARGES = "cahier_des_charges"
SPEC_A_CONFIRMER = "spec_a_confirmer"
DECISION_PROVISOIRE = "decision_provisoire"

# Cadence de relance de la circularisation (maquettes 0_Barre_laterale et
# 5_Suivi_reponses) — SEUL endroit où elle est définie.
# TODO(spec: CAC-CIR-01) : cadence définitive et rôle de chaque échéance.
# Utilisée par le suivi des réponses (suivi_reponses_service) : échéances
# figées à l'envoi de chaque demande. Descriptions : maquette 5_Suivi_reponses.
CADENCE_RELANCES = (
    {"cle": "envoi", "libelle": "Envoi", "jour": 0, "description": "Envoi de la demande"},
    {"cle": "relance_1", "libelle": "Relance 1", "jour": 15, "description": "Relance 1"},
    {"cle": "relance_2", "libelle": "Relance 2", "jour": 30, "description": "Relance 2 et alerte du Manager"},
    {"cle": "alternative", "libelle": "Alternative", "jour": 45, "description": "Procédures alternatives requises"},
)

# Seuils d'écart PROPOSÉS par défaut par le cahier des charges §2.4, NON
# appliqués à ce jour : la tolérance utilisée reste
# rapprochement_ipe_service.TOLERANCE_ECART_IPE (0). Affichés pour information.
# TODO(spec: CAC-IPE-01 §2) : seuils définitifs et leur application.
SEUILS_PROPOSES_CAHIER_DES_CHARGES = {"absolu_fcfa": 500_000, "pourcentage": 0.5}

# Étapes du workflow jamais bloquées par le verrou (avant l'ouverture des
# cycles : CLAUDE.md, séquencement métier), affichées pour compléter la liste.
ETAPES_NON_VERROUILLEES = (
    {"etape": 3, "libelle": "Contrôle de cohérence"},
    {"etape": 4, "libelle": "Contrôle d’intangibilité"},
)


def _source(categorie: str, reference: str) -> Dict[str, str]:
    return {"categorie": categorie, "reference": reference}


def _racines_immobilisations() -> Dict[str, str]:
    brutes = sorted(rapprochement.RACINES_IMMOBILISATIONS_BRUTES)
    amortissements = rapprochement.RACINE_AMORTISSEMENTS
    return {
        "valeur": f"{brutes[0]} à {max(brutes[-1], amortissements)}",
        "detail": f"{brutes[0]} à {brutes[-1]} : valeurs brutes · {amortissements} : amortissements",
    }


def lire_parametres() -> Dict[str, Any]:
    """Réglages réellement utilisés par le code, avec leur source. Lecture seule."""
    racines = rapprochement.RACINES_COLLECTIFS
    return {
        "modifiable": False,
        "verrou": {
            "actif": verrou.verrou_actif(),
            "variable": "IPE_VERROU_ACTIF",
            "source": _source(DECISION_PROVISOIRE,
                              "Désactivé par défaut : ne pas l'activer en production tant que les droits "
                              "et la spec CAC-IPE-01 ne sont pas intégrés"),
        },
        "rapprochements": {
            "racines": [
                {"libelle": "Racine clients", "valeur": racines["clients"]},
                {"libelle": "Racine fournisseurs", "valeur": racines["fournisseurs"]},
            ],
            "racines_source": _source(CAHIER_DES_CHARGES,
                                      "Valeurs par défaut du cahier des charges §2.4 · à confirmer par CAC-IPE-01 §2"),
            "immobilisations": {"libelle": "Immobilisations", **_racines_immobilisations(),
                                "exclusion": "dépréciations (29) non prises en compte"},
            "immobilisations_source": _source(SPEC_A_CONFIRMER, "Périmètre IPE-3 à confirmer par CAC-IPE-01 §3"),
            "seuils": [
                {"libelle": "Seuil d'écart absolu (FCFA)", "valeur": rapprochement.TOLERANCE_ECART_IPE,
                 "applique": True, "propose_unite": "FCFA",
                 "propose": SEUILS_PROPOSES_CAHIER_DES_CHARGES["absolu_fcfa"]},
                {"libelle": "Seuil d'écart significatif (%)", "valeur": None, "applique": False,
                 "propose_unite": "%", "propose": SEUILS_PROPOSES_CAHIER_DES_CHARGES["pourcentage"]},
            ],
            "seuils_source": _source(DECISION_PROVISOIRE,
                                     "Aucune tolérance appliquée : tout écart non nul est un écart. "
                                     "Le cahier des charges §2.4 propose 0,5 % et 500 000 FCFA par défaut, "
                                     "non appliqués à ce jour · à confirmer par CAC-IPE-01 §2"),
        },
        "causes_ecart": {
            "valeurs": list(revue.CAUSES_ECART),
            "source": _source(CAHIER_DES_CHARGES, "Liste provisoire du cahier des charges §2.3.4 · à confirmer par la spec"),
        },
        "circularisation": {
            "cadence": [{"libelle": c["libelle"], "valeur": f"J+{c['jour']}" if c["jour"] else "J0"}
                        for c in CADENCE_RELANCES],
            "utilisee": True,
            "source": _source(SPEC_A_CONFIRMER, "Cadence à confirmer par CAC-CIR-01 · échéances figées à l'envoi de chaque demande"),
        },
        "etapes_verrou": {
            "bloquees": [{"etape": e["etape"], "libelle": e["libelle"]} for e in verrou.ETAPES_VERROUILLABLES],
            "non_bloquees": list(ETAPES_NON_VERROUILLEES),
            "source": _source(DECISION_PROVISOIRE, "Décision métier à confirmer par la direction"),
        },
    }
