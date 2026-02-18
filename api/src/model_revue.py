
# import os
# from mongoengine import Document, StringField, EmbeddedDocument, EmbeddedDocumentField, ListField, DictField
# import docx
# import openpyxl
# from xlsxwriter import worksheet
# from src.models import clit
# from bson import ObjectId
# import json
# from openpyxl import load_workbook


# db = clit.get_database('cac_perform')

# document = docx.Document("Rapports/revue.docx")

# # document = docx.Document('Rapports/revue.docx')
# # docmt = DocxTemplate('Rapports/revue.docx')


# class Revue_analytique(Document):

#     def __init__(self):
#         self.list_tableaux = ["CR", "BI", "ERE", "MA", "APE", "TSE", "IT", "PE", "ADP", "ACE",
#                               "RF", "PA", "IC", "AAVI", "IF", "ST", "AC", "TR", "CP", "DF", "DCRA", "FCR", "DFS", "AD"]

#     def init_revue(self, mission_id):
#         # Recupérer les balances
#         balances = db.Mission1.find_one(
#             {"_id": ObjectId(mission_id)}, {"_id": 0})['balances']
#         # balance_variation = db.Mission1.find_one({"_id": ObjectId(mission_id)}, {"_id":0})['balance_variation']

#         id_balance_n = balances[0]
#         id_balance_n1 = balances[1]

#         balance_n = db.Balance.find_one(
#             {"_id": ObjectId(id_balance_n)})['balance']
#         balance_n1 = db.Balance.find_one(
#             {"_id": ObjectId(id_balance_n1)})['balance']

#         # Produire structure à partir d'un fichier JSON
#         with open('revue.json', 'r') as file:
#             result = json.load(file)

#         result['mission_id'] = mission_id
#         structure = result['structure']

#         for struct in result['structure']:
#             compte = struct['compte']

#             struct['solde_n'] = sum(((item['debit_fin'] if item['debit_fin'] is not None else 0) - (item['credit_fin']
#                                     if item['credit_fin'] is not None else 0)) for item in balance_n if item['numero_compte'].startswith(str(compte)))
#             struct['solde_n1'] = sum(((item['debit_fin'] if item['debit_fin'] is not None else 0) - (item['credit_fin']
#                                      if item['credit_fin'] is not None else 0)) for item in balance_n1 if item['numero_compte'].startswith(str(compte)))
#             struct['variation'] = struct['solde_n'] - struct['solde_n1']

#             if struct['solde_n1'] == 0:
#                 struct['variation_pourcent'] = 0
#             else:
#                 struct['variation_pourcent'] = (
#                     struct['solde_n'] - struct['solde_n1']) / struct['solde_n1']
#                 struct['variation_pourcent'] = struct['variation_pourcent'] * 100

#         created = db.Revue.insert_one(result)

#         return str(created.inserted_id)

#     def return_tab_ma(self, mission_id, code_tab, sheet):
#         query = {"mission_id": mission_id}
#         result = db.Revue.find_one(query, {"_id": 0})
#         structure = result['structure']

#         data = []

#         length_tab = sheet.max_row

#         for i in range(length_tab):
#             row = {}
#             cell = code_tab + str(i + 1)

#             row['solde_n'] = sum(item['solde_n']
#                                  for item in structure if cell in item['ref_revue'])
#             row['solde_n1'] = sum(item['solde_n1']
#                                   for item in structure if cell in item['ref_revue'])
#             row['variation'] = sum(item['variation']
#                                    for item in structure if cell in item['ref_revue'])
#             row['variation_pourcent'] = sum(
#                 item['variation_pourcent'] for item in structure if cell in item['ref_revue'])

#             data.append(row)

#         for ligne in data:
#             sheet.append(ligne)

#         # for row_index, row_data in enumerate(data):
#         #     for col_index, cell_data in enumerate(row_data.values()):
#         #         worksheet.write(row_index, col_index, str(cell_data))
#         # return document

#     def revue(self, mission_id):

#         # try:
#         file = openpyxl.load_workbook(
#             'Rapports/Tableaux_revue_analytique.xlsx')
#         sheet = file['Tableaux_revue']
#         colonnes = [colonne for colonne in sheet.iter_cols(
#             min_row=3, max_row=7)]

#         for colonne in colonnes[0]:
#             # Obtenez la lettre de la colonne (A, B, C, ...)
#             print(colonne)
#             code = colonne.column_letter
#             self.return_tab_ma(mission_id, code, sheet)

#         file.save("Rapports/Tableaux_revue_analytique.xlsx")
#         os.system('start Rapports/Tableaux_revue_analytique.xlsx')

#         return file
#         # except Exception as e:
#         #     print(f"An exception occured : {str(e)} ")
# Assurez-vous que ce code est dans model_revue.py
from mongoengine import Document
from bson import ObjectId
from src.models import clit

db = clit.get_database('cac_perform')

class Revue_analytique(Document):
    def __init__(self):
        self.list_tableaux = [
            "CR", "BI", "ERE", "MA", "APE", "TSE", "IT", "PE", "ADP", "ACE",
            "RF", "PA", "IC", "AAVI", "IF", "ST", "AC", "TR", "CP", "DF",
            "DCRA", "FCR", "DFS", "AD", "COMMENTAIRE"
        ]

    def init_revue(self, mission_id):
        try:
            mission = db.Mission1.find_one({"_id": ObjectId(mission_id)}, {"_id": 0})
            if not mission:
                return {"ok": False, "message": "Mission non trouvée", "structure": []}

            balances = mission.get("balances", [])
            if len(balances) < 2:
                return {"ok": False, "message": "Balances manquantes", "structure": []}

            balance_n = db.Balance.find_one({"_id": ObjectId(balances[0])}, {"balance": 1})
            balance_n1 = db.Balance.find_one({"_id": ObjectId(balances[1])}, {"balance": 1})

            if not balance_n or not balance_n1:
                return {"ok": False, "message": "Balances introuvables", "structure": []}

            structure = [{"compte": x, "COMMENTAIRE": ""} for x in self.list_tableaux]

            for struct in structure:
                compte = struct.get("compte")
                struct['solde_n'] = sum(
                    ((item.get('debit_fin', 0) or 0) - (item.get('credit_fin', 0) or 0))
                    for item in balance_n.get("balance", [])
                    if str(item.get("numero_compte", "")).startswith(str(compte))
                )
                struct['solde_n1'] = sum(
                    ((item.get('debit_fin', 0) or 0) - (item.get('credit_fin', 0) or 0))
                    for item in balance_n1.get("balance", [])
                    if str(item.get("numero_compte", "")).startswith(str(compte))
                )

            return {"ok": True, "mission_id": mission_id, "structure": structure}

        except Exception as e:
            return {"ok": False, "message": str(e), "structure": []}
