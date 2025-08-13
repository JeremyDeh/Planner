from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from neo4j import GraphDatabase
import os
from functools import wraps


# Connection Neo4j (reprend tes variables d'env)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
NEO4J_DB = "neo4j"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Blueprint Auth
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))

            with driver.session(database=NEO4J_DB) as neo_session:
                result = neo_session.run("""
                    MATCH (u:Auth)
                    WHERE u.pk = $id
                    RETURN u.role AS role
                """, id=session["user_id"]).single()

                if not result or result["role"] != required_role:
                    return redirect(url_for("auth.unauthorized"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html"), 403


def create_user_in_neo4j(username, password):
    password_hash = generate_password_hash(password)

    with driver.session(database=NEO4J_DB) as session:
        # On vérifie si l'utilisateur existe déjà
        existing = session.run("""
            MATCH (u:Auth {user: $username})
            RETURN u
        """, username=username).single()

        if existing:
            return False  # déjà pris

        # Création avec PK incrémentée
        result = session.run("""
            MATCH (n:Auth) 
            WITH coalesce(max(n.pk) + 1, 1) AS maximum
            CREATE (u:Auth {
                user: $username,
                password: $password_hash,
                pk: maximum,
                created_at: datetime(),
                role: 'nobody'
                             
            })
            RETURN u
        """, username=username, password_hash=password_hash)

        return result.single() is not None



def verify_user_in_neo4j(username, password):
    """Vérifie si un utilisateur existe et si le mot de passe est correct."""
    with driver.session(database=NEO4J_DB) as session:
        result = session.run("""
            MATCH (u:Auth {user: $username})
            RETURN u.password AS password_hash, u.pk AS id
        """, username=username)
        record = result.single()
        if record and check_password_hash(record["password_hash"], password):
            return {"id": record["id"], "username": username}
    return None

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    print("########")
    print(session.get('user_id'))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = verify_user_in_neo4j(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.journee"))
        else:
            return render_template("login.html", error="Nom d'utilisateur ou mot de passe invalide")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        created = create_user_in_neo4j(username, password)
        if created:
            return redirect(url_for("auth.login"))
        else:
            return render_template("register.html", error="Nom d'utilisateur déjà pris")

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))