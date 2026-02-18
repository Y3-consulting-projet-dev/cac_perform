#!/usr/bin/env python3
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client['cac_perform']
mission = db.Mission1.find_one({'_id': ObjectId('690237d33b694de2f40f4329')})
report = mission.get('controle_intangibilite', {})
print(f'total_comptes: {report.get("total_comptes", 0)}')
print(f'comptes length: {len(report.get("comptes", []))}')
print(f'ok: {report.get("ok", "N/A")}')
print(f'message: {report.get("message", "N/A")}')









