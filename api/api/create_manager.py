import bcrypt
import pymongo

EMAIL = "admin@cac-perform.local"
PASSWORD = "MonMotDePasse!2026"

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["cac_perform"]

hashed = bcrypt.hashpw(PASSWORD, bcrypt.gensalt()).decode()
res = db.Manager.update_one(
    {"email": EMAIL},
    {"$set": {"email": EMAIL, "mot_de_passe": hashed}},
    upsert=True,
)
print("OK - user set:", EMAIL)
