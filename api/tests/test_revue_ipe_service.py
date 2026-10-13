"""
Tests du circuit de revue du contrôle IPE (revue_ipe_service.py) — voir
docs/PLAN_verrou_IPE.md. Seules les règles pures sont testées ici (accès
Mongo pour les actions, comme pour les autres services de ce lot) ; le
circuit complet est vérifié en live via le serveur Flask local.
"""
from src.services import revue_ipe_service as service


def _modules_avec_un_ecart(numero_compte="4011", ok=False):
    return {
        "ipe_2_fournisseurs": {
            "statut": "ecart",
            "derniere_evaluation": {"detail_collectifs": [{"numero_compte": numero_compte, "ok": ok}]},
        },
    }


def _qualification(numero_compte="4011", cause="Cut-off", commentaire="Facture reçue en janvier N+1."):
    return {"module": "ipe_2_fournisseurs", "numero_compte": numero_compte, "cause": cause, "commentaire": commentaire}


# ---------------------------------------------------------------------------
# Qualification d'un écart : cause de la liste + commentaire
# ---------------------------------------------------------------------------

def test_liste_des_causes_provisoire():
    assert service.CAUSES_ECART == ("Cut-off", "Erreur d'imputation", "En cours de justification", "Partie liée")


def test_ecart_sans_qualification_est_non_qualifie():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart(), []) == ["ipe_2_fournisseurs:4011"]


def test_ecart_qualifie_avec_cause_et_commentaire():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart(), [_qualification()]) == []


def test_une_cause_hors_liste_ne_qualifie_pas():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart(), [_qualification(cause="Autre")]) == [
        "ipe_2_fournisseurs:4011"
    ]


def test_un_commentaire_vide_ne_qualifie_pas():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart(), [_qualification(commentaire="   ")]) == [
        "ipe_2_fournisseurs:4011"
    ]


def test_une_qualification_sur_un_autre_collectif_ne_compte_pas():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart("4011"), [_qualification("4081")]) == [
        "ipe_2_fournisseurs:4011"
    ]


def test_collectif_ok_et_modules_non_evaluables_ignores():
    assert service.ecarts_non_qualifies(_modules_avec_un_ecart(ok=True), []) == []
    non_evaluable = {
        "ipe_1_clients": {
            "statut": "non_evaluable",
            "derniere_evaluation": {"detail_collectifs": [{"numero_compte": "411", "ok": False}]},
        },
    }
    assert service.ecarts_non_qualifies(non_evaluable, []) == []


def test_ecarts_non_qualifies_sans_modules():
    assert service.ecarts_non_qualifies(None, None) == []


# ---------------------------------------------------------------------------
# Demandes de correction / remarques informatives
# ---------------------------------------------------------------------------

def test_seule_une_demande_de_correction_non_traitee_est_bloquante():
    remarques = [
        {"_id": "a", "type": "information", "traitee": False},
        {"_id": "b", "type": "demande_correction", "traitee": True},
        {"_id": "c", "type": "demande_correction", "traitee": False},
    ]
    assert [r["_id"] for r in service.demandes_correction_non_traitees(remarques)] == ["c"]


def test_marquage_reserve_a_l_auteur():
    remarque = {"utilisateur_id": "Awa Koné", "reponse": {"commentaire": "Corrigé."}}
    assert service.refus_marquage_remarque(remarque, "Jean Kouassi", True) is not None
    assert service.refus_marquage_remarque(remarque, "Awa Koné", True) is None


def test_marquage_traitee_exige_la_reponse_de_l_auditeur():
    remarque = {"utilisateur_id": "Awa Koné", "reponse": None}
    refus = service.refus_marquage_remarque(remarque, "Awa Koné", True)
    assert refus is not None and "réponse" in refus


def test_rouvrir_n_exige_pas_de_reponse_mais_reste_reserve_a_l_auteur():
    remarque = {"utilisateur_id": "Awa Koné", "reponse": None}
    assert service.refus_marquage_remarque(remarque, "Awa Koné", False) is None
    assert service.refus_marquage_remarque(remarque, "Jean Kouassi", False) is not None


# ---------------------------------------------------------------------------
# Modules non évaluables : justification écrite par module
# ---------------------------------------------------------------------------

def test_module_non_evaluable_sans_justification():
    modules = {"ipe_1_clients": {"statut": "non_evaluable"}, "ipe_2_fournisseurs": {"statut": "ok"}}
    assert service.modules_non_evaluables_sans_justification(modules, {}) == ["ipe_1_clients"]


def test_module_non_evaluable_justifie():
    modules = {"ipe_1_clients": {"statut": "non_evaluable"}}
    justifications = {"ipe_1_clients": {"commentaire": "Pas de balance auxiliaire clients : client sans créances."}}
    assert service.modules_non_evaluables_sans_justification(modules, justifications) == []


# ---------------------------------------------------------------------------
# Règle globale de validation
# ---------------------------------------------------------------------------

def _etat_validable():
    return {
        "modules": {
            **_modules_avec_un_ecart(),
            "ipe_1_clients": {"statut": "non_evaluable"},
        },
        "qualifications_ecarts": [_qualification()],
        "remarques": [{"type": "demande_correction", "traitee": True}],
        "justifications_non_evaluables": {"ipe_1_clients": {"commentaire": "Justification écrite du module."}},
    }


def test_validation_permise_quand_tout_est_regle():
    assert service.refus_validation(_etat_validable()) is None


def test_validation_refusee_si_ecart_non_qualifie():
    etat = _etat_validable()
    etat["qualifications_ecarts"] = []
    assert "non qualifié" in service.refus_validation(etat)


def test_validation_refusee_si_demande_de_correction_non_traitee():
    etat = _etat_validable()
    etat["remarques"] = [{"type": "demande_correction", "traitee": False}]
    assert "demande(s) de correction" in service.refus_validation(etat)


def test_validation_permise_malgre_une_remarque_informative_non_traitee():
    etat = _etat_validable()
    etat["remarques"].append({"type": "information", "traitee": False})
    assert service.refus_validation(etat) is None


def test_validation_refusee_si_module_non_evaluable_non_justifie():
    etat = _etat_validable()
    etat["justifications_non_evaluables"] = {}
    assert "ipe_1_clients" in service.refus_validation(etat)


# ---------------------------------------------------------------------------
# Décisions du 2026-10-13 : utilisateur identifié, justification dès la soumission
# ---------------------------------------------------------------------------

def test_marquage_refuse_a_un_utilisateur_non_identifie():
    """Plus de règle « traitable seulement par un non identifié »."""
    remarque_sans_auteur = {"utilisateur_id": None, "reponse": {"commentaire": "Corrigé."}}
    assert service.refus_marquage_remarque(remarque_sans_auteur, None, True) is not None
    assert service.refus_marquage_remarque(remarque_sans_auteur, None, False) is not None
    remarque = {"utilisateur_id": "Awa Koné", "reponse": {"commentaire": "Corrigé."}}
    assert service.refus_marquage_remarque(remarque, None, True) is not None


def test_demande_de_correction_exige_un_utilisateur_identifie():
    assert service.refus_demande_correction_sans_auteur(None) is not None
    assert service.refus_demande_correction_sans_auteur("") is not None
    assert service.refus_demande_correction_sans_auteur("Manager M") is None


def test_soumission_exige_la_justification_des_modules_non_evaluables():
    etat = _etat_validable()
    assert service.refus_soumission(etat) is None
    etat["justifications_non_evaluables"] = {}
    assert "ipe_1_clients" in service.refus_soumission(etat)


def test_soumission_exige_toujours_la_qualification_des_ecarts():
    etat = _etat_validable()
    etat["qualifications_ecarts"] = []
    assert "non qualifié" in service.refus_soumission(etat)


def test_soumission_ne_depend_pas_des_demandes_de_correction():
    """Une demande non traitée bloque la validation, pas la re-soumission (l'auditeur re-soumet après correction)."""
    etat = _etat_validable()
    etat["remarques"] = [{"type": "demande_correction", "traitee": False}]
    assert service.refus_soumission(etat) is None
    assert service.refus_validation(etat) is not None
