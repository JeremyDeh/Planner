from flask import Flask
from app.routes.routes import main_bp
from app.routes.auth import auth_bp

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import json, datetime
import base64


# Charger clé publique
with open("app/licences/public.pem", "rb") as f:
    public_key = serialization.load_pem_public_key(f.read())
with open("app/licences/licence.lic", "rb") as f:
    signature_b64 = f.readline().strip()
    licence_json_b64 = f.read().strip()

# Décodage
signature = base64.b64decode(signature_b64)
licence_json = base64.b64decode(licence_json_b64)

# Vérification de la signature
try:
    public_key.verify(
        signature,
        licence_json,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
except Exception:
    raise SystemExit("Licence invalide ou falsifiée.")

# Vérification de la date
licence_data = json.loads(licence_json)
#if datetime.date.today() > datetime.date.fromisoformat(licence_data["expire"]):
#    print("Licence expirée.")
#    raise SystemExit("Licence expirée.")

print("Licence valide pour :", licence_data["client"])

def create_app():
    app = Flask(__name__)
    app.secret_key = "change_me_secret"  # à mettre en variable d'env
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    return app

app = create_app()
if __name__ == "__main__":
    
    print('Lancement en cours ')
    app.run(host="0.0.0.0", port=5001, debug=True)
    #app.run(debug=True, port=5001)
