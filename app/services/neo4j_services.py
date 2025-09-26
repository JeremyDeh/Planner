from neo4j import GraphDatabase
import os
from datetime import datetime, timedelta, date
from app.services.utils_date import (generate_dates,
                                     generate_smart_weekday_recurrence)
import pandas as pd




def get_personnel(driver, NEO4J_DB="neo4j"):
    """
    Récupère la liste du personnel (médecins et infirmières) depuis la base Neo4j.

    Returns:
        list[str]: Liste des noms du personnel, triés par ordre alphabétique.
    """
    personnel = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Service) RETURN n.nom ORDER BY n.nom"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom']
            if nom:
                personnel.append(nom)
    return personnel

def get_residents(driver, NEO4J_DB="neo4j"):
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

def get_residents_chambre(driver, NEO4J_DB="neo4j"):
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

def get_rendez_vous_jour(driver, NEO4J_DB="neo4j"):
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
                        MATCH (n:Resident)-[r:Rdv]->(m)
                        WHERE date(r.date) = date()
                        RETURN n.nom AS nom, n.prenom AS prenom, n.chambre AS chambre, r.date AS date, r.heure AS heure, r.lieu AS lieu, m.metier AS metier, m.type AS type, r.commentaire AS commentaire, r.responsable AS responsable, 'Note' AS type_element
                        ORDER BY m.metier, n.nom, n.prenom
                        """
        neo4j_results = session.run(cypher_query)
        data = [record.data() for record in neo4j_results]
    df_rdv = pd.DataFrame(data)

    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
                        MATCH (n:Service)-[r]->(m)
                        WHERE r.date = date() OR (r.date is null and r.status=1)
                        RETURN r.date AS date, r.heure AS heure, r.commentaire AS commentaire, m.metier AS metier, ID(r) AS id, r.status AS status, 'PermaNote' AS type_element
                        ORDER BY r.date, m.metier
                        """
        neo4j_results = session.run(cypher_query)
        data = [record.data() for record in neo4j_results]
    df_service = pd.DataFrame(data)
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
                        MATCH (n)-[r:Rappel]->(m)
                        WHERE date(r.date) = date()
                        RETURN r.date AS date, 
                            type(r) + " " + n.nom_affichage + " " + r.date_evt + " " + m.metier + " : " + r.commentaire AS commentaire, ID(r) AS id, r.status AS status, r.heure AS heure,
                            m.metier AS metier, 'Rappel' AS type_element
                        ORDER BY r.date, m.metier
                        """
        neo4j_results = session.run(cypher_query)
        data = [record.data() for record in neo4j_results]
    df_rappel = pd.DataFrame(data)
    df_service = pd.concat([df_service, df_rappel], ignore_index=True)

        
    return df_rdv,df_service

def ajouter_note_persistante(driver,note, metier='Autre',NEO4J_DB="neo4j"):
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
        Match (n:Service {nom:'Infirmières'})
        match (m:Categorie{metier:$metier})
        CREATE (n)-[r:Note { commentaire:$contenu, status:1, create_date:datetime()}]->(m)
        """
        session.run(cypher_query,  contenu=note,metier=metier)

def ajout_note(driver,note, date_note, heure_note,metier='Autre', NEO4J_DB="neo4j"):
    """
    Ajoute une note à la base de données Neo4j.

    Args:
        note (str): Le contenu de la note.
        date_note (str): La date de la note au format 'YYYY-MM-DD'.
        heure_note (str): L'heure de la note au format 'HH:MM'.
    """
    #date_heure = datetime.fromisoformat(f"{date_note}T{heure_note}")
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
        Match (n:Service {nom:'Infirmières'})
        match (m:Categorie{metier:$metier})
        CREATE (n)-[r:Note {date:date($date),heure:$heure, commentaire:$contenu, status:1, create_date:datetime()}]->(m)
        """
        session.run(cypher_query, date=date_note, heure=heure_note, contenu=note,metier=metier)

def get_medecins(driver, NEO4J_DB="neo4j"):

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

def get_next_id(driver, NEO4J_DB="neo4j"):
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
        MATCH ()-[rel:Rdv]-()
        RETURN coalesce(max(rel.id_chain), 0) + 1 AS next_id  

        """
        session.run(
            cypher_query
        )
        result = session.run(cypher_query).single()
        return result["next_id"] if result else 1


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


    pk = form['nomPatients'].split(",")
    metier = form.get('nomMedecin', '')
    service = form.get('nomService', '')
    lieu = form.get('lieu')
    commentaire = form.get('commentaire', '')
    transport = form.get('transport')
    date_rdv = form.get('date_prestation', '')
    heure_rdv = form.get('heure_prestation', '')
    medecin = form.get('identiteMedecin', '')

    rdv_debut = datetime.fromisoformat(date_rdv + 'T' + heure_rdv + ':00') if heure_rdv != '' else date.fromisoformat(date_rdv)
    fin=True
    if recurrence == 'on':
        date_fin = form.get('date_fin', '')
        try:
            rdv_fin = datetime.fromisoformat(date_fin + 'T' + heure_rdv + ':00')
            
        except :
            rdv_fin = rdv_debut + timedelta(days=365)  # Si pas de date fin, on prend un an par défaut
            fin=False
        type_recurrence = form.get('recurrence')

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
        'medecin': medecin,
        'fin': fin
    }


def insert_rendez_vous(driver,data,individu_pk, next_id, NEO4J_DB="neo4j"):
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
            if isinstance(rdv, datetime):
                    date_part = rdv.date()
                    time_part = rdv.time()
            elif isinstance(rdv, date):
                    date_part = rdv
                    time_part = None
            cypher_query = """
            // Puis utilise next_id dans la création
            MATCH (n:Resident {pk: $pk})
            MATCH (m:Categorie {metier: $metier})
            CREATE (n)-[r:Rdv {
                date: date($date),
                heure: localtime($heure),
                transport: $transport,
                lieu: $lieu,
                commentaire: $commentaire,
                responsable: $responsable,
                medecin: $medecin,
                create_date: datetime(),
                id_chain: $next_id
            }]->(m)
            """
            session.run(
                cypher_query,
                date=date_part,
                heure=time_part,
                recurrence=data['recurrence'],
                action=liste_actions,
                commentaire=data['commentaire'],
                metier=data['metier'],
                transport=data['transport'],
                lieu=data['lieu'],
                responsable=data['service'],
                pk= individu_pk,
                medecin= data['medecin'],
                next_id=next_id
            )

def get_service(driver, NEO4J_DB="neo4j"):
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

def create_rappels(driver,data,individu_pk, next_id, NEO4J_DB="neo4j"):
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
                #rappel_rdv = rdv - timedelta(days=int(rappel_item[2]))
                if isinstance(rdv, datetime):
                    rappel_date_part = rdv.date() - timedelta(days=int(rappel_item[2]))
                    rdv_date_part = rdv.date()
                    time_part = rdv.time()
                elif isinstance(rdv, date):
                    rappel_date_part = rdv - timedelta(days=int(rappel_item[2]))
                    rdv_date_part = rdv
                    time_part = None
                commentaire_rappel = rappel_item[0]
                cypher_query = """
                MATCH (n:Resident {pk:$pk})-[s:Rdv{date:$date_evt}]-(o:Categorie{metier:$type_rdv})
                WITH n, o, ID(s) as id_rdv
                CREATE (n)-[r:Rappel {date:$date_str,
                                date_evt:$date_evt,
                                heure:$heure,
                                status:1,
                                rdv:$type_rdv,
                                lieu:$lieu,
                                transport:$transport,
                                commentaire:$commentaire,
                                create_date:datetime(),
                                id_chain: $next_id,
                                id_rdv:id_rdv
                            }]->(o)
                """
                session.run(
                    cypher_query,
                    pk=individu_pk,
                    type_rdv=data['metier'],
                    date_str=rappel_date_part,
                    date_evt=rdv_date_part,
                    heure=time_part,
                    action=None,
                    commentaire=commentaire_rappel,
                    transport=data['transport'],
                    lieu=data['lieu'],
                    next_id=next_id
                )

def create_rappel_infini(driver, data, individu_pk, next_id, NEO4J_DB="neo4j"):
    date_fin =data['date_rdv_list'][-1]## on prend la derniere date 
    pk= individu_pk
    metier = data['metier']

    with driver.session(database=NEO4J_DB) as session:
        cypher_query = ("""
            MATCH (n:Resident {pk:$pk}) 
            MATCH (m:Categorie {metier: $metier})
            CREATE (n)-[r:Rappel {date: date($date_fin), 
                                id_chain: $next_id, 
                                rdv:$metier,
                                commentaire:"Fin de la récurrence, recréér un rendez-vous si toujours en vigueur",
                                create_date:datetime()}]->(m)
            """
        )
        session.run(cypher_query, pk=pk,next_id=next_id,date_fin=date_fin, metier=metier)

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
        cypher_query = ("""
            MATCH (n:Resident {pk:$pk})-[r:Rdv]->(m) 
            RETURN n.nom, n.prenom, r.date, r.heure, m.metier, r.commentaire, r.transport , r.medecin, r.lieu
            ORDER BY r.date ASC"""
        )
        results = session.run(cypher_query, pk=pk)
        return [
            {
                'Date_Fr': record['r.date'].to_native().strftime('%d/%m/%Y'),
                'Date': record['r.date'].to_native().strftime('%Y-%m-%d'),
                'Heure': record['r.heure'].to_native().strftime('%H:%M') if record['r.heure']  else '--:--',
                'Rendez-vous': record['m.metier'],
                'Transport': record['r.transport'],
                'Note': record['r.commentaire'],
                'Medecin': record['r.medecin'],
                'Lieu': record['r.lieu'],
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
        RETURN n.nom, n.prenom, n.etage, n.chambre, type(r), r.date, r.heure, m.metier,
        r.commentaire, r.rdv, ID(r) as id_rdv_one, r.id_chain AS id_chain
        ORDER BY toString(r.date) ASC
        """
        ## on doit order by toString() car sans le cast, il differencie les dates et les datetime etfait son tr séparémment
        results = session.run(cypher_query)
        events = [
            {
                'Nom': record['n.nom'] + ' ' + record['n.prenom'],
                'Etage': record['n.etage'],
                'Chambre': record['n.chambre'],
                'Date_Fr': record['r.date'].to_native().strftime('%d/%m/%Y') if not record['r.heure'] else record['r.date'].to_native().strftime('%d/%m/%Y')+' '+ record['r.heure'].to_native().strftime('%H:%M'),
                'Date': record['r.date'].to_native().strftime('%Y-%m-%d') if not record['r.heure'] else record['r.date'].to_native().strftime('%Y-%m-%d')+'T'+ record['r.heure'].to_native().strftime('%H:%M:%S'),
                'Rendez-vous': record['m.metier'] if record['type(r)'] == 'Rdv' else record['type(r)'] + ' : ' + record['r.rdv'],
                'Note': record['r.commentaire'],
                'Type_Evt': record['type(r)'],
                'ID_one': record['id_rdv_one'],
                'ID_chain': record['id_chain']
            }
            for record in results
        ]
    return events


def add_resident_to_db(driver, NEO4J_DB, nom, prenom, commentaire, sexe, etage,
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

def enregistrer_valeur_selles(driver,data,NEO4J_DB='neo4j'): # on n'enregistre pas les données "Absence"
 
    data_f = []
    for nom_complet in data.keys():
        
        nom, prenom = nom_complet.split(" ", 1)
        for moment in ["nuit", "matin", "apres_midi"]:
            if data[nom_complet][moment] != "--" :##and  data[nom_complet][moment] != "Absence" :
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
def maj_last_check_selles(driver, data, NEO4J_DB='neo4j'): 

    data_f = []
    for noms_complet in data.keys():  # original_data contient les noms complets
        nom,prenom = noms_complet.split(" ")
        
        data_f.append({"nom": nom, "prenom": prenom, "pk":data[noms_complet]['pk'], "liste":['nuit' if data[noms_complet]['nuit']!='--' else None,'matin' if data[noms_complet]['matin']!='--' else None,'apres_midi' if data[noms_complet]['apres_midi']!='--' else None ]}) if any([valeur !='--' for valeur in (data[noms_complet]['nuit'],data[noms_complet]['matin'],data[noms_complet]['apres_midi']) ]) else None

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
            n.derniere_verif_selles_apres_midi = CASE
                WHEN 'apres_midi' in row.liste THEN date()
                ELSE n.derniere_verif_selles_apres_midi
            END
            """,
            data=data_f
        )# derniere_verif_selles correspond a la derniere fois qu'on a mis a jour les selles pour la personne, mais il peut ne pas y avoir de selles enregistrées si on a verifié mais qu'elle n'a pas été a la selle ce jour, cela sert juste a verifer les oubli d'enregistrement de la part des personnes en charge
def selles_non_enregistrees(driver, NEO4J_DB='neo4j'):
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
def get_selles_du_jour(driver, NEO4J_DB='neo4j'):
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
                   r.caracteristique AS caracteristique, m.commentaire AS commentaire, n.derniere_verif_selles_nuit, n.derniere_verif_selles_matin, n.derniere_verif_selles_apres_midi
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
                'apres_midi': record['n.derniere_verif_selles_apres_midi']
            } for record in results
    ]
    return maListe
def get_plusieurs_jours_selles(driver, NEO4J_DB='neo4j'):
    """
    Récupère les enregistrements de selles pour les derniers jours.

    Returns:
        list[dict]: Liste de dictionnaires contenant les informations des selles.
    """
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
           MATCH (n:Resident)
            WHERE NOT EXISTS {
                MATCH (n)<-[r:Par]-(m:Selles)
                WHERE r.caracteristique <> 'Absence' AND duration.between(m.date, date()).days < 2
            }
            OPTIONAL MATCH (n)<-[s:Par]-(m:Selles) WHERE s.caracteristique <> 'Absence'
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
def get_infos_rdv(driver,date,heure, nom_full, rdv,pk='', NEO4J_DB='neo4j'):
    nom=nom_full.split(" ")[0]
    prenom =nom_full.split(" ")[1]
    #date=date+':00'

    # Si la date contient 'T00', cela signifie qu'il n'y a pas d'heure réelle
    date=date
    heure=heure
    
    print(f"ma date : {date}")
    print('get_infos_rdv : ',date, nom, prenom, rdv)
    date_iso = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")### reformatter la date fr en date isoo pour la BDD
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
           MATCH (n:Resident {nom:$nom, prenom:$prenom})-[r:Rdv ]->(m:Categorie {metier:$rdv}) WHERE r.date = date($date) and r.heure=localtime($heure)
        RETURN r.lieu AS lieu, r.medecin AS medecin, r.commentaire AS commentaire, r.transport AS transport, n.deplacement AS deplacement, n.oxygen AS oxygen, n.diabete AS diabete

        """
        results = session.run(cypher_query,nom=nom,prenom=prenom,date=date_iso, heure=heure,rdv=rdv)
        data= [dict(record) for record in results]
        print("data sortie fonction : ",data)
        return  data
    
def get_all_users(driver, NEO4J_DB='neo4j'):
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
def update_roles(driver,username, role, NEO4J_DB='neo4j'):
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

def supprimer_rdv(driver,id_rdv, NEO4J_DB='neo4j'):
    """
    Supprime un rendez-vous spécifique de la base Neo4j.

    Args:
        id_rdv (int): ID du rendez-vous à supprimer.
    """
    print("je tente de supprimer le rdv : ",id_rdv)
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH ()-[r]->()
            WHERE ID(r) = $id_rdv or r.id_rdv = $id_rdv
            DELETE r
        """
        session.run(cypher_query, id_rdv=id_rdv)


def supprimer_rdv_chaine(driver, id_rdv,date, NEO4J_DB='neo4j'):
    """
    Supprime un rendez-vous spécifique de la base Neo4j.

    Args:
        id_rdv (int): ID du rendez-vous à supprimer.
    """
    id_rdv = int(id_rdv) if isinstance(id_rdv, str) else id_rdv
    print("dates a supprimer : ",date)
    if 'T' in date :
        date =date.split("T")[0]
        #heure=date.split("T")[1] 
        date_iso = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
    elif ' ' in date :
        print(date)
        date =date.split(" ")[0]
        #heure=date.split(" ")[1] 
        date_iso = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        date_iso = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
        #heure=None  
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n)-[r:Rdv]->()
            WHERE (r.id_chain = $id_rdv AND r.date >= date($date)) 
            WITH r, ID(r) AS id_rdv_rappel
            OPTIONAL MATCH ()-[s:Rappel]->()
            WHERE s.id_rdv = id_rdv_rappel
            DELETE r,s
        """
        session.run(cypher_query, id_rdv=id_rdv,date=date_iso)

def imprimerMultiJours(driver,NEO4J_DB='neo4j'):
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
            MATCH (n:Resident)-[r:Rdv]-(m:Categorie)
            WITH n, m, r, date(substring(toString(r.date), 0, 10)) AS rdvDate
            WHERE rdvDate >= date()
            AND rdvDate <= date() + duration('P7D')
            RETURN n.nom AS nom, n.chambre AS chambre, n.prenom AS prenom, m.metier AS typeRdv, r.date as date, r.heure as heure, r.medecin as nomMedecin, r.lieu AS lieu, r.commentaire AS commentaire, r.transport AS transport, n.oxygen AS oxygene
            ORDER BY rdvDate, r.date

        """
        result = session.run(cypher_query)
        liste_rdv = [dict(record) for record in result]
        print("liste rdv impression : ", liste_rdv)
    return liste_rdv
