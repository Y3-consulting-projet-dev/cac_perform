"""
Tests du circuit de revue du contrôle IPE (revue_ipe_service.py) — voir
docs/PLAN_verrou_IPE.md. Seule la fonction pure ecarts_non_qualifies est
testée ici (accès Mongo pour soumettre_pour_revue/demander_correction/
ajouter_remarque/..., comme pour les autres services de ce lot) ; le circuit
complet (soumettre -> demander correction -> corriger -> valider) est
vérifié en live via le serveur Flask local (voir le récap du commit).
"""
from src.services import revue_ipe_service as service


def _modules_avec_un_ecart(numero_compte="4011AAA", ok=False):
    return {
        "ipe_2_fournisseurs": {
            "statut": "ecart",
            "derniere_evaluation": {
                "detail_collectifs": [
                    {"numero_compte": numero_compte, "ok": ok},
                ],
            },
        },
    }


def test_ecarts_non_qualifies_detecte_un_collectif_sans_remarque():
    modules = _modules_avec_un_ecart()
    assert service.ecarts_non_qualifies(modules, []) == ["ipe_2_fournisseurs:4011AAA"]


def test_ecarts_non_qualifies_laisse_passer_un_collectif_commente():
    modules = _modules_avec_un_ecart()
    remarques = [{"module": "ipe_2_fournisseurs", "numero_compte": "4011AAA", "commentaire": "Écart analysé."}]
    assert service.ecarts_non_qualifies(modules, remarques) == []


def test_ecarts_non_qualifies_ignore_les_collectifs_ok():
    """Un collectif dont le rapprochement est OK (ok=True) n'est jamais un écart à qualifier, même si le module est "ecart" globalement."""
    modules = _modules_avec_un_ecart(ok=True)
    assert service.ecarts_non_qualifies(modules, []) == []


def test_ecarts_non_qualifies_ignore_les_modules_non_evaluables():
    modules = {
        "ipe_1_clients": {
            "statut": "non_evaluable",
            "derniere_evaluation": {"detail_collectifs": [{"numero_compte": "411", "ok": False}]},
        },
    }
    assert service.ecarts_non_qualifies(modules, []) == []


def test_ecarts_non_qualifies_ignore_une_remarque_generale():
    """Une remarque générale (module/numero_compte absents) ne qualifie aucun écart précis."""
    modules = _modules_avec_un_ecart()
    remarques = [{"module": None, "numero_compte": None, "commentaire": "Commentaire général sur le contrôle."}]
    assert service.ecarts_non_qualifies(modules, remarques) == ["ipe_2_fournisseurs:4011AAA"]


def test_ecarts_non_qualifies_ignore_une_remarque_sur_un_autre_collectif():
    modules = _modules_avec_un_ecart(numero_compte="4011AAA")
    remarques = [{"module": "ipe_2_fournisseurs", "numero_compte": "4081BBB", "commentaire": "Autre écart."}]
    assert service.ecarts_non_qualifies(modules, remarques) == ["ipe_2_fournisseurs:4011AAA"]


def test_ecarts_non_qualifies_plusieurs_collectifs_en_ecart():
    modules = {
        "ipe_2_fournisseurs": {
            "statut": "ecart",
            "derniere_evaluation": {
                "detail_collectifs": [
                    {"numero_compte": "4011AAA", "ok": False},
                    {"numero_compte": "4081BBB", "ok": False},
                ],
            },
        },
    }
    remarques = [{"module": "ipe_2_fournisseurs", "numero_compte": "4011AAA", "commentaire": "Traité."}]
    assert service.ecarts_non_qualifies(modules, remarques) == ["ipe_2_fournisseurs:4081BBB"]


def test_ecarts_non_qualifies_sans_modules():
    assert service.ecarts_non_qualifies(None, None) == []
    assert service.ecarts_non_qualifies({}, []) == []
