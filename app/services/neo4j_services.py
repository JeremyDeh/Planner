from neo4j import GraphDatabase
import os
from datetime import datetime, timedelta
from app.services.utils_date import generate_dates
import pandas as pd

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
NEO4J_DB = "neo4j"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_residents():
    """
    Récupère la liste des noms complets des résidents depuis la base Neo4j.

    Returns:
        list[str]: Liste des noms complets des résidents,
        triés par nom puis prénom.
    """
    residents = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Resident) RETURN n.nom, n.prenom " \
                       "ORDER BY n.nom, n.prenom"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom'] + ' ' + record['n.prenom']
            if nom:
                residents.append(nom)
    return residents


def get_medecins():

    """
    Récupère la liste des métiers (catégories)
    des médecins depuis la base Neo4j.

    Returns:
        list[str]: Liste des métiers, triés par ordre alphabétique.
    """

    medecins = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Categorie) RETURN n.metier ORDER BY n.metier"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.metier']
            if nom:
                medecins.append(nom)
    return medecins


def extract_form_data(form):
    """
    Extrait et organise les données pertinentes du formulaire soumis.

    Args:
        form (ImmutableMultiDict): Données du formulaire HTTP (request.form).

    Returns:
        dict: Dictionnaire contenant :
            - recurrence (str): Indicateur de récurrence ('on' ou autre).
            - nom (str): Nom du patient.
            - prenom (str): Prénom du patient.
            - metier (str): Métier/médecin sélectionné.
            - lieu (str): Lieu du rendez-vous.
            - commentaire (str): Commentaire associé.
            - transport (str): Mode de transport.
            - date_rdv_list (list[datetime]): Liste des dates de
            rendez-vous (simple ou récurrent).
            - colonnes_table (dict): Détails des colonnes
            supplémentaires du formulaire,
              avec clé indice et valeurs [nom_colonne, unité, nombre, pk].
    """
    recurrence = form.get('fichierCSV', '0')

    nomPatient = form['nomPatient']
    nom, prenom = nomPatient.split(' ')[0], nomPatient.split(' ')[1]

    metier = form.get('nomMedecin', '')
    lieu = form.get('lieu')
    commentaire = form.get('commentaire', '')
    transport = form.get('transport')
    date_rdv = form.get('date_prestation', '')
    heure_rdv = form.get('heure_prestation', '')

    rdv_debut = datetime.fromisoformat(date_rdv + 'T' + heure_rdv + ':00')

    if recurrence == 'on':
        date_fin = form.get('date_fin', '')
        rdv_fin = datetime.fromisoformat(date_fin + 'T' + heure_rdv + ':00')
        type_recurrence = form.get('recurrence')
        date_rdv_list = generate_dates(rdv_debut, rdv_fin, type_recurrence)
    else:
        date_rdv_list = [rdv_debut]

    colonnes_table = {}
    colonne_ids = sorted({
        key.split('_')[0][3:]
        for key in form.keys()
        if key.startswith('col') and key.endswith('_name')
    })

    for i in colonne_ids:
        col_name = form.get(f'col{i}_name')
        if col_name:
            colonnes_table[i] = [
                col_name,
                form.get(f'col{i}_unit'),
                form.get(f'col{i}_nombre'),
                form.get(f'col{i}_pk') or ''
            ]

    return {
        'recurrence': recurrence,
        'nom': nom,
        'prenom': prenom,
        'metier': metier,
        'lieu': lieu,
        'commentaire': commentaire,
        'transport': transport,
        'date_rdv_list': date_rdv_list,
        'colonnes_table': colonnes_table
    }


def insert_rendez_vous(data):
    """
    Insère un ou plusieurs rendez-vous dans la base Neo4j
    pour un résident donné.

    Args:
        data (dict): Dictionnaire contenant les informations du rendez-vous,
            notamment :
            - nom (str): Nom du résident.
            - prenom (str): Prénom du résident.
            - metier (str): Métier/médecin concerné.
            - date_rdv_list (list[datetime]): Liste des dates des rendez-vous.
            - transport (str): Mode de transport.
            - lieu (str): Lieu du rendez-vous.
            - commentaire (str): Commentaire associé.
            - recurrence (str): Indicateur de récurrence.
            - colonnes_table (dict): Détails des actions
              associées au rendez-vous.
    """
    liste_actions = [x[0] for x in data['colonnes_table'].values()]
    with driver.session(database=NEO4J_DB) as session:
        for rdv in data['date_rdv_list']:
            cypher_query = """
            MATCH (n:Resident {nom:$nom, prenom:$prenom})
            MATCH (m:Categorie{metier:$metier})
            CREATE (n)-[r:Rdv {date:$date_str,
                               transport:$transport,
                               lieu:$lieu,
                               commentaire:$commentaire
                        }]->(m)
            """
            session.run(
                cypher_query,
                nom=data['nom'],
                prenom=data['prenom'],
                date_str=rdv,
                recurrence=data['recurrence'],
                action=liste_actions,
                commentaire=data['commentaire'],
                metier=data['metier'],
                transport=data['transport'],
                lieu=data['lieu']
            )


def create_rappels(data):
    """
    Crée des rappels associés aux rendez-vous dans la base Neo4j.

    Args:
        data (dict): Dictionnaire contenant les informations nécessaires,
        notamment :
            - nom (str): Nom du résident.
            - prenom (str): Prénom du résident.
            - metier (str): Métier/médecin concerné.
            - date_rdv_list (list[datetime]): Liste des dates des rendez-vous.
            - colonnes_table (dict): Détails des rappels à créer,
              avec le nombre de jours avant le rendez-vous.
            - transport (str): Mode de transport.
            - lieu (str): Lieu du rendez-vous.
    """
    with driver.session(database=NEO4J_DB) as session:
        for rdv in data['date_rdv_list']:
            for rappel_item in data['colonnes_table'].values():
                rappel_rdv = rdv - timedelta(days=int(rappel_item[2]))
                commentaire_rappel = rappel_item[0]
                cypher_query = """
                MATCH (n:Resident {nom:$nom, prenom:$prenom})
                MATCH (m:Rappel{nom:'Rappel'})
                CREATE (n)-[r:Rappel {date:$date_str,
                                date_evt:$date_evt,
                                rdv:$type_rdv,
                                lieu:$lieu,
                                transport:$transport,
                                commentaire:$commentaire
                            }]->(m)
                """
                session.run(
                    cypher_query,
                    nom=data['nom'],
                    prenom=data['prenom'],
                    type_rdv=data['metier'],
                    date_str=rappel_rdv,
                    date_evt=rdv,
                    action=None,
                    commentaire=commentaire_rappel,
                    transport=data['transport'],
                    lieu=data['lieu']
                )


def get_resident_properties(driver, db_name, nom, prenom):
    """
    Récupère les propriétés d'un résident spécifique.

    Args:
        driver: Objet driver Neo4j.
        db_name: Nom de la base de données.
        nom: Nom du résident.
        prenom: Prénom du résident.

    Returns:
        Un DataFrame pandas avec les propriétés du résident ou vide.
    """
    with driver.session(database=db_name) as session:
        cypher_query = (
            "MATCH (n:Resident {nom:$nom, prenom:$prenom}) "
            "RETURN properties(n) as consult"
        )
        results = session.run(cypher_query, nom=nom, prenom=prenom)
        dicts = [dict(record['consult']) for record in results]
        if dicts:
            return pd.DataFrame(dicts)
        else:
            return pd.DataFrame()


def get_rendez_vous(driver, db_name, nom, prenom):
    """
    Récupère la liste des rendez-vous d'un résident.

    Args:
        driver: Objet driver Neo4j.
        db_name: Nom de la base de données.
        nom: Nom du résident.
        prenom: Prénom du résident.

    Returns:
        Liste de dictionnaires avec les infos des rendez-vous.
    """
    with driver.session(database=db_name) as session:
        cypher_query = (
            "MATCH (n:Resident {nom:$nom,prenom:$prenom})-[r:Rdv]->(m) "
            "RETURN n.nom, n.prenom, r.date, m.metier, r.commentaire, "
            "r.transport ORDER BY r.date ASC"
        )
        results = session.run(cypher_query, nom=nom, prenom=prenom)
        return [
            {
                'Date': record['r.date'].strftime('%Y-%m-%d %H:%M'),
                'Rendez-vous': record['m.metier'],
                'Transport': record['r.transport'],
                'Note': record['r.commentaire']
            } for record in results
        ]


def get_rdv_types(driver, db_name):
    """
    Récupère la liste des types de rendez-vous (métiers).

    Args:
        driver: Objet Neo4j driver.
        db_name (str): Nom de la base Neo4j.

    Returns:
        list[str]: Liste des métiers.
    """
    rdv_types = []
    with driver.session(database=db_name) as session:
        cypher_query = "MATCH (n:Categorie) RETURN n.metier"
        results = session.run(cypher_query)
        for record in results:
            metier = record['n.metier']
            if metier:
                rdv_types.append(metier)
    return rdv_types


def get_all_rdv_events(driver, db_name):
    """
    Récupère tous les événements de rendez-vous avec leurs propriétés.

    Args:
        driver: Objet Neo4j driver.
        db_name (str): Nom de la base Neo4j.

    Returns:
        list[dict]: Liste de dictionnaires représentant chaque événement.
    """
    with driver.session(database=db_name) as session:
        cypher_query = """
        MATCH (n)-[r]->(m)
        RETURN n.nom, n.prenom, n.etage, n.chambre, type(r), r.date, m.metier,
        r.commentaire, r.rdv
        ORDER BY r.date ASC
        """
        results = session.run(cypher_query)
        events = [
            {
                'Nom': record['n.nom'] + ' ' + record['n.prenom'],
                'Etage': record['n.etage'],
                'Chambre': record['n.chambre'],
                'Date': record['r.date'].strftime('%Y-%m-%d %H:%M'),
                'Rendez-vous': record['m.metier'] if record['type(r)'] == 'Rdv'
                else record['type(r)'] + ' : ' + record['r.rdv'],
                'Note': record['r.commentaire'],
                'Type_Evt': record['type(r)']
            }
            for record in results
        ]
    return events


def add_resident_to_db(driver, db_name, nom, prenom, commentaire, sexe, etage,
                       oxygen, diabete, chambre):
    """
    Crée un nouveau résident dans la base Neo4j avec les propriétés fournies.
    """
    with driver.session(database=db_name) as session:
        session.run(
            """
            CREATE (n:Resident {
                nom: $nom,
                prenom: $prenom,
                commentaire: $commentaire,
                sexe: $sexe,
                etage: $etage,
                chambre: $chambre,
                oxygen: $oxygen,
                diabete: $diabete
            })
            """,
            nom=nom,
            prenom=prenom,
            commentaire=commentaire,
            sexe=sexe,
            etage=etage,
            chambre=chambre,
            oxygen=oxygen,
            diabete=diabete
        )