from neo4j import GraphDatabase
import time
import os

uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
user = os.environ.get("NEO4J_USER", "neo4j")
password = os.environ.get("NEO4J_PASSWORD", "neo4j")

# Attendre que la base soit dispo
def wait_for_neo4j(driver):
    for _ in range(30):
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            time.sleep(1)
    return False

# Vérifier s’il y a des données
def is_db_empty(driver):
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN COUNT(n) AS count")
        count = result.single()["count"]
        return count == 0

# Injecter les données
def init_db(driver):
    with driver.session() as session:
        session.run("""
UNWIND ['Dentiste', 'Imagerie','Esthéticienne','Cardiologie','Coiffeur','Pédicure','Famille','Autre' ,'Ophtalmologie','Audioprothésiste','Télémédecine','Urologie','Pneumologie','Dermatologie','Consultation mémoire','Chirurgie','Kinésithérapie','Ergothérapie','Rhumatologie','Urgence','Gastrologie/Entérologie','Animation','PASA','Endoscopie','Neurologie','Gynécologie','Oncologie','Néphrologie','Orthopédie','Ambulatoire','Endocrinologie','Diabétologie','Optique','Médecine','EMPPA'] AS catego
CREATE (:Categorie {metier: catego});
        """)
    with driver.session() as session:
        session.run("""
UNWIND ['Infirmières','Aides Soignantes','Ergothérapeute','Kiné','Secrétaire Médicale', 'Médecin Généraliste', 'Tous'] AS catego
CREATE (:Service {nom: catego});
        """)
    with driver.session() as session:
        session.run("""
        CREATE (g:Rappel {metier: 'Rappel',nom:'Rappel'})
        """)
    with driver.session() as session:
        session.run("""
        CREATE (n:Auth {user: 'Admin', password: 'pbkdf2:sha256:260000$37caSawTGiKjVu2W$debfe94b19d39d8174a82e00aa6e3fbb946396cf2e08a6f8adae85100bf9a391', role: 'admin',pk:1 })
        """)



        
if __name__ == "__main__":
    driver = GraphDatabase.driver(uri, auth=(user, password))
    if wait_for_neo4j(driver):
        if is_db_empty(driver):
            print("Base vide, insertion des données initiales...")
            init_db(driver)
        else:
            print("Base déjà remplie, rien à faire.")
    else:
        print("Échec de connexion à Neo4j.")
