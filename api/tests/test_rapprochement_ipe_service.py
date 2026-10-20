"""
Tests de rapprochement_ipe_service.rapprocher_famille : rapprochement compte
collectif par compte collectif entre balance générale et fichier auxiliaire.
Voir docs/PLAN_verrou_IPE.md §4, §7.

Jeu de données FICTIF, construit directement en Python (pas de classeur
Excel nécessaire : rapprocher_famille travaille sur des lignes déjà
parsées). Seule la fonction pure est testée ici ; evaluer_ipe/valider_fiabilite
(accès Mongo) ne le sont pas, comme pour les autres services de ce lot.
"""
from datetime import datetime, timedelta, timezone

from src.services import rapprochement_ipe_service as service


def test_cas_equilibre_un_seul_collectif():
    lignes_bg = [{"numero_compte": "411", "solde_reel": 300.0}]
    lignes_aux = [
        {"numero_compte": "4111001", "solde_final_debit": 100.0, "solde_final_credit": 0.0},
        {"numero_compte": "4111002", "solde_final_debit": 200.0, "solde_final_credit": 0.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "411", "numero_compte")

    assert resultat["ok"] is True
    assert len(resultat["collectifs"]) == 1
    assert resultat["collectifs"][0]["numero_compte"] == "411"
    assert resultat["collectifs"][0]["ecart"] == 0.0
    assert resultat["orphelins_auxiliaire"] == []
    assert resultat["orphelins_balance_generale"] == []


def test_cas_en_ecart_construit():
    lignes_bg = [{"numero_compte": "411", "solde_reel": 300.0}]
    lignes_aux = [
        {"numero_compte": "4111001", "solde_final_debit": 100.0, "solde_final_credit": 0.0},
        # Écart introduit : 250 au lieu de 200.
        {"numero_compte": "4111002", "solde_final_debit": 250.0, "solde_final_credit": 0.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "411", "numero_compte")

    assert resultat["ok"] is False
    assert resultat["collectifs"][0]["ecart"] == -50.0
    assert resultat["collectifs"][0]["ok"] is False


def test_detection_orphelins_des_deux_cotes():
    """
    Collectif "402" sans aucun tiers -> orphelin côté balance générale.
    Tiers "4099XYZ" ne correspond à aucun collectif -> orphelin côté auxiliaire.
    """
    lignes_bg = [
        {"numero_compte": "401", "solde_reel": 100.0},
        {"numero_compte": "402", "solde_reel": 0.0},
    ]
    lignes_aux = [
        {"numero_compte": "4011AAA", "solde_final_debit": 100.0, "solde_final_credit": 0.0},
        {"numero_compte": "4099XYZ", "solde_final_debit": 50.0, "solde_final_credit": 0.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")

    assert resultat["orphelins_balance_generale"] == ["402"]
    assert [o["numero"] for o in resultat["orphelins_auxiliaire"]] == ["4099XYZ"]
    assert resultat["ok"] is False


def test_rattachement_par_prefixe_le_plus_long():
    """
    Deux collectifs emboîtés ("401" et "4011") : un tiers "4011AAA" doit se
    rattacher au plus spécifique ("4011"), jamais être compté sous "401" en
    plus (pas de double comptage).
    """
    lignes_bg = [
        {"numero_compte": "401", "solde_reel": 500.0},
        {"numero_compte": "4011", "solde_reel": 100.0},
    ]
    lignes_aux = [
        {"numero_compte": "4011AAA", "solde_final_debit": 100.0, "solde_final_credit": 0.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")
    par_collectif = {c["numero_compte"]: c for c in resultat["collectifs"]}

    assert par_collectif["4011"]["nb_tiers_rattaches"] == 1
    assert par_collectif["4011"]["ecart"] == 0.0
    # "401" n'a reçu aucun tiers (le seul tiers est allé au collectif plus spécifique).
    assert par_collectif["401"]["nb_tiers_rattaches"] == 0
    assert "401" in resultat["orphelins_balance_generale"]


def test_ligne_non_calculable_ne_fait_jamais_planter_le_calcul():
    """
    Une ligne auxiliaire sans aucune colonne de montant exploitable (ex.
    mapping incomplet, TODO(spec) non résolu) ne doit jamais être traitée
    comme valant 0 silencieusement : elle est isolée dans lignes_non_calculables,
    et le résultat global n'est jamais "ok" tant qu'elle n'est pas résolue.
    """
    lignes_bg = [{"numero_compte": "401", "solde_reel": 100.0}]
    lignes_aux = [
        {"numero_compte": "4011AAA", "solde_final_debit": 100.0, "solde_final_credit": 0.0},
        {"numero_compte": "4011BBB"},  # aucune colonne de montant
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "401", "numero_compte")

    assert [l["numero"] for l in resultat["lignes_non_calculables"]] == ["4011BBB"]
    # Le collectif lui-même boucle (100 == 100), mais le résultat global reste
    # prudent tant que la ligne non calculable n'est pas résolue.
    assert resultat["collectifs"][0]["ok"] is True
    assert resultat["ok"] is False


def test_aucun_collectif_trouve_nest_jamais_ok():
    """Famille absente de la balance générale : rien à comparer -> jamais "ok" silencieusement."""
    resultat = service.rapprocher_famille([], [], "411", "numero_compte")
    assert resultat["collectifs"] == []
    assert resultat["ok"] is False


# ---------------------------------------------------------------------------
# choisir_balance_generale / resoudre_annee_auditee — sélection par année
# auditée (N), jamais par position dans Mission1.balances (correction).
# ---------------------------------------------------------------------------

def test_choisir_balance_generale_selectionne_lannee_n():
    candidats = [
        {"_id": "bal_n1", "annee_balance": 2024},
        {"_id": "bal_n", "annee_balance": 2025},
    ]
    resultat = service.choisir_balance_generale(candidats, 2025)
    assert resultat["_id"] == "bal_n"


def test_choisir_balance_generale_accepte_annee_en_chaine():
    """annee_balance peut être stockée en int ou en str selon le chemin d'import : les deux doivent matcher."""
    candidats = [{"_id": "bal_n", "annee_balance": "2025"}]
    resultat = service.choisir_balance_generale(candidats, 2025)
    assert resultat["_id"] == "bal_n"


def test_choisir_balance_generale_echoue_si_introuvable():
    candidats = [{"_id": "bal_n1", "annee_balance": 2024}]
    try:
        service.choisir_balance_generale(candidats, 2025)
        assert False, "devait lever ValueError"
    except ValueError as e:
        assert "introuvable" in str(e)


def test_choisir_balance_generale_echoue_si_ambigu():
    """Deux documents distincts portant la même année auditée : jamais de choix au hasard."""
    candidats = [
        {"_id": "bal_a", "annee_balance": 2025},
        {"_id": "bal_b", "annee_balance": 2025},
    ]
    try:
        service.choisir_balance_generale(candidats, 2025)
        assert False, "devait lever ValueError"
    except ValueError as e:
        assert "ambigu" in str(e).lower()


def test_resoudre_annee_auditee_echoue_si_absente():
    try:
        service.resoudre_annee_auditee(None)
        assert False, "devait lever ValueError"
    except ValueError:
        pass


def test_resoudre_annee_auditee_accepte_une_chaine():
    assert service.resoudre_annee_auditee("2025") == 2025


# ---------------------------------------------------------------------------
# Invalidation automatique après remplacement d'un fichier utilisé par une
# validation positive (verrou_ipe_service.decider_invalidation) — scénario :
# valider, réimporter l'auxiliaire, la mission doit être de nouveau bloquée.
# ---------------------------------------------------------------------------

def test_invalidation_apres_remplacement_du_fichier_valide():
    from src.services import verrou_ipe_service

    etat_valide = {
        "verrou_applicable": True,
        "ipe_fiabilite_validee": True,
        "modules": {"ipe_2_fournisseurs": {"statut": "ok"}},
        "fichiers_references": {
            "balance_generale": {"_id": "bal_n", "annee_balance": 2025},
            "auxiliaire_fournisseur": {"_id": "aux_v1", "version": 1},
        },
    }
    # Mission bloquée tant que la fiabilité n'est pas validée, mais ici elle
    # vient d'être validée -> pas bloquée avant le remplacement du fichier.
    assert verrou_ipe_service.mission_est_bloquee(etat_valide) is False

    decision = verrou_ipe_service.decider_invalidation(etat_valide, "auxiliaire_fournisseur", "aux_v2")
    assert decision is not None
    assert decision["updates"]["ipe.ipe_fiabilite_validee"] is False
    assert decision["updates"]["ipe.modules.ipe_2_fournisseurs.statut"] == "non_evalue"

    # Applique la décision sur une copie de l'état pour vérifier le blocage effectif.
    etat_apres = dict(etat_valide)
    etat_apres["ipe_fiabilite_validee"] = False
    assert verrou_ipe_service.mission_est_bloquee(etat_apres) is True


def test_invalidation_ne_declenche_rien_si_fichier_jamais_reference():
    from src.services import verrou_ipe_service

    etat = {"fichiers_references": {}}
    assert verrou_ipe_service.decider_invalidation(etat, "auxiliaire_client", "aux_v1") is None


def test_invalidation_ne_declenche_rien_si_meme_fichier():
    from src.services import verrou_ipe_service

    etat = {"fichiers_references": {"immobilisations": {"_id": "immo_v1", "version": 1}}}
    assert verrou_ipe_service.decider_invalidation(etat, "immobilisations", "immo_v1") is None


# ---------------------------------------------------------------------------
# normaliser_compte_collectif / rattachement par préfixe après normalisation
# — comptes de la balance générale complétés à 8 chiffres par des zéros de
# fin (ex. 40110000), jamais rattachables aux tiers (ex. 4011TO) sans retirer
# ces zéros au préalable.
# ---------------------------------------------------------------------------

def test_normaliser_compte_collectif_retire_les_zeros_de_fin():
    assert service.normaliser_compte_collectif("40110000") == "4011"
    assert service.normaliser_compte_collectif("41110000") == "4111"


def test_normaliser_compte_collectif_ne_touche_pas_un_numero_sans_zero_de_fin():
    assert service.normaliser_compte_collectif("4011TO") == "4011TO"
    assert service.normaliser_compte_collectif("401") == "401"


def test_normaliser_compte_collectif_cas_limite_que_des_zeros():
    """Ne renvoie jamais une chaîne vide, même pour un numéro entièrement composé de zéros."""
    assert service.normaliser_compte_collectif("00000000") == "00000000"


def test_rattachement_apres_normalisation_comptes_8_chiffres():
    """
    Reproduit le cas réel rencontré sur la mission de test : balance générale
    sur 8 chiffres (40110000), tiers de l'auxiliaire au format court
    (4011TO). Sans normalisation, aucun tiers n'est jamais rattaché.
    """
    lignes_bg = [{"numero_compte": "40110000", "solde_reel": -1000.0}]
    lignes_aux = [
        {"numero_compte": "4011TO", "solde_final_debit": 0.0, "solde_final_credit": 1000.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")

    assert resultat["collectifs"][0]["numero_compte"] == "4011"
    assert resultat["collectifs"][0]["nb_tiers_rattaches"] == 1
    assert resultat["collectifs"][0]["ecart"] == 0.0
    assert resultat["ok"] is True
    assert resultat["orphelins_balance_generale"] == []


def test_rattachement_apres_normalisation_plusieurs_collectifs_8_chiffres():
    """Deux comptes collectifs sur 8 chiffres, chacun avec son propre tiers rattaché après normalisation."""
    lignes_bg = [
        {"numero_compte": "40110000", "solde_reel": -500.0},
        {"numero_compte": "40120000", "solde_reel": -300.0},
    ]
    lignes_aux = [
        {"numero_compte": "4011TO", "solde_final_debit": 0.0, "solde_final_credit": 500.0},
        {"numero_compte": "4012AB", "solde_final_debit": 0.0, "solde_final_credit": 300.0},
    ]

    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")
    par_collectif = {c["numero_compte"]: c for c in resultat["collectifs"]}

    assert set(par_collectif.keys()) == {"4011", "4012"}
    assert all(c["ok"] for c in resultat["collectifs"])
    assert resultat["ok"] is True


# ---------------------------------------------------------------------------
# determiner_statut_module — fichier complémentaire absent ou aucun compte
# collectif trouvé -> "non_evaluable", jamais "ecart".
# ---------------------------------------------------------------------------

def test_statut_non_evaluable_si_fichier_complementaire_absent():
    """
    Avant la correction, un fichier auxiliaire absent (balance générale avec
    des collectifs, aucun tiers côté auxiliaire) produisait un "écart" — ce
    n'est pas un écart réel, juste l'absence de données à comparer.
    """
    lignes_bg = [{"numero_compte": "401", "solde_reel": -1000.0}]
    resultat = service.rapprocher_famille(lignes_bg, [], "40", None)

    decision = service.determiner_statut_module(resultat, fichier_auxiliaire_absent=True)

    assert decision["statut"] == "non_evaluable"
    assert decision["motif_non_evaluable"] == "fichier_complementaire_absent"


def test_statut_non_evaluable_si_aucun_collectif_trouve():
    resultat = service.rapprocher_famille([], [], "411", "numero_compte")
    decision = service.determiner_statut_module(resultat, fichier_auxiliaire_absent=False)
    assert decision["statut"] == "non_evaluable"
    assert decision["motif_non_evaluable"] == "aucun_compte_collectif_trouve"


def test_statut_ecart_reel_reste_ecart():
    lignes_bg = [{"numero_compte": "401", "solde_reel": -1000.0}]
    lignes_aux = [{"numero_compte": "4011AAA", "solde_final_debit": 0.0, "solde_final_credit": 800.0}]
    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")

    decision = service.determiner_statut_module(resultat, fichier_auxiliaire_absent=False)

    assert decision["statut"] == "ecart"
    assert decision["motif_non_evaluable"] is None


def test_statut_ok_reste_ok():
    lignes_bg = [{"numero_compte": "401", "solde_reel": -1000.0}]
    lignes_aux = [{"numero_compte": "4011AAA", "solde_final_debit": 0.0, "solde_final_credit": 1000.0}]
    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")

    decision = service.determiner_statut_module(resultat, fichier_auxiliaire_absent=False)

    assert decision["statut"] == "ok"


# ---------------------------------------------------------------------------
# Convention de signe (débit - crédit) harmonisée entre balance générale et
# auxiliaire, des deux côtés — vérification explicite demandée.
# ---------------------------------------------------------------------------

def test_convention_de_signe_coherente_cote_debiteur():
    """Compte collectif débiteur net (ex. 411 clients) et tiers débiteur équivalent -> écart nul."""
    lignes_bg = [{"numero_compte": "411", "solde_reel": 500.0}]
    lignes_aux = [{"numero_compte": "4111AAA", "solde_final_debit": 500.0, "solde_final_credit": 0.0}]
    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "411", "numero_compte")
    assert resultat["collectifs"][0]["ecart"] == 0.0


def test_convention_de_signe_coherente_cote_crediteur():
    """Compte collectif créditeur net (ex. 401 fournisseurs) et tiers créditeur équivalent -> écart nul."""
    lignes_bg = [{"numero_compte": "401", "solde_reel": -500.0}]
    lignes_aux = [{"numero_compte": "4011AAA", "solde_final_debit": 0.0, "solde_final_credit": 500.0}]
    resultat = service.rapprocher_famille(lignes_bg, lignes_aux, "401", "numero_compte")
    assert resultat["collectifs"][0]["ecart"] == 0.0


# ---------------------------------------------------------------------------
# validation_identique_trop_recente — garde-fou double clic (refuse côté
# backend deux validations/invalidations identiques à quelques secondes
# d'intervalle), docs/PLAN_verrou_IPE.md.
# ---------------------------------------------------------------------------

def test_validation_identique_trop_recente_bloque_le_double_clic():
    maintenant = datetime.now(timezone.utc)
    historique = [{
        "horodatage": (maintenant - timedelta(seconds=2)).isoformat(),
        "action": "validation_manager",
        "resultat": {"validee": True},
    }]
    assert service.validation_identique_trop_recente(historique, True, maintenant) is True


def test_validation_identique_trop_recente_laisse_passer_apres_le_delai():
    maintenant = datetime.now(timezone.utc)
    historique = [{
        "horodatage": (maintenant - timedelta(seconds=30)).isoformat(),
        "action": "validation_manager",
        "resultat": {"validee": True},
    }]
    assert service.validation_identique_trop_recente(historique, True, maintenant) is False


def test_validation_identique_trop_recente_laisse_passer_une_valeur_differente():
    """Valider puis invalider juste après est une décision distincte, jamais bloquée."""
    maintenant = datetime.now(timezone.utc)
    historique = [{
        "horodatage": (maintenant - timedelta(seconds=1)).isoformat(),
        "action": "validation_manager",
        "resultat": {"validee": True},
    }]
    assert service.validation_identique_trop_recente(historique, False, maintenant) is False


def test_validation_identique_trop_recente_ignore_une_autre_action():
    maintenant = datetime.now(timezone.utc)
    historique = [{
        "horodatage": (maintenant - timedelta(seconds=1)).isoformat(),
        "action": "evaluation",
        "resultat": {"ipe_1_clients": "ok"},
    }]
    assert service.validation_identique_trop_recente(historique, True, maintenant) is False


def test_validation_identique_trop_recente_historique_vide():
    assert service.validation_identique_trop_recente([], True) is False


# ---------------------------------------------------------------------------
# modules_en_ecart_non_qualifie — refuse la validation tant qu'un module est
# en écart réel sans qualification ; "non_evaluable" n'est jamais bloquant
# (TODO(spec: CAC-IPE-01)), docs/PLAN_verrou_IPE.md.
# ---------------------------------------------------------------------------

def test_modules_en_ecart_non_qualifie_detecte_un_ecart_sans_etiquette():
    modules = {
        "ipe_2_fournisseurs": {
            "statut": "ecart",
            "derniere_evaluation": {"qualification": {"etiquette": None}},
        },
    }
    assert service.modules_en_ecart_non_qualifie(modules) == ["ipe_2_fournisseurs"]


def test_modules_en_ecart_non_qualifie_laisse_passer_un_ecart_qualifie():
    modules = {
        "ipe_2_fournisseurs": {
            "statut": "ecart",
            "derniere_evaluation": {"qualification": {"etiquette": "accepte"}},
        },
    }
    assert service.modules_en_ecart_non_qualifie(modules) == []


def test_modules_en_ecart_non_qualifie_ignore_les_modules_non_evaluables():
    """Un module "non_evaluable" (fichier absent, ou aucun collectif) ne bloque jamais la validation."""
    modules = {
        "ipe_1_clients": {
            "statut": "non_evaluable",
            "derniere_evaluation": {"qualification": {"etiquette": None}},
        },
    }
    assert service.modules_en_ecart_non_qualifie(modules) == []


def test_modules_en_ecart_non_qualifie_ignore_les_modules_ok():
    modules = {"ipe_3_immobilisations": {"statut": "ok", "derniere_evaluation": {"qualification": {}}}}
    assert service.modules_en_ecart_non_qualifie(modules) == []


def test_modules_en_ecart_non_qualifie_sans_modules():
    assert service.modules_en_ecart_non_qualifie(None) == []
    assert service.modules_en_ecart_non_qualifie({}) == []


def test_collectif_conserve_les_numeros_de_la_balance_generale():
    lignes_bg = [{"numero_compte": "401000", "solde_reel": -300.0}]
    lignes_aux = [{"numero_compte": "4011AF", "solde_final_debit": 0.0, "solde_final_credit": 300.0}]
    collectif = service.rapprocher_famille(lignes_bg, lignes_aux, "40", "numero_compte")["collectifs"][0]
    assert collectif["numero_compte"] == "401"
    assert collectif["comptes_balance_generale"] == ["401000"]
