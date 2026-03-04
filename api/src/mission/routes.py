import os
from flask import jsonify, make_response, request, send_file
from src.mission import mission
from src.model import BalanceComptable, LigneComptable, Mission
from src.services.mission_services import MissionService
# from src.model_revue import Revue_analytique  # Désactivé pour éviter le crash si le docx n'existe pas
from werkzeug.utils import secure_filename
from bson import ObjectId




# =========================
# Revue / Cohérence / Intangibilité (UNIQUE)
# =========================
@mission.get('/revue_analytique/<id_mission>')
def revue_analytique_route(id_mission):
    cls = Mission()
    result = cls.revue_analytique(id_mission)
    return make_response(jsonify({"response": result}), 200)

@mission.put('/revue_analytique/<id_mission>/commentaire')
def update_commentaire_route(id_mission):
    """
    Met à jour le commentaire personnalisé pour un compte spécifique
    """
    try:
        data = request.get_json()
        numero_compte = data.get('numero_compte')
        commentaire_perso = data.get('commentaire_perso')
        
        if not numero_compte:
            return make_response(jsonify({"error": "Numéro de compte requis"}), 400)
        
        cls = Mission()
        success = cls.update_commentaire_perso(id_mission, numero_compte, commentaire_perso)
        
        if success:
            return make_response(jsonify({"response": "Commentaire mis à jour avec succès"}), 200)
        else:
            return make_response(jsonify({"error": "Échec de la mise à jour du commentaire"}), 500)
            
    except Exception as e:
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)

@mission.get('/controle_coherence/<id_mission>')
def controle_coherence_route(id_mission):
    cls = Mission()
    report = cls.controle_coherence(id_mission)
    return jsonify(report)

@mission.get('/all_missions')
def all_missions_route():
    missions = MissionService.get_all_missions()
    return make_response(jsonify({"response": missions}), 200)

@mission.get('/controle_intangibilite/<id_mission>')
def controle_intangibilite_route(id_mission):
    print(f"[ROUTE] GET /controle_intangibilite/{id_mission}")
    cls = Mission()
    # Utiliser la version avec reclassements si disponibles
    report = cls.controle_intangibilite_avec_reclassements(id_mission)
    # Ne retourner que les écarts
    comptes = report.get("comptes")
    if isinstance(comptes, list):
        ecarts = [
            c for c in comptes
            if c and c.get("status") in ("ecart", "nouveau", "supprime", "ecart_partiel")
        ]
        report["comptes"] = ecarts
        report["ecarts_only"] = True
    print(f"[ROUTE] Rapport retourne: total_comptes={report.get('total_comptes', 'N/A')}, comptes_length={len(report.get('comptes', []))}")
    return make_response(jsonify({"response": report}), 200)

@mission.get('/classement_bilan/<id_mission>')
def classement_bilan_route(id_mission):
    cls = Mission()
    report = cls.classement_bilan(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.get('/etats_financiers_preliminaires/<id_mission>')
def etats_financiers_preliminaires_route(id_mission):
    cls = Mission()
    report = cls.etats_financiers_preliminaires(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.get('/materialite/<id_mission>')
def materialite_route(id_mission):
    cls = Mission()
    report = cls.materialite(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.get('/analyse_quantitative/<id_mission>')
def analyse_quantitative_route(id_mission):
    cls = Mission()
    report = cls.analyse_quantitative(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.get('/analyse_qualitative/<id_mission>')
def analyse_qualitative_route(id_mission):
    cls = Mission()
    report = cls.analyse_qualitative(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.post('/init_qualitative_responses/<id_mission>')
def init_qualitative_responses_route(id_mission):
    try:
        from src.config.db import db
        from bson import ObjectId
        
        # Récupérer la mission
        mission = db.Mission1.find_one({"_id": ObjectId(id_mission)})
        if not mission:
            return make_response(jsonify({"response": {"ok": False, "message": "Mission non trouvée"}}), 404)
        
        # Récupérer les données de grouping
        grouping = mission.get("grouping", [])
        if not grouping:
            return make_response(jsonify({"response": {"ok": False, "message": "Données de grouping manquantes"}}), 400)
        
        # Initialiser les réponses qualitatives
        qualitative_responses = {}
        for item in grouping:
            compte = item.get('compte', '')
            qualitative_responses[compte] = {}
            # Initialiser toutes les questions Q1-Q8 à False
            for q in range(1, 9):
                qualitative_responses[compte][f'Q{q}'] = False
        
        # Sauvegarder les réponses initialisées
        result = db.Mission1.update_one(
            {"_id": ObjectId(id_mission)}, 
            {"$set": {"qualitative_responses": qualitative_responses}}
        )
        
        if result.modified_count > 0:
            return make_response(jsonify({"response": {"ok": True, "message": "Réponses qualitatives initialisées avec succès"}}), 200)
        else:
            return make_response(jsonify({"response": {"ok": False, "message": "Aucune modification effectuée"}}), 200)
            
    except Exception as e:
        return make_response(jsonify({"response": {"ok": False, "message": str(e)}}), 500)

@mission.put('/save_qualitative_responses/<id_mission>')
def save_qualitative_responses_route(id_mission):
    try:
        from flask import request
        from bson import ObjectId
        from src.config.db import db
        
        data = request.get_json()
        if not data:
            return make_response(jsonify({"response": {"ok": False, "message": "Aucune donnée reçue"}}), 400)
            
        responses = data.get('responses', {})
        print(f"🔄 Sauvegarde des réponses pour mission {id_mission}")
        print(f"📊 Nombre de réponses: {len(responses)}")
        
        # Vérifier que la mission existe
        mission = db.Mission1.find_one({"_id": ObjectId(id_mission)})
        if not mission:
            return make_response(jsonify({"response": {"ok": False, "message": "Mission non trouvée"}}), 404)
        
        # Sauvegarder les réponses dans la mission
        result = db.Mission1.update_one(
            {"_id": ObjectId(id_mission)}, 
            {"$set": {"qualitative_responses": responses}}
        )
        
        print(f"✅ Résultat de la mise à jour: {result.modified_count} documents modifiés")
        
        if result.modified_count > 0:
            return make_response(jsonify({"response": {"ok": True, "message": "Réponses sauvegardées avec succès"}}), 200)
        else:
            return make_response(jsonify({"response": {"ok": True, "message": "Aucune modification nécessaire"}}), 200)
            
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {str(e)}")
        return make_response(jsonify({"response": {"ok": False, "message": str(e)}}), 500)

# =========================
# Création mission
# =========================
@mission.post('/nouvelle_mission')
def new_assign():
    try:
        uploaded_files = request.files.getlist('files[]')
        annee_auditee = request.form.get('annee_auditee')
        id_client = request.form.get('id')
        date_debut = request.form.get('date_debut')
        date_fin = request.form.get('date_fin')
        date_debut_mandat = request.form.get('date_debut_mandat')
        date_fin_mandat = request.form.get('date_fin_mandat')
        responsable_nom = request.form.get('responsable_nom')
        responsable_grade = request.form.get('responsable_grade')
        responsable_role = request.form.get('responsable_role')
        responsable_id = request.form.get('responsable_id')
        
        # Validation des données reçues
        if not uploaded_files or len(uploaded_files) < 2:
            return make_response(jsonify({"error": "Au moins 2 fichiers de balance sont requis (N et N-1)"}), 400)
        
        if not all([annee_auditee, id_client, date_debut, date_fin, date_debut_mandat, date_fin_mandat]):
            return make_response(jsonify({"error": "Tous les champs sont requis (y compris les dates du mandat)"}), 400)
        
        # Filtrer les fichiers valides (non vides)
        valid_files = [f for f in uploaded_files if f and f.filename]
        if len(valid_files) < 2:
            return make_response(jsonify({"error": f"Seulement {len(valid_files)} fichier(s) valide(s) reçu(s), 2 requis"}), 400)
        
        print(f"Fichiers reçus: {[f.filename for f in valid_files]}")
        print(f"Données reçues: annee={annee_auditee}, client={id_client}, debut={date_debut}, fin={date_fin}")
        print(f"Mandat: debut={date_debut_mandat}, fin={date_fin_mandat}")
        
        cls = Mission()
        donnees = cls.nouvelle_mission(
            valid_files,
            annee_auditee,
            id_client,
            date_debut,
            date_fin,
            date_debut_mandat,
            date_fin_mandat,
            responsable_nom,
            responsable_grade,
            responsable_role,
            responsable_id
        )

        if donnees:
            return make_response(jsonify({"success": True, "data": donnees}), 200)
        else:
            return make_response(jsonify({"error": "Erreur lors de la création de la mission"}), 500)
            
    except Exception as e:
        print(f"Erreur dans new_assign: {str(e)}")
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)

# =========================
# Suppression de mission
# =========================
@mission.delete('/supprimer_mission/<id_mission>')
def supprimer_mission_route(id_mission):
    """
    Supprime une mission et toutes ses données associées (balances, etc.)
    """
    try:
        from src.model import db
        
        # Vérifier que la mission existe
        mission = db.Mission1.find_one({"_id": ObjectId(id_mission)})
        if not mission:
            return make_response(jsonify({"error": "Mission non trouvée"}), 404)
        
        # Récupérer les IDs des balances associées
        balance_ids = mission.get("balances", [])
        
        # Supprimer les balances associées
        balances_supprimees = 0
        for balance_id in balance_ids:
            try:
                result = db.Balance.delete_one({"_id": ObjectId(balance_id)})
                if result.deleted_count > 0:
                    balances_supprimees += 1
            except Exception as e:
                print(f"⚠️ Erreur lors de la suppression de la balance {balance_id}: {str(e)}")
        
        # Supprimer la mission
        result = db.Mission1.delete_one({"_id": ObjectId(id_mission)})
        
        if result.deleted_count > 0:
            print(f"✅ Mission {id_mission} supprimée avec succès ({balances_supprimees} balance(s) supprimée(s))")
            return make_response(jsonify({
                "success": True,
                "message": f"Mission supprimée avec succès ({balances_supprimees} balance(s) supprimée(s))"
            }), 200)
        else:
            return make_response(jsonify({"error": "Erreur lors de la suppression de la mission"}), 500)
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression de la mission {id_mission}: {str(e)}")
        import traceback
        traceback.print_exc()
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)

# =========================
# Grouping (si encore utilisé)
# =========================
@mission.get('/grouping_model/')
def make_grouping():
    data = request.files.getlist('file[]')
    model_mission = Mission()
    groupe = model_mission.grouping(balances_rapprochee=data)
    if groupe:
        return make_response(jsonify({"response": groupe}), 200)
    else:
        return make_response(jsonify({"response": "Impossible"}), 201)

#################################################################################################
# Tests liés à Revue_analytique — DÉSACTIVÉS
#################################################################################################
# @mission.get('/test/<id_mission>')
# def test(id_mission):
#     data = Revue_analytique()
#     res = data.init_revue(id_mission)
#     if res == 1:
#         return make_response(jsonify({"response": "Ok"}), 200)
#     else:
#         return make_response(jsonify({"response": "Nop"}), 200)

# @mission.get('/marges/<id_mission>')
# def poptab(id_mission):
#     data = Revue_analytique()
#     res = data.return_tab_ma(id_mission, 12, "MA")
#     if res:
#         return make_response(jsonify({"response": res}), 200)
#     else:
#         return make_response(jsonify({"response": "Nop"}), 200)

# =========================
# Infos mission
# =========================
@mission.get('/affichage_infos_mission/<_id>')
def show_assign_info(_id):
    cls = Mission()
    infos = cls.afficher_informations_missions(_id)
    return jsonify(infos)

# =========================
# EFI (placeholder ancien)
# =========================
@mission.post('/recuperation_etats_financier/')
def generate_efi():
    balances = request.files.getlist('file[]')
    cls = Mission()
    tous = cls.prod_efi(balances)
    return tous

#################################################################################################
# Seuil de signification
#################################################################################################
@mission.get('/get_benchmarks/<id_mission>')
def get_benchmarks(id_mission):
    cls = Mission()
    benchmarks = cls.get_benchmarks(id_mission)
    return make_response(jsonify({"response": benchmarks}), 200)

@mission.put('/save_materiality/<id_mission>')
def save_materiality(id_mission):
    materialities = request.get_json()
    cls = Mission()
    result = cls.save_materiality(id_mission, materialities)
    return make_response(jsonify({"response": result}), 200)

@mission.put('/validate_materiality/<id_mission>')
def validate_materiality(id_mission):
    req = request.get_json()
    bench = req['benchmark']
    cls = Mission()
    result = cls.validate_materiality(id_mission, bench)
    if result:
        return make_response(jsonify({"response": result}), 200)
    else:
        return make_response(jsonify({"response": "Echec"}), 200)

@mission.get('/get_materiality/<id_mission>')
def get_materiality(id_mission):
    cls = Mission()
    materiality = cls.get_materiality(id_mission)
    return make_response(jsonify({"response": materiality}), 200)

@mission.put('/quantitative_analysis/<id_mission>')
def make_quantitative_analysis(id_mission):
    cls = Mission()
    result = cls.make_quantitative_analysis(id_mission)
    return make_response(jsonify({"response": result}), 200)

@mission.put('/qualitative_analysis/<id_mission>')
def make_qualitative_analysis(id_mission):
    try:
        cls = Mission()
        data = request.get_json()
        listGrouping = data.get('listGrouping', [])

        if not listGrouping:
            return make_response(jsonify({"response": {"ok": False, "message": "Aucune donnée de grouping fournie"}}), 400)

        # Grouper les réponses par compte
        _list_unique_compte = list(set((item['compte'] for item in listGrouping)))

        _listGrouping = []
        for compte in _list_unique_compte:
            data = {}
            data['compte'] = compte
            # Récupérer toutes les réponses pour ce compte
            _list = [{"question": item['question'], "significant": item['significant']}
                     for item in listGrouping if item['compte'] == compte]
            data['data'] = _list
            _listGrouping.append(data)

        # Déterminer si le compte est significatif (au moins une réponse positive)
        for group in _listGrouping:
            value_sign = any((item['significant'] for item in group['data']))
            group['significant'] = value_sign
            del group['data']

        result = cls.make_qualitative_analysis(id_mission, _listGrouping)
        
        if result > 0:
            return make_response(jsonify({"response": {"ok": True, "message": "Analyse qualitative appliquée avec succès", "modified_count": result}}), 200)
        else:
            return make_response(jsonify({"response": {"ok": False, "message": "Aucune modification effectuée"}}), 200)
            
    except Exception as e:
        return make_response(jsonify({"response": {"ok": False, "message": str(e)}}), 500)

@mission.get('/grouping_with_qualitative/<id_mission>')
def get_grouping_with_qualitative(id_mission):
    try:
        from src.config.db import db
        from bson import ObjectId
        
        mission = db.Mission1.find_one({"_id": ObjectId(id_mission)})
        if not mission:
            return make_response(jsonify({"response": {"ok": False, "message": "Mission non trouvée"}}), 404)
        
        grouping = mission.get("grouping", [])
        if not grouping:
            return make_response(jsonify({"response": {"ok": False, "message": "Données de grouping manquantes"}}), 400)
        
        # Ajouter des statistiques
        total_accounts = len(grouping)
        significant_accounts = len([item for item in grouping if item.get('significant', False)])
        
        result = {
            "ok": True,
            "grouping": grouping,
            "statistics": {
                "total_accounts": total_accounts,
                "significant_accounts": significant_accounts,
                "non_significant_accounts": total_accounts - significant_accounts,
                "percentage_significant": (significant_accounts / total_accounts * 100) if total_accounts > 0 else 0
            }
        }
        
        return make_response(jsonify({"response": result}), 200)
        
    except Exception as e:
        return make_response(jsonify({"response": {"ok": False, "message": str(e)}}), 500)

@mission.get('/make_final/<id_mission>')
def make_final(id_mission):
    cls = Mission()
    result, grouping = cls.make_final_sm(id_mission)
    return make_response(jsonify({"response": result, "grouping": grouping}), 200)

@mission.get('/presentation_comptes_significatifs/<id_mission>')
def presentation_comptes_significatifs_route(id_mission):
    cls = Mission()
    report = cls.presentation_comptes_significatifs(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.get('/revue_analytique_finale/<id_mission>')
def revue_analytique_finale_route(id_mission):
    cls = Mission()
    report = cls.revue_analytique_finale(id_mission)
    return make_response(jsonify({"response": report}), 200)

@mission.put('/save_revue_analytique/<id_mission>')
def save_revue_analytique_route(id_mission):
    try:
        data = request.get_json()
        revue_data = data.get('revue_data', [])
        
        # Sauvegarder les données de revue dans la mission
        from src.config.db import db
        from bson import ObjectId
        
        result = db.Mission1.update_one(
            {"_id": ObjectId(id_mission)}, 
            {"$set": {"revue_analytique_finale.revue": revue_data}}
        )
        
        if result.modified_count > 0:
            return make_response(jsonify({"response": {"ok": True, "message": "Revue analytique sauvegardée avec succès"}}), 200)
        else:
            return make_response(jsonify({"response": {"ok": False, "message": "Aucune modification effectuée"}}), 200)
            
    except Exception as e:
        return make_response(jsonify({"response": {"ok": False, "message": str(e)}}), 500)

@mission.get('/download_grouping/<id_mission>')
def download_grouping(id_mission):
    cls = Mission()
    excel_result = cls.extract_grouping(id_mission)
    return send_file(
        excel_result,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name="grouping.xlsx"
    )

# =========================
# Reclassements pour contrôle d'intangibilité
# =========================
@mission.post('/controle_intangibilite/<id_mission>/reclassement')
def ajouter_reclassement_route(id_mission):
    """
    Ajoute un reclassement dans le contrôle d'intangibilité
    """
    try:
        data = request.get_json()
        if not data:
            return make_response(jsonify({"error": "Aucune donnée reçue"}), 400)
        
        cls = Mission()
        result = cls.ajouter_reclassement_intangibilite(id_mission, data)
        
        if result.get("ok", False):
            return make_response(jsonify({"response": result}), 200)
        else:
            return make_response(jsonify({"error": result.get("message", "Erreur inconnue")}), 400)
            
    except Exception as e:
        print(f"❌ Erreur dans ajouter_reclassement_route: {str(e)}")
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)

@mission.get('/controle_intangibilite/<id_mission>/reclassements')
def lister_reclassements_route(id_mission):
    """
    Liste tous les reclassements d'une mission
    """
    try:
        cls = Mission()
        result = cls.lister_reclassements_intangibilite(id_mission)
        return make_response(jsonify({"response": result}), 200)
        
    except Exception as e:
        print(f"❌ Erreur dans lister_reclassements_route: {str(e)}")
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)

@mission.delete('/controle_intangibilite/<id_mission>/reclassement/<reclassement_id>')
def supprimer_reclassement_route(id_mission, reclassement_id):
    """
    Supprime un reclassement
    """
    try:
        cls = Mission()
        result = cls.supprimer_reclassement_intangibilite(id_mission, reclassement_id)
        
        if result.get("ok", False):
            return make_response(jsonify({"response": result}), 200)
        else:
            return make_response(jsonify({"error": result.get("message", "Erreur inconnue")}), 400)
            
    except Exception as e:
        print(f"❌ Erreur dans supprimer_reclassement_route: {str(e)}")
        return make_response(jsonify({"error": f"Erreur serveur: {str(e)}"}), 500)
