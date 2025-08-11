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
    get_residents_chambre,
    get_medecins,
    get_service,
    get_resident_properties,
    get_rendez_vous,
    get_rdv_types,
    get_all_rdv_events,
    add_resident_to_db,
    get_rendez_vous_jour,
    ajout_note,
    enregistrer_valeur_selles,
    maj_last_check_selles,
    selles_non_enregistrees,
    get_selles_du_jour,
    get_plusieurs_jours_selles

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
        pks,residents = get_residents_chambre()
        medecins = get_medecins()
        service = get_service()
        return render_template("form.html", residents=residents, medecins=medecins, service=service,pks=pks)


@main_bp.route('/journee', methods=['GET', 'POST'])
def journee():
    manquants=selles_non_enregistrees()
    plusieurs_jours= get_plusieurs_jours_selles()
    print('plusieurs_jours : \n#####\n',plusieurs_jours)
    if request.method == 'POST':
        note = request.form.get('note', '').strip()
        date_note = request.form.get('date_note')
        heure_note = request.form.get('heure_note')
        print(note, date_note, heure_note)
        ajout_note(note, date_note, heure_note)
        
    
    rendez_vous,notes=get_rendez_vous_jour(driver, NEO4J_DB)
    return render_template(
        'recap_jour.html',
        rdv=rendez_vous,
        notes=notes,
        manquants=manquants,
        plusieurs_jours=plusieurs_jours
    )

@main_bp.route('/enregistre_selles', methods=['GET','POST'])
def enregistre_selles():
    if request.method == 'POST':
        data = request.get_json()
        #print("### Données reçues :", data)

        enregistrer_valeur_selles(data)
        maj_last_check_selles(data)

        return jsonify({'status': 'success', 'message': 'Données enregistrées avec succès'})

    # Sinon, méthode GET → on renvoie le tableau HTML
    df_selles_du_jour = pd.DataFrame(get_selles_du_jour())
    aujourdhui = pd.Timestamp.today().normalize()  # sans l'heure
    cols_dates = ['nuit', 'matin', 'soir']  # tes colonnes de dates
    df_selles_du_jour[cols_dates] = df_selles_du_jour[cols_dates].where(
        df_selles_du_jour[cols_dates] == aujourdhui, 
        None
    )
    if df_selles_du_jour.shape == (0,0):
        print('il est broke ton df')
        df_selles_du_jour=pd.DataFrame(columns=['nom', 'prenom', 'moment', 'caracteristique', 'commentaire'])
    else :
        print('df ok')
        for col in ['nuit', 'matin', 'soir']:
            df_none = df_selles_du_jour[df_selles_du_jour[col].isna()].copy()

            # On modifie leur 'caracteristique'
            df_none["caracteristique"] = "--"
            df_none["moment"] = col

            # On concatène les lignes originales avec les nouvelles
            df_selles_du_jour = pd.concat([df_selles_du_jour, df_none], ignore_index=True)
            print("nouveau df")
            print(df_selles_du_jour)
    residents = get_residents()

    def options_html(selected_value):
        options = ['--', 'Normale', 'Liquide', 'Mou', 'Absence']
        return '\n'.join([
            f'<option value="{opt}"{" selected" if opt == selected_value else ""}>{opt}</option>'
            for opt in options
        ])

    def get_val(nom_famille, prenom, moment):
        print(df_selles_du_jour)
        val = df_selles_du_jour.loc[
            (df_selles_du_jour['nom'] == nom_famille) &
            (df_selles_du_jour['prenom'] == prenom) &
            (df_selles_du_jour['moment'] == moment),
            'caracteristique'
        ].values
        if len(val) > 0:
            return val[0]
        elif f"{nom_famille} {prenom}" not in selles_non_enregistrees():
            return 'Absence'
        else:
            return "--"

    table_html = '''
    <div id="sellesPopupContentInner" style="background:#fff; border-radius:18px; box-shadow:0 8px 32px rgba(35,41,70,0.18); padding:32px; max-width:90vw; max-height:80vh; overflow:auto; position:relative;">
        <button onclick="closeSellesPopup()" style="position:absolute; top:18px; right:18px;">Fermer</button>
        <h2>Selles</h2>
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr>
                    <th>Nom</th><th>Nuit</th><th>Matin</th><th>Soir</th><th>Note</th>
                </tr>
            </thead>
            <tbody>
    '''

    for nom in residents:
        parts = nom.split(' ')
        nom_famille = parts[0]
        prenom = parts[1] if len(parts) > 1 else ""

        valeur_nuit = get_val(nom_famille, prenom, 'nuit')
        valeur_matin = get_val(nom_famille, prenom, 'matin')
        valeur_soir = get_val(nom_famille, prenom, 'soir')

        commentaire = df_selles_du_jour.loc[
            (df_selles_du_jour['nom'] == nom_famille) &
            (df_selles_du_jour['prenom'] == prenom),
            'commentaire'
        ].values
        commentaire = commentaire[0] if len(commentaire) > 0 else ""

        safe_nom = nom.replace(" ", "_")

        table_html += f'''
        <tr>
            <td>{nom}</td>
            <td><select id="{safe_nom}-nuit-select">{options_html(valeur_nuit)}</select></td>
            <td><select id="{safe_nom}-matin-select">{options_html(valeur_matin)}</select></td>
            <td><select id="{safe_nom}-soir-select">{options_html(valeur_soir)}</select></td>
            <td><input type="text" value="{commentaire}" placeholder="Note..."></td>
        </tr>
        '''

    table_html += '''
            </tbody>
        </table>
        <div style="text-align:right; margin-top:18px;">
            <button id="validerSellesBtn" onclick="enregistre_selles()">Valider</button>
        </div>
    </div>
    '''

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return table_html
    # Otherwise, return nothing (or a simple message)
    return ''

@main_bp.route('/client_file', methods=['GET', 'POST'])
def client_file():
    pks,residents = get_residents_chambre()
    name = ''
    results = None
    node_result = []

    if request.method == 'POST':
        pk = request.form.get('nomPatientEDT', '').strip()
        if pk:
            
            results = get_resident_properties(driver, NEO4J_DB,
                                                  pk)
            node_result = get_rendez_vous(driver, NEO4J_DB, pk)
        else:
            results = pd.DataFrame()
            node_result = []


    return render_template(
        'client_file.html',
        name=name,
        results=results,
        residents=residents,
        nodes=node_result,
        pks=pks
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
    naissance= request.form.get('date_naissance')

    try:
        add_resident_to_db(driver, NEO4J_DB, nom, prenom, commentaire,
                           sexe, etage, oxygen, diabete, chambre,deplacement,naissance)
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