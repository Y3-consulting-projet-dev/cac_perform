import os
from mongoengine import Document, StringField, EmbeddedDocument, EmbeddedDocumentField, ListField, DictField
import docx
import openpyxl
from xlsxwriter import worksheet
from src.models import clit
from bson import ObjectId
import json
from openpyxl import load_workbook

db = clit.get_database('cac_perform')

# Classe Revue_analytique
class Revue_analytique(Document):
    def __init__(self):
        # Remplacer EFI et SIGNIFICATIF par COMMENTAIRE dans la liste des tableaux
        self.list_tableaux = [
            "CR", "BI", "ERE", "MA", "APE", "TSE", "IT", "PE", "ADP", "ACE", 
            "RF", "PA", "IC", "AAVI", "IF", "ST", "AC", "TR", "CP", "DF", "DCRA", 
            "FCR", "DFS", "AD", "COMMENTAIRE"  # Ajout de COMMENTAIRE ici
        ]
    
    def init_revue(self, mission_id):
        """
        Cette méthode récupère les balances de la mission spécifiée et génère un rapport de revue analytique.
        """
        # Récupérer les balances
        balances = db.Mission1.find_one({"_id": ObjectId(mission_id)}, {"_id": 0})['balances']

        # Code existant pour la gestion des balances
        id_balance_n = balances[0]
        id_balance_n1 = balances[1]
        balance_n = db.Balance.find_one({"_id": ObjectId(id_balance_n)})['balance']
        balance_n1 = db.Balance.find_one({"_id": ObjectId(id_balance_n1)})['balance']

        # Produire structure à partir d'un fichier JSON
        with open('revue.json', 'r') as file:
            result = json.load(file)
        
        # Mise à jour de la structure avec "COMMENTAIRE"
        result['mission_id'] = mission_id
        structure = result['structure']
        
        # Calcul des soldes et ajout des données de la revue
        for struct in structure:
            compte = struct['compte']
            struct['solde_n'] = sum((
                (item['debit_fin'] if item['debit_fin'] is not None else 0) - 
                (item['credit_fin'] if item['credit_fin'] is not None else 0)) 
                for item in balance_n if item['numero_compte'].startswith(str(compte))
            )
            struct['solde_n1'] = sum((
                (item['debit_fin'] if item['debit_fin'] is not None else 0) - 
                (item['credit_fin'] if item['credit_fin'] is not None else 0)) 
                for item in balance_n1 if item['numero_compte'].startswith(str(compte))
            )

        # Sauvegarder la structure mise à jour dans un fichier ou base de données
        # Vous pouvez ici sauvegarder le fichier JSON ou l'enregistrer dans la base de données
        return result

    def generate_report(self, mission_id):
        """
        Génère le rapport complet de la revue analytique pour la mission.
        """
        # Initialiser la revue
        revue_data = self.init_revue(mission_id)
        
        # Exemple de génération d'un fichier Word (rapport) à partir des données de revue
        document = docx.Document()

        document.add_heading(f"Rapport de Revue Analytique - Mission {mission_id}", 0)

        # Ajout de la structure des comptes et des soldes
        for struct in revue_data['structure']:
            document.add_paragraph(f"Compte: {struct['compte']}")
            document.add_paragraph(f"Solde N: {struct['solde_n']}")
            document.add_paragraph(f"Solde N-1: {struct['solde_n1']}")
            document.add_paragraph("")

        # Sauvegarder le document Word
        document.save(f"rapport_revue_{mission_id}.docx")

        return f"Rapport de revue pour la mission {mission_id} généré avec succès !"
