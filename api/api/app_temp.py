#!/usr/bin/env python3
"""
Version temporaire de l'application qui fonctionne sans MongoDB
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import bcrypt
import json
import os
import time
import jwt

# Créer l'application Flask
app = Flask(__name__)

# Configuration CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],
        "methods": "GET, POST, PUT, DELETE",
        "allow_headers": ["Authorization", "Content-Type"]
    }
})

# Fichier temporaire pour les utilisateurs
USERS_FILE = "temp_users.json"

def load_users():
    """Charge les utilisateurs depuis le fichier temporaire"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users):
    """Sauvegarde les utilisateurs dans le fichier temporaire"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def verify_user(email, password):
    """Vérifie les identifiants de l'utilisateur"""
    users = load_users()
    
    for user in users:
        if user.get("email") == email:
            stored_password = user.get("mot_de_passe", "")
            
            try:
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    return {"email": user.get("email"), "_id": user.get("_id", "temp_id")}
            except Exception:
                # Fallback: mot de passe en clair
                if stored_password == password:
                    return {"email": user.get("email"), "_id": user.get("_id", "temp_id")}
    
    return None

# Routes temporaires
@app.route('/cors/manager/connexion/', methods=['POST'])
def login():
    """Route de connexion temporaire"""
    try:
        data = request.get_json()
        email = data.get('mail')
        password = data.get('pwd')
        
        if not email or not password:
            return jsonify({"error": "Email et mot de passe requis"}), 400
        
        user = verify_user(email, password)
        
        if not user:
            return jsonify({"error": "Identifiants invalides"}), 401
        
        # Générer un token JWT
        payload = {
            "sub": user.get("email"),
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60 * 8  # 8h
        }
        secret = 'temp_secret_key'
        token = jwt.encode(payload, secret, algorithm='HS256')
        
        return jsonify({
            "token": token,
            "user": {"email": user.get("email")}
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/controle_coherence/<id_mission>', methods=['GET'])
def controle_coherence_temp(id_mission):
    """Route temporaire pour le contrôle de cohérence"""
    try:
        # Données de test
        report = {
            "2024": {
                "annee": 2024,
                "equilibre_global": True,
                "erreurs": [],
                "nb_erreurs": 0
            },
            "2023": {
                "annee": 2023,
                "equilibre_global": True,
                "erreurs": [],
                "nb_erreurs": 0
            }
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/materialite/<id_mission>', methods=['GET'])
def materialite_temp(id_mission):
    """Route temporaire pour les matérialités"""
    try:
        # Données de test
        materiality = [
            {
                "benchmark": "profit_before_tax",
                "factor": "5%",
                "materiality": 100000,
                "performance_materiality": 80000,
                "trivial_misstatements": 5000,
                "choice": "",
                "warning": "",
                "original_value": 2000000
            }
        ]
        
        return jsonify({
            "ok": True,
            "message": "Données de matérialité récupérées avec succès",
            "materiality": materiality
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/affichage_infos_mission/<id_mission>', methods=['GET'])
def mission_info_temp(id_mission):
    """Route temporaire pour les informations de mission"""
    try:
        # Données de test
        mission_info = {
            "nom": "Mission Test",
            "annee_auditee": 2024,
            "client": "Client Test",
            "statut": "En cours"
        }
        
        return jsonify({"response": mission_info}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/save_materiality/<id_mission>', methods=['PUT'])
def save_materiality_temp(id_mission):
    """Route temporaire pour sauvegarder les matérialités"""
    try:
        data = request.get_json()
        print(f"Matérialité sauvegardée pour mission {id_mission}: {data}")
        
        return jsonify({"response": 1}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/quantitative_analysis/<id_mission>', methods=['PUT'])
def quantitative_analysis_temp(id_mission):
    """Route temporaire pour l'analyse quantitative"""
    try:
        print(f"Analyse quantitative pour mission {id_mission}")
        
        return jsonify({"response": "Analyse quantitative effectuée"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/controle_intangibilite/<id_mission>', methods=['GET'])
def controle_intangibilite_temp(id_mission):
    """Route temporaire pour le contrôle d'intangibilité"""
    try:
        report = {
            "ok": True,
            "message": "Contrôle d'intangibilité effectué",
            "erreurs": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/classement_bilan/<id_mission>', methods=['GET'])
def classement_bilan_temp(id_mission):
    """Route temporaire pour le classement bilan"""
    try:
        report = {
            "ok": True,
            "message": "Classement bilan effectué",
            "grouping": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/etats_financiers_preliminaires/<id_mission>', methods=['GET'])
def etats_financiers_temp(id_mission):
    """Route temporaire pour les états financiers"""
    try:
        report = {
            "ok": True,
            "message": "États financiers générés",
            "efi": {}
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/grouping/<id_mission>', methods=['GET'])
def grouping_temp(id_mission):
    """Route temporaire pour le grouping"""
    try:
        report = {
            "ok": True,
            "message": "Grouping récupéré",
            "grouping": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/revue_analytique/<id_mission>', methods=['GET'])
def revue_analytique_temp(id_mission):
    """Route temporaire pour la revue analytique"""
    try:
        report = {
            "ok": True,
            "message": "Revue analytique récupérée",
            "revue": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/qualitatif/<id_mission>', methods=['GET'])
def qualitatif_temp(id_mission):
    """Route temporaire pour l'analyse qualitative"""
    try:
        report = {
            "ok": True,
            "message": "Analyse qualitative récupérée",
            "qualitatif": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

@app.route('/cors/mission/synthese/<id_mission>', methods=['GET'])
def synthese_temp(id_mission):
    """Route temporaire pour la synthèse"""
    try:
        report = {
            "ok": True,
            "message": "Synthèse récupérée",
            "synthese": []
        }
        
        return jsonify({"response": report}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Démarrage de l'application temporaire (sans MongoDB)")
    print("=" * 60)
    print("📋 Identifiants de connexion :")
    print("   Email: admin@cac-perform.local")
    print("   Mot de passe: MonMotDePasse!2026")
    print("=" * 60)
    print("🌐 Application disponible sur : http://localhost:5000")
    print("🔗 Frontend : http://localhost:5173")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
