
from neo4j import GraphDatabase
import os
import pandas as pd
from datetime import datetime, timedelta, date
from flask import (
    Blueprint,
    request,
    render_template,
    jsonify,
    make_response,
    redirect, 
    url_for)
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
    get_plusieurs_jours_selles,
    get_infos_rdv,
    get_all_users,
    update_roles,
    supprimer_rdv,
    supprimer_rdv_chaine,
    get_next_id,
    create_rappel_infini,
    imprimerMultiJours,
    get_personnel

)
from app.routes.auth import login_required, role_required

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASS")
NEO4J_DB = "neo4j"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


main_bp = Blueprint('main', __name__)

# Nouvelle route pour la popup ALT
@main_bp.route('/popup_row_alt', methods=['POST'])
def popup_row_alt():
    """
    Génère le contenu HTML pour la nouvelle popup personnalisée (colonne alt).
    """
    data = request.get_json(force=True)
    html = '<h3 class="noselect" style="margin-top:0; color:#5A8DEE; font-weight:bold;">Informations complémentaires</h3>'
    html += '<table class="noselect" style="width:100%; border-collapse:collapse;">'

    # Oxygène spécifique
    if data.get('oxygen') == 'Oui':
        oxygen_html = '<p class="noselect" style="color: red; font-weight: bold;">Attention : Oxygène requis</p>'
    else:
        oxygen_html = '<p class="noselect" style="color: green; font-weight: bold;">Pas d\'oxygène requis</p>'
    html += oxygen_html

    # Correspondance clé → libellé
    labels = {
        "nom_resident": "Nom résident",
        "Date": "Date",
        "Rendez-vous": "Rendez-vous",
        "Transport": "Transport",
        "Medecin": "Médecin",
        "Lieu": "Lieu",
        "diabete": "Diabète",
        "oxygen": "O₂"
    }

    for key, value in data.items():
        # Si on a un libellé, sinon on met la clé brute
        label = labels.get(key, key)
        key_td = (
            f"<td class='noselect' style='font-weight:600; color:#5A8DEE; padding:6px 10px; border-bottom:1px solid #eee; text-align:left;'>"
            f"{label}</td>"
        )
        value_td = (
            f"<td class='noselect' style='padding:6px 10px; border-bottom:1px solid #eee;'>"
            f"{value}</td>"
        )
        html += f"<tr>{key_td}{value_td}</tr>"

    html += '</table>'
    return make_response(html)




@main_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required("infirmiere","admin")
def form():
    if request.method == 'POST':
        form_data = extract_form_data(request.form)
        
        next_id = get_next_id(driver)
        for individu_pk in form_data['pk']:
            insert_rendez_vous(driver,form_data,individu_pk, next_id, NEO4J_DB)
            create_rappels(driver,form_data,individu_pk, next_id)
        if not form_data.get('fin') : ## si boolean fin est False, on cree un rappel apres 365 jours
            create_rappel_infini(driver,form_data,individu_pk,next_id, NEO4J_DB) # quand il n'y a paz de date de fin, on cree sur 365 jours et ensuite on met un rappel pour qu'ils recréent apres un an
        return "Rendez-vous créés:"
    else:
        pks,residents = get_residents_chambre(driver)
        medecins = get_medecins(driver)
        service = get_service(driver)
        return render_template("form.html", residents=residents, medecins=medecins, service=service,pks=pks)


@main_bp.route('/impression', methods=['GET', 'POST'])
@login_required
@role_required("infirmiere","admin")
def impression():
    rdv_list=imprimerMultiJours(driver)
    return render_template("impression.html",rdv_list=rdv_list)


@main_bp.route('/journee', methods=['GET', 'POST'])
@login_required
@role_required("infirmiere","admin")
def journee():
    manquants=[x['nom'] for x in selles_non_enregistrees(driver)]
    plusieurs_jours= get_plusieurs_jours_selles(driver)
    liste_service= get_personnel(driver)
    print('plusieurs_jours : \n#####\n',plusieurs_jours)
    if request.method == 'POST':
        note = request.form.get('note', '').strip()
        date_note = request.form.get('date_note')
        heure_note = request.form.get('heure_note')
        print(note, date_note, heure_note)
        ajout_note(driver,note, date_note, heure_note)
        
    
    rendez_vous,notes=get_rendez_vous_jour(driver, NEO4J_DB)
    return render_template(
        'recap_jour.html',
        rdv=rendez_vous,
        notes=notes,
        manquants=manquants,
        plusieurs_jours=plusieurs_jours,
        liste_service=liste_service
    )

@main_bp.route('/enregistre_selles', methods=['GET','POST'])
def enregistre_selles():
    if request.method == 'POST':
        data = request.get_json()
        #print("### Données reçues :", data)

        enregistrer_valeur_selles(driver,data)
        maj_last_check_selles(driver,data)

        return jsonify({'status': 'success', 'message': 'Données enregistrées avec succès'})

    # Sinon, méthode GET → on renvoie le tableau HTML
    df_selles_du_jour = pd.DataFrame(get_selles_du_jour(driver))
    aujourdhui = pd.Timestamp.today().normalize()  # sans l'heure
    cols_dates = ['nuit', 'matin', 'apres_midi']  # tes colonnes de dates
    try:
        df_selles_du_jour[cols_dates] = df_selles_du_jour[cols_dates].where(df_selles_du_jour[cols_dates] == aujourdhui, None)
    except :
        df_selles_du_jour=pd.DataFrame(columns=['nom', 'prenom', 'pk', 'moment', 'caracteristique', 'commentaire','nuit','matin','apres_midi'])
    if df_selles_du_jour.empty:
        print('il est broke ton df')
        df_selles_du_jour=pd.DataFrame(columns=['nom', 'prenom', 'pk', 'moment', 'caracteristique', 'commentaire','nuit','matin','apres_midi'])
    else :
        print('df ok')
        for col in ['nuit', 'matin', 'apres_midi']:
            df_none = df_selles_du_jour[df_selles_du_jour[col].isna()].copy()

            # On modifie leur 'caracteristique'
            df_none["caracteristique"] = "--"
            df_none["moment"] = col

            # On concatène les lignes originales avec les nouvelles
            df_selles_du_jour = pd.concat([df_selles_du_jour, df_none], ignore_index=True)
            print("nouveau df")
            print(df_selles_du_jour)
    noms,prenoms,pks = get_residents(driver)

    def options_html(selected_value):
        options = ['--', 'Normale', 'Liquide', 'Mou', 'Absence']
        return '\n'.join([
            f'<option value="{opt}"{" selected" if opt == selected_value else ""}>{opt}</option>'
            for opt in options
        ])

    def get_val(nom_famille, prenom, pk, moment):
        print(df_selles_du_jour)
        val = df_selles_du_jour.loc[
            (df_selles_du_jour['pk'] == pk) &
            (df_selles_du_jour['moment'] == moment),
            'caracteristique'
        ].values
        if len(val) > 0:
            return val[0]
        #elif f"{pk}" not in [x['pk'] for x in selles_non_enregistrees(driver)]:
        #    return 'Absence'
        else:
            return "--"

    table_html = '''
    <div id="sellesPopupContentInner" style="background:#fff; border-radius:18px; box-shadow:0 8px 32px rgba(35,41,70,0.18); padding:32px; max-width:90vw; max-height:80vh; overflow:auto; position:relative;">
        <button onclick="closeSellesPopup()" style="position:absolute; top:18px; right:18px;">Fermer</button>
        <h2>Selles</h2>
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr>
                    <th>Nom</th><th>Nuit</th><th>Matin</th><th>Après-Midi</th><th>Note</th><th style="display:none;">pk</th>
                </tr>
            </thead>
            <tbody>
    '''

    for nom,prenom,pk in zip(noms,prenoms,pks):
        valeur_nuit = get_val(nom, prenom, pk, 'nuit')
        valeur_matin = get_val(nom, prenom, pk, 'matin')
        valeur_apres_midi = get_val(nom, prenom, pk, 'apres_midi')

        commentaire = df_selles_du_jour.loc[
            (df_selles_du_jour['nom'] == nom) &
            (df_selles_du_jour['prenom'] == prenom),
            'commentaire'
        ].values
        commentaire = commentaire[0] if len(commentaire) > 0 else ""
        commentaire =commentaire if commentaire !=None else ""
        nom_complet = f"{nom.replace(' ', '-')} {prenom.replace(' ', '-')}"
        safe_nom = pk.replace(' ', '_')

        table_html += f'''
        <tr>
            <td>{nom_complet}</td>
            <td><select id="{safe_nom}-nuit-select">{options_html(valeur_nuit)}</select></td>
            <td><select id="{safe_nom}-matin-select">{options_html(valeur_matin)}</select></td>
            <td><select id="{safe_nom}-apres_midi-select">{options_html(valeur_apres_midi)}</select></td>
            <td><input type="text" value="{commentaire}" placeholder="Note..."></td>
            <td style="display:none;">{pk}</td>
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
@login_required
@role_required("infirmiere","admin")
def client_file():
    pks,residents = get_residents_chambre(driver)
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
@login_required
@role_required("infirmiere","admin")
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
    html = '<h3 style="margin-top:20px;">Détail du rendez-vous</h3>'
    html += '<table style="width:100%; border-collapse:collapse;">'

    date_parts = data["Date"]
    heure_parts = data["Heure"]
    nom_reserv = data["nom_resident"]
    rdv = data["Rendez-vous"]
    transport = data["Transport"]
    infos = get_infos_rdv(driver,date_parts,heure_parts, nom_reserv, rdv)

    print('infos : ', infos)
    medecin=infos[0].get('medecin', '') if infos[0].get('medecin', '') != None else ''
    html += f"<strong>{nom_reserv}</strong><br>"
    intro= f"""Vous avez rendez vous  "{rdv}" prévu le {date_parts} à {heure_parts}"""
    if medecin != '':
        intro += f", avec : {medecin}. "
    html += intro
    if transport != '---':
        transport_html = f"""<p style="color: #232946; font-weight: bold;">Un transport est prévu pour vous emmener à ce rendez vous : {transport}</p>"""
        html += transport_html
    else:
        transport_html = f"""<p style="color: #232946; font-weight: bold;">Aucun transport n'est prévu pour ce rendez-vous.</p>"""
        html += transport_html
    if len(infos) > 0:
        lieu= infos[0].get('lieu', 'Non spécifié')
        lieu_html = f"""<p style="color: #232946; font-weight: bold;">Lieu du rendez-vous : {lieu}</p>"""
        html += lieu_html


    html += '</table>'
    return make_response(html)

@main_bp.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required("admin")
def admin():
    """
    Route d'administration pour upgrade des user.
    """
    users_dico = get_all_users(driver)
    if request.method == 'POST':
        selected_role = request.form.get("selected_role")
        username = request.form.get("username")
        if selected_role:
            print(f"Rôle sélectionné : {selected_role}, {username}")
            update_roles(driver,username, selected_role)
        else:
            choix = request.form.get('selected_item')
            print('choix : ', choix)
            print('users_dico : ', users_dico[choix])
            liste_roles=["admin","infirmiere","nobody"]
            return render_template('admin.html',
                users_list=users_dico.keys(),
                users_roles=users_dico.values(),
                choix=choix,
                liste_roles=liste_roles 
        )
    
    return render_template(
        'admin.html',
        users_list=users_dico.keys(),
        users_roles=users_dico.values()
    )

@main_bp.route('/supp_one', methods=['GET','POST'])
def supp_one():
    if request.method == 'POST':
        id_one= request.form.get('id_one')
        id_one= int(id_one) if id_one.isdigit() else id_one
        print('id_one : ', id_one)
        supprimer_rdv(driver,id_one)
    return redirect(url_for('main.emploi_collectif'))

@main_bp.route('/supp_all', methods=['GET','POST'])
def supp_all():
    if request.method == 'POST':
        id_chain,date = request.form.get('id_chain').split('_')
        print("date avant : ",date)
        date=date.replace(' ','T')+':00'
        print("date apres : ", date)
        supprimer_rdv_chaine(driver,id_chain,date)
    return redirect(url_for('main.emploi_collectif'))