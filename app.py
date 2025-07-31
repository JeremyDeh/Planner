from flask import Flask, render_template, request, redirect, url_for, jsonify
# --- Pop-up détail ligne planning ---
from flask import make_response
from markupsafe import Markup
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from neo4j import GraphDatabase
import pandas as pd
import os
import openpyxl  # Ajout pour ajuster les colonnes Excel
from datetime import date, datetime, timedelta

def generate_dates(start, end, frequency):
    freq_map = {
        'jour': DAILY,
        'semaine': WEEKLY,
        'mois': MONTHLY
    }

    return list(rrule(freq_map[frequency], dtstart=start, until=end))


app = Flask(__name__)


NEO4J_URI = "bolt://localhost:7687" 
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
NEO4J_DB = "neo4j"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.route('/', methods=['GET', 'POST'])
def form():
    # Récupérer la liste des noms des résidents pour le menu déroulant
    residents = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Resident) RETURN n.nom, n.prenom ORDER BY n.nom, n.prenom"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom']+ ' ' + record['n.prenom'] 
            if nom:
                residents.append(nom)

    medecins = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Categorie) RETURN n.metier ORDER BY n.metier"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.metier'] 
            if nom:
                medecins.append(nom)

    if request.method == 'POST':
        recurrence = request.form.get('fichierCSV', '0')
        
        nomPatient = request.form['nomPatient']
        nom,prenom=nomPatient.split(' ')[0] , nomPatient.split(' ')[1]
        metier = request.form.get('nomMedecin', '')  
        lieu = request.form.get('lieu') 
        commentaire= request.form.get('commentaire', '') 
        transport = request.form.get('transport')  
        date_rdv = request.form.get('date_prestation', '')
        heure_rdv = request.form.get('heure_prestation', '')
        rdv_debut = datetime.fromisoformat(date_rdv+'T'+heure_rdv+':00')
        if recurrence == 'on':
            date_fin = request.form.get('date_fin', '')
            rdv_fin= datetime.fromisoformat(date_fin+'T'+heure_rdv+':00')
            type_recurrence = request.form.get('recurrence')
            date_rdv=generate_dates(rdv_debut, rdv_fin, type_recurrence)
        else :
            date_rdv=[datetime.fromisoformat(date_rdv+'T'+heure_rdv+':00')]   




        colonnes_table = {}
        colonne_ids = sorted({
            key.split('_')[0][3:]
            for key in request.form.keys()
            if key.startswith('col') and key.endswith('_name')
        })

        for i in colonne_ids:
            col_name = request.form.get(f'col{i}_name')
            if col_name:
                colonnes_table[i] = [
                    col_name,
                    request.form.get(f'col{i}_unit'),
                    request.form.get(f'col{i}_nombre'),
                    request.form.get(f'col{i}_pk') or ''
                ]
 

        liste_actions=[x[0] for x in colonnes_table.values()]
  
        
        with driver.session(database=NEO4J_DB) as session:
            for rdv in date_rdv:
                cypher_query = """
                MATCH (n:Resident {nom:$nom, prenom:$prenom})
                MATCH (m:Categorie{metier:$metier})
                CREATE (n)-[r:Rdv {date:$date_str,
                                   transport:$transport,
                                   lieu:$lieu,
                                   commentaire:$commentaire
                            }]->(m) 
                """
                session.run(cypher_query, nom=nom, prenom=prenom, date_str=rdv,recurrence=recurrence,action=liste_actions,commentaire=commentaire,metier=metier,transport=transport, lieu=lieu)
        ##creer les rappels en amont
        date_donnee = datetime(2025, 7, 29)
        jours_avant = 5
        date_resultat = date_donnee - timedelta(days=jours_avant)
        with driver.session(database=NEO4J_DB) as session:
            for rdv in date_rdv:
                for rappel_item in colonnes_table.values():
                    rappel_rdv= rdv - timedelta(days=int(rappel_item[2]))
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
                    session.run(cypher_query, nom=nom, prenom=prenom, type_rdv=metier,date_str=rappel_rdv,date_evt=rdv,action=liste_actions,commentaire=commentaire_rappel,transport=transport, lieu=lieu)



        # Dépendances multiples (depends_on[])
        depends_on_list = request.form.getlist('depends_on')
        depends_on_str = ','.join(depends_on_list) if not recurrence else ''


        return f"Fichier Excel généré :"

    return render_template("form.html", residents=residents,medecins=medecins)


# --- Client file page ---
@app.route('/client_file', methods=['GET', 'POST'])
def client_file():
    residents = []
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Resident) RETURN n.nom, n.prenom ORDER BY n.nom, n.prenom"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.nom']+ ' ' + record['n.prenom'] 
            if nom:
                residents.append(nom)

    name = ''
    results = None
    if request.method == 'POST':
        name = request.form.get('nomPatientEDT', '').strip()
        nom, prenom = name.split(' ')[0], name.split(' ')[1] 
        if name:
            with driver.session(database=NEO4J_DB) as session:
                cypher_query = """
                MATCH (n:Resident {nom:$nom, prenom:$prenom}) RETURN properties(n) as consult
                """
                neo4j_results = session.run(cypher_query, nom=nom, prenom=prenom)
                dicts = [dict(record['consult']) for record in neo4j_results]
                if dicts:
                    df = pd.DataFrame(dicts)
                else:
                    df = pd.DataFrame()
            results = df


            

            with driver.session(database=NEO4J_DB) as session:
                cypher_query = "MATCH (n:Resident {nom:$nom,prenom:$prenom})-[r:Rdv]->(m) RETURN n.nom, n.prenom, r.date, m.metier, r.commentaire, r.transport ORDER BY r.date ASC"
                neo4j_results = session.run(cypher_query,nom=nom, prenom=prenom)
                node_result = [{'Date': record['r.date'].strftime('%Y-%m-%d %H:%M'),# date de la relation
                                'Rendez-vous': record['m.metier'],  
                                'Transport': record['r.transport'], 
                                'Note': record['r.commentaire'] 
                            }for record in neo4j_results
                        ]
        else:
            results = pd.DataFrame()
            node_result = []
    else:
        results = None
        node_result = []

    return render_template('client_file.html', name=name, results=results, residents=residents,nodes=node_result)



# --- Emploi du temps collectif ---
@app.route('/emploi_collectif', methods=['GET'])
def emploi_collectif():
    RDVTypes=[]
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Categorie) RETURN n.metier"
        neo4j_results = session.run(cypher_query)
        for record in neo4j_results:
            nom = record['n.metier'] 
            if nom:
                RDVTypes.append(nom)

    
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n)-[r]->(m) RETURN n.nom, n.prenom, n.etage, n.chambre, type(r), r.date, m.metier, r.commentaire, r.rdv ORDER BY r.date ASC"
        neo4j_results = session.run(cypher_query)
        node_result = [
                                    {
                                        'Nom' : record['n.nom']+' '+record['n.prenom'],      
                                        'Etage': record['n.etage'],
                                        'Chambre' : record['n.chambre'],
                                        'Date': record['r.date'].strftime('%Y-%m-%d %H:%M'),
                                        'Rendez-vous': record['m.metier'] if record['type(r)']=='Rdv' else record['type(r)']+' : '+record['r.rdv'],  
                                        'Note': record['r.commentaire'],   
                                        'Type_Evt': record['type(r)']  # type de la relation (Rdv, Rappel, etc.)
                                    }
                                    for record in neo4j_results
                                ]
    return render_template('emploi_collectif.html', nodes=node_result,RDVTypes=RDVTypes)
# --- Ajout Resident via pop-up ---
@app.route('/add_resident', methods=['POST'])
def add_resident():
    nom = request.form.get('nom')
    prenom = request.form.get('prenom')
    commentaire = request.form.get('commentaire')
    sexe = request.form.get('gender') 
    etage = request.form.get('etage')
    oxygen = request.form.get('O2','0')
    diabete = request.form.get('diabete','0')
    chambre = request.form.get('chambre')
    try:
        with driver.session(database=NEO4J_DB) as session:
            session.run('CREATE (n:Resident {nom:$nom, prenom:$prenom, commentaire:$commentaire, sexe:$sexe, etage:$etage, chambre:$chambre, oxygen:$oxygen, diabete:$diabete})',
                nom=nom, prenom=prenom, commentaire=commentaire, sexe=sexe, etage=etage, oxygen=oxygen, diabete=diabete, chambre=chambre
            )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/agenda')
def agenda():
    
    
    with driver.session(database=NEO4J_DB) as session:
            cypher_query = "MATCH (n:Categorie) RETURN n.metier ORDER BY n.metier ASC"
            neo4j_results = session.run(cypher_query)
            RDVTypes = [x['n.metier'] for x in neo4j_results]
    with driver.session(database=NEO4J_DB) as session:
            cypher_query = "MATCH (n)-[r]->(m) RETURN n.nom, n.prenom, r.date, m.metier, type(r), r.commentaire ORDER BY r.date ASC"
            neo4j_results = session.run(cypher_query)
            node_result = { record['r.date'].isoformat(): [record['n.nom']+' '+record['n.prenom'],
                                                        record['m.metier'], 
                                                        record['r.commentaire'],   
                                                        record['type(r)']  
                                                        ]
                        for record in neo4j_results}
                                    
    events = [
        {
            "title": label[0],
            "start": dt,  # format ISO: "2025-07-08T09:00:00"
            "description": label[1]+' ('+label[3]+') : '+label[2]  
        }
        for dt, label in node_result.items()
    ]
    
    return render_template("agenda.html", events=events,RDVTypes=RDVTypes)
@app.route('/popup_content')
def popup_content():
    return '<h2 style="margin-top:0;">Rendez-vous</h2><p>Ce contenu est chargé depuis Flask !</p>'


@app.route('/popup_row', methods=['POST'])
def popup_row():
    data = request.get_json(force=True)
    html = '<h3 style="margin-top:0;">Détail du rendez-vous</h3>'
    html += '<table style="width:100%; border-collapse:collapse;">'
    html += f'{data["nom_resident"]} a rendez-vous le {data["Date"].split(" ")[0]} à {data["Date"].split(" ")[1]} pour un rendez-vous \"{data["Rendez-vous"]}\" '
    if data['oxygen'] == 'Oui':
        html += '<p style="color: red; font-weight: bold;">Attention : Oxygène requis</p>'
    else :
        html += '<p style="color: green; font-weight: bold;">Pas d\'oxygène requis</p>'
    for key, value in data.items():
        html += f"<tr><td style='font-weight:600; color:#232946; padding:6px 10px; border-bottom:1px solid #eee;'>{key}</td>"
        html += f"<td style='padding:6px 10px; border-bottom:1px solid #eee;'>{value}</td></tr>"
    html += '</table>'
    return make_response(html)



if __name__ == '__main__':
    app.run(debug=True, port=5001)

