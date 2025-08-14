from neo4j import GraphDatabase
import os
from datetime import datetime, timedelta, date
from app.services.utils_date import (generate_dates,
                                     generate_smart_weekday_recurrence)
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
    residents_noms = []
    residents_prenoms = []
    pks = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """MATCH (n:Resident) RETURN n.nom, n.prenom, n.pk
                       ORDER BY n.nom, n.prenom, n.pk"""
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
                residents_noms.append(record['n.nom'])
                residents_prenoms.append(record['n.prenom'])
                pks.append(record['n.pk'])
    return residents_noms, residents_prenoms, pks

def get_residents_chambre():
    """
    Récupère la liste des noms complets des résidents depuis la base Neo4j.

    Returns:
        list[str]: Liste des noms complets des résidents,
        triés par nom puis prénom.
    """
    residents = []
    pks = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """MATCH (n:Resident) RETURN n.nom, n.prenom, n.chambre, n.pk
                       ORDER BY n.nom, n.prenom, n.chambre"""
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom'] + ' ' + record['n.prenom'] + ' (Chambre ' + str(record['n.chambre']) + ')'
            pk = record['n.pk']
            if nom:
                residents.append(nom)
                pks.append(pk)
    return pks,residents

def get_rendez_vous_jour(driver, NEO4J_DB):
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
                        MATCH (n:Resident)-[r]->(m)
                        WHERE date(r.date) = date()
                        RETURN n.nom AS nom, n.prenom AS prenom, r.date AS date, r.lieu AS lieu, m.metier AS metier, r.commentaire AS commentaire
                        ORDER BY m.metier, n.nom, n.prenom
                        """
        neo4j_results = session.run(cypher_query)
        data = [record.data() for record in neo4j_results]
    df_rdv = pd.DataFrame(data)

    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
                        MATCH (n:Service)-[r]->(m)
                        WHERE date(r.date) = date()
                        RETURN r.date AS date, r.commentaire AS commentaire, m.metier AS metier
                        ORDER BY m.metier
                        """
        neo4j_results = session.run(cypher_query)
        data = [record.data() for record in neo4j_results]
    df_service = pd.DataFrame(data)

    
    return df_rdv,df_service


def ajout_note(note, date_note, heure_note,metier='Autre'):
    """
    Ajoute une note à la base de données Neo4j.

    Args:
        note (str): Le contenu de la note.
        date_note (str): La date de la note au format 'YYYY-MM-DD'.
        heure_note (str): L'heure de la note au format 'HH:MM'.
    """
    date_heure = datetime.fromisoformat(f"{date_note}T{heure_note}")
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
        Match (n:Service {nom:'Infirmières'})
        match (m:Categorie{metier:$metier})
        CREATE (n)-[r:Note {date:datetime($date),commentaire:$contenu, create_date:datetime()}]->(m)
        """
        session.run(cypher_query, date=date_heure, contenu=note,metier=metier)

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

    pk = form['nomPatient']
    metier = form.get('nomMedecin', '')
    service = form.get('nomService', '')
    lieu = form.get('lieu')
    commentaire = form.get('commentaire', '')
    transport = form.get('transport')
    date_rdv = form.get('date_prestation', '')
    heure_rdv = form.get('heure_prestation', '')
    medecin = form.get('identiteMedecin', '')

    rdv_debut = datetime.fromisoformat(date_rdv + 'T' + heure_rdv + ':00') if heure_rdv != '' else date.fromisoformat(date_rdv)

    if recurrence == 'on':
        date_fin = form.get('date_fin', '')
        rdv_fin = datetime.fromisoformat(date_fin + 'T' + heure_rdv + ':00')
        type_recurrence = form.get('recurrence')
        print(type_recurrence)

        if type_recurrence == 'mois':
            date_rdv_list = generate_smart_weekday_recurrence(rdv_debut,
                                                              rdv_fin)
        else:
            date_rdv_list = generate_dates(rdv_debut,
                                           rdv_fin,
                                           type_recurrence)
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
        'metier': metier,
        'lieu': lieu,
        'commentaire': commentaire,
        'transport': transport,
        'date_rdv_list': date_rdv_list,
        'colonnes_table': colonnes_table,
        'service': service,
        'pk': pk,
        'medecin': medecin
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
            MATCH (n:Resident {pk:$pk})
            MATCH (m:Categorie{metier:$metier})
            CREATE (n)-[r:Rdv {date:$date_str,
                               transport:$transport,
                               lieu:$lieu,
                               commentaire:$commentaire,
                               responsable:$responsable,
                               medecin:$medecin,
                               create_date:datetime()
                        }]->(m)
            """
            session.run(
                cypher_query,
                date_str=rdv,
                recurrence=data['recurrence'],
                action=liste_actions,
                commentaire=data['commentaire'],
                metier=data['metier'],
                transport=data['transport'],
                lieu=data['lieu'],
                responsable=data['service'],
                pk= data['pk'],
                medecin= data['medecin']
            )

def get_service():
    """
    Récupère la liste des services (médecins) depuis la base Neo4j.

    Returns:
        list[str]: Liste des noms de services (médecins).
    """
    service = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Service) RETURN n.nom ORDER BY n.nom"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom']
            if nom:
                service.append(nom)
    return service

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
                                commentaire:$commentaire,
                                create_date:datetime()
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


def get_resident_properties(driver, db_name, pk):
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
            "MATCH (n:Resident {pk:$pk}) "
            "RETURN properties(n) as consult"
        )
        results = session.run(cypher_query, pk=pk)
        dicts = [dict(record['consult']) for record in results]
        if dicts:
            return pd.DataFrame(dicts)
        else:
            return pd.DataFrame()


def get_rendez_vous(driver, db_name, pk):
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
            "MATCH (n:Resident {pk:$pk})-[r:Rdv]->(m) "
            "RETURN n.nom, n.prenom, r.date, m.metier, r.commentaire, "
            "r.transport ORDER BY r.date ASC"
        )
        results = session.run(cypher_query, pk=pk)
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
        MATCH (n:Resident)-[r]->(m)
        RETURN n.nom, n.prenom, n.etage, n.chambre, type(r), r.date, m.metier,
        r.commentaire, r.rdv
        ORDER BY toString(r.date) ASC
        """
        ## on doit order by toString() car sans le cast, il differencie les dates et les datetime etfait son tr séparémment
        results = session.run(cypher_query)
        events = [
            {
                'Nom': record['n.nom'] + ' ' + record['n.prenom'],
                'Etage': record['n.etage'],
                'Chambre': record['n.chambre'],
                'Date': record['r.date'].strftime('%Y-%m-%d %H:%M') if 'T' in str(record['r.date']) else record['r.date'].strftime('%Y-%m-%d'),
                'Rendez-vous': record['m.metier'] if record['type(r)'] == 'Rdv'
                else record['type(r)'] + ' : ' + record['r.rdv'],
                'Note': record['r.commentaire'],
                'Type_Evt': record['type(r)']
            }
            for record in results
        ]
    return events


def add_resident_to_db(driver, db_name, nom, prenom, commentaire, sexe, etage,
                       oxygen, diabete, chambre,deplacement,naissance):
    """
    Crée un nouveau résident dans la base Neo4j avec les propriétés fournies.
    """
    with driver.session(database=NEO4J_DB) as session:
        session.run(
            """
            CREATE (n:Resident {
                nom: $nom,
                prenom: $prenom,
                commentaire: $commentaire,
                sexe: $sexe,
                etage: $etage,
                chambre: $chambre,
                deplacement: $deplacement,
                oxygen: $oxygen,
                diabete: $diabete,
                naissance: date($naissance),
                pk : $pk,
                nom_affichage: $nom_affichage
            })
            """,
            nom=nom.upper(),
            prenom=prenom.capitalize(),
            commentaire=commentaire,
            sexe=sexe,
            etage=etage,
            chambre=chambre,
            deplacement=deplacement,
            oxygen=oxygen,
            diabete=diabete,
            naissance=naissance,
            pk=nom.upper().replace(' ', '-') + '_' + prenom.capitalize().replace(' ', '-') + '_' + naissance,
            nom_affichage=nom.upper() + ' ' + prenom.capitalize()
        )

def enregistrer_valeur_selles(data): # on n'enregistre pas les données "Absence"
    print('data : ',data)
 
    data_f = []
    for nom_complet in data.keys():
        
        nom, prenom = nom_complet.split(" ", 1)
        for moment in ["nuit", "matin", "soir"]:
            if data[nom_complet][moment] != "--" and  data[nom_complet][moment] != "Absence" :
                data_f.append({
                    "nom": nom,
                    "prenom": prenom,
                    "moment": moment,
                    "caracteristique": data[nom_complet][moment],
                    "note": data[nom_complet].get("note", ""),
                    'pk': data[nom_complet].get("pk", "")
                }) 

    with driver.session(database=NEO4J_DB) as session:
        session.run(
            """
            UNWIND $data AS row
            MATCH (n:Resident {pk: row.pk})
            MERGE (m:Selles {
                date: date(),
                moment_date: row.moment,
                commentaire: row.note
            })
            MERGE (m)-[r:Par ]->(n) SET r.caracteristique = row.caracteristique
            """,
            data=data_f
        )
def maj_last_check_selles(data) :
    print(data)

    data_f = []
    for noms_complet in data.keys():  # original_data contient les noms complets
        nom,prenom = noms_complet.split(" ")
        data_f.append({"nom": nom, "prenom": prenom, "pk":data[noms_complet]['pk'], "liste":['nuit' if data[noms_complet]['nuit']!='--' else None,'matin' if data[noms_complet]['matin']!='--' else None,'soir' if data[noms_complet]['soir']!='--' else None ]}) if any([valeur !='--' for valeur in (data[noms_complet]['nuit'],data[noms_complet]['matin'],data[noms_complet]['soir']) ]) else None
        print('data_f : ',data_f)
    with driver.session(database=NEO4J_DB) as session:
        session.run(
            """
            UNWIND $data AS row
            MATCH (n:Resident {pk:row.pk})
            SET n.derniere_verif_selles = date()
            SET n.derniere_verif_selles_nuit = CASE 
                WHEN 'nuit' in row.liste  THEN date()
                ELSE n.derniere_verif_selles_nuit
            END,
            n.derniere_verif_selles_matin = CASE
                WHEN 'matin' in row.liste THEN date()
                ELSE n.derniere_verif_selles_matin
            END,
            n.derniere_verif_selles_soir = CASE
                WHEN 'soir' in row.liste THEN date()
                ELSE n.derniere_verif_selles_soir
            END
            """,
            data=data_f
        )# derniere_verif_selles correspond a la derniere fois qu'on a mis a jour les selles pour la personne, mais il peut ne pas y avoir de selles enregistrées si on a verifié mais qu'elle n'a pas été a la selle ce jour, cela sert juste a verifer les oubli d'enregistrement de la part des personnes en charge
def selles_non_enregistrees():
    """
    Récupère la liste des résidents pour lesquels les selles n'ont pas été
    enregistrées aujourd'hui.

    Returns:
        results, a recuperer en dehors der la fonction sous la forme [x['nom'] for x in results] ou [x['pk'] for x in results]
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n:Resident)
            WHERE n.derniere_verif_selles is null OR n.derniere_verif_selles < date()
            RETURN n.pk AS pk, n.nom_affichage AS nom 
            ORDER BY n.nom_affichage
        """
        results = session.run(cypher_query)
        results = [dict(record) for record in results]
        return  results
def get_selles_du_jour():
    """
    Récupère les enregistrements de selles pour la journée en cours.

    Returns:
        list[dict]: Liste de dictionnaires contenant les informations des selles.
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n:Resident)
            OPTIONAL MATCH (m:Selles)-[r:Par]->(n)
            WHERE n.derniere_verif_selles = date()
            RETURN n.nom AS nom, n.prenom AS prenom, n.pk AS pk, m.moment_date AS moment,
                   r.caracteristique AS caracteristique, m.commentaire AS commentaire, n.derniere_verif_selles_nuit, n.derniere_verif_selles_matin, n.derniere_verif_selles_soir
            ORDER BY n.nom, n.prenom, m.moment_date

        """
        results = session.run(cypher_query)
        maListe = [
            {
                'nom': record['nom'],
                'prenom': record['prenom'],
                'pk': record['pk'],
                'moment': record['moment'],
                'caracteristique': record['caracteristique'],
                'commentaire': record['commentaire'],
                'nuit': record['n.derniere_verif_selles_nuit'],
                'matin': record['n.derniere_verif_selles_matin'],
                'soir': record['n.derniere_verif_selles_soir']
            } for record in results
    ]
    print("get_selles_du_jour : ",maListe)
    return maListe
def get_plusieurs_jours_selles():
    """
    Récupère les enregistrements de selles pour les derniers jours.

    Returns:
        list[dict]: Liste de dictionnaires contenant les informations des selles.
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
           MATCH (n:Resident)
            WHERE NOT EXISTS {
                MATCH (n)<-[:Par]-(m:Selles)
                WHERE duration.between(m.date, date()).days < 2
            }
            OPTIONAL MATCH (n)<-[:Par]-(m:Selles)
            WITH n,max(m.date) AS Date
            RETURN n.nom AS Nom, n.prenom AS Prenom, n.pk AS pk, Date, duration.between(Date, date()).days as Jours
            ORDER BY n.nom, n.prenom

        """
        results = session.run(cypher_query)
        df = pd.DataFrame([dict(record) for record in results])
        #df['Jours'] = df['Jours'].fillna("-1")
        if not df.empty:
            df['Date'] = df['Date'].fillna("--")
            df['Jours'] = df['Jours'].astype('Int32') 
        return  df #df.fillna("--")
def get_infos_rdv(date, nom_full, rdv,pk=''):
    nom=nom_full.split(" ")[0]
    prenom =nom_full.split(" ")[1]
    date=date+':00'
    print('get_infos_rdv : ',date, nom, prenom, rdv)
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
           MATCH (n:Resident {nom:$nom, prenom:$prenom})-[r:Rdv ]->(m:Categorie {metier:$rdv}) WHERE toString(r.date) = $date
        RETURN r.lieu AS lieu, r.medecin AS medecin, r.commentaire AS commentaire, r.transport AS transport, n.deplacement AS deplacement, n.oxygen AS oxygen, n.diabete AS diabete

        """
        results = session.run(cypher_query,nom=nom,prenom=prenom,date=date,rdv=rdv)
        data= [dict(record) for record in results]
 
        return  data
    
def get_all_users():
    """
    Récupère la liste de tous les utilisateurs (username) dans la base Neo4j.

    Returns:
        dict:  dico contenant les usernames et roles.
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n:Auth)
            RETURN n.user AS username, n.role AS role, n.pk AS pk
            ORDER BY n.user
        """
        results = session.run(cypher_query)
        return {record['username']:[record['role']] for record in results}
def update_roles(username, role):
    """
    Met à jour les rôles d'un utilisateur dans la base Neo4j.

    Args:
        username (str): Nom d'utilisateur à mettre à jour.
        roles (list[str]): Liste des rôles à attribuer.
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n:Auth {user: $username})
            SET n.role = $role
        """
        session.run(cypher_query, username=username, role=role)