from neo4j import GraphDatabase
import os
import pandas as pd
from flask import (
    Blueprint,
    request,
    render_template,
    jsonify,
    make_response)
from app.services import (
    extract_form_data,
    insert_rendez_vous,
    create_rappels,
    get_residents,
    get_medecins,
    get_service,
    get_resident_properties,
    get_rendez_vous,
    get_rdv_types,
    get_all_rdv_events,
    add_resident_to_db,
    get_rendez_vous_jour,
    ajout_note,
)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
NEO4J_DB = "neo4j"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        form_data = extract_form_data(request.form)
        insert_rendez_vous(form_data)
        create_rappels(form_data)
        return "Fichier Excel généré :"
    else:
        residents = get_residents()
        medecins = get_medecins()
        service = get_service()
        return render_template("form.html", residents=residents, medecins=medecins, service=service)


@main_bp.route('/journee', methods=['GET', 'POST'])
def journee():

    if request.method == 'POST':
        note = request.form.get('note', '').strip()
        date_note = request.form.get('date_note')
        heure_note = request.form.get('heure_note')
        print(note, date_note, heure_note)
        ajout_note(note, date_note, heure_note)
    
    rendez_vous,notes=get_rendez_vous_jour(driver, NEO4J_DB)
    print("Rendez-vous du jour:", rendez_vous)
    return render_template(
        'recap_jour.html',
        rdv=rendez_vous,
        notes=notes
    )

@main_bp.route('/enregistre_selles', methods=['GET','POST'])
def enregistre_selles():
    if request.method == 'POST':
        data = request.get_json()
        print("Données reçues:", data)

        enregistrer_valeur_selles(data) # on n'enregistre pas les données "Absence"
        maj_last_check_selles(data) # sert a faire la distinction entre une absence de donnée parce que le mec a pas fait de la journée, et l'absence de donnée parce que les personnes ont oublié de remplir

        # Traitez les données ici, par exemple, en les enregistrant dans la base de données
        return jsonify({'status': 'success', 'message': 'Données enregistrées avec succès'})
    return render_template('enregistre_selles.html')

@main_bp.route('/client_file', methods=['GET', 'POST'])
def client_file():
    residents = get_residents()
    name = ''
    results = None
    node_result = []

    if request.method == 'POST':
        name = request.form.get('nomPatientEDT', '').strip()
        if name:
            try:
                nom, prenom = name.split(' ')[0], name.split(' ')[1]
            except IndexError:
                # Gérer le cas où il manque prénom ou nom
                nom, prenom = '', ''

            if nom and prenom:
                results = get_resident_properties(driver, NEO4J_DB,
                                                  nom, prenom)
                node_result = get_rendez_vous(driver, NEO4J_DB, nom, prenom)
            else:
                results = pd.DataFrame()
                node_result = []
        else:
            results = pd.DataFrame()
            node_result = []

    return render_template(
        'client_file.html',
        name=name,
        results=results,
        residents=residents,
        nodes=node_result
    )


@main_bp.route('/emploi_collectif', methods=['GET'])
def emploi_collectif():
    rdv_types = get_rdv_types(driver, NEO4J_DB)
    events = get_all_rdv_events(driver, NEO4J_DB)
    events2= [ {"title": x["Nom"], "start" : x["Date"], "description":f"{x['Rendez-vous']} ({x['Type_Evt']}) : {x['Note']}", "Etage":x['Etage']} for x in events]


    return render_template('emploi_collectif.html', nodes=events,
                           RDVTypes=rdv_types,events=events2)


@main_bp.route('/add_resident', methods=['POST'])
def add_resident():
    nom = request.form.get('nom')
    prenom = request.form.get('prenom')
    commentaire = request.form.get('commentaire')
    sexe = request.form.get('gender')
    etage = request.form.get('etage')
    oxygen = request.form.get('O2', '0')
    diabete = request.form.get('diabete', '0')
    chambre = request.form.get('chambre')
    deplacement = request.form.get('deplacement', 'Seul')

    try:
        add_resident_to_db(driver, NEO4J_DB, nom, prenom, commentaire,
                           sexe, etage, oxygen, diabete, chambre,deplacement)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@main_bp.route('/agenda')
def agenda():
    with driver.session(database=NEO4J_DB) as session:
        cypher_query = "MATCH (n:Categorie) RETURN n.metier " \
                       "ORDER BY n.metier ASC"
        neo4j_results = session.run(cypher_query)
        RDVTypes = [x['n.metier'] for x in neo4j_results]

    with driver.session(database=NEO4J_DB) as session:
        cypher_query = """
        MATCH (n:Resident)-[r]->(m)
        RETURN n.nom, n.prenom, r.date, m.metier, type(r), r.commentaire
        ORDER BY r.date ASC
        """
        neo4j_results = session.run(cypher_query)
        node_result = {
            record['r.date'].isoformat(): [
                record['n.nom'] + ' ' + record['n.prenom'],
                record['m.metier'],
                record['r.commentaire'],
                record['type(r)']
            ] for record in neo4j_results
        }

    events = [
        {
            "title": label[0],
            "start": dt,
            "description": f"{label[1]} ({label[3]}) : {label[2]}"
        }
        for dt, label in node_result.items()
    ]

    return render_template("agenda.html", events=events, RDVTypes=RDVTypes)


@main_bp.route('/popup_content')
def popup_content():
    """
    Retourne un contenu HTML simple pour le popup rendez-vous.
    """
    return (
        '<h2 style="margin-top:0;">Rendez-vous</h2>'
        '<p>Ce contenu est chargé depuis Flask !</p>'
    )


@main_bp.route('/popup_row', methods=['POST'])
def popup_row():
    """
    Génère le contenu HTML détaillé pour un rendez-vous depuis
    les données JSON.
    """
    data = request.get_json(force=True)
    html = '<h3 style="margin-top:0;">Détail du rendez-vous</h3>'
    html += '<table style="width:100%; border-collapse:collapse;">'

    date_parts = data["Date"].split(" ")
    nom_reserv = data["nom_resident"]
    rdv = data["Rendez-vous"]

    intro = (f'{nom_reserv} a rendez-vous le {date_parts[0]} à {date_parts[1]}'
             f'pour un rendez-vous "{rdv}" ')
    html += intro

    if data.get('oxygen') == 'Oui':
        oxygen_html = (
            '<p style="color: red; font-weight: bold;">'
            'Attention : Oxygène requis</p>'
        )
    else:
        oxygen_html = (
            '<p style="color: green; font-weight: bold;">'
            'Pas d\'oxygène requis</p>'
        )
    html += oxygen_html

    for key, value in data.items():
        key_td = (
            "<td style='font-weight:600; color:#232946; padding:6px 10px;"
            " border-bottom:1px solid #eee;'>"
            f"{key}</td>"
        )
        value_td = (
            "<td style='padding:6px 10px; border-bottom:1px solid #eee;'>"
            f"{value}</td>"
        )
        row = f"<tr>{key_td}{value_td}</tr>"
        html += row

    html += '</table>'
    return make_response(html)
