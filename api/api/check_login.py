import pymongo, bcrypt
EMAIL = "admin@cac-perform.local"
PASSWORD = b"MonMotDePasse!2026"
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["cac_perform"]
user = db.Manager.find_one({"email": EMAIL})
if not user:
    print("USER_NOT_FOUND")
else:
    stored = user.get("mot_de_passe", "")
    try:
        ok = bcrypt.checkpw(PASSWORD, stored.encode("utf-8"))
    except Exception as e:
        print("CHECK_ERROR", e)
        ok = False
    print("EMAIL:", EMAIL)
    print("HASH_PREFIX:", stored[:10])
    print("MATCH:", ok)






