from flask import Flask
from app.routes.routes import main_bp
from app.routes.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "change_me_secret"  # à mettre en variable d'env
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    print('Lancement en cours ')
    app.run(debug=True, port=5001)
