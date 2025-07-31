# 🏥 Application Web de Gestion Résidents & Rendez-vous (Python + Neo4j)

Cette application web permet de gérer des **résidents**, de planifier des **rendez-vous**, d’afficher un **calendrier**, et de centraliser le tout via une interface web en **Python** (Flask) avec une base de données **Neo4j**.

---

## 🚀 Fonctionnalités principales

- ✅ Ajouter un résident
- ✅ Ajouter un rendez-vous
- ✅ Afficher un calendrier avec récurrence
- ✅ Dashboard synthétique

---

## 📦 Technologies utilisées

| Composant       | Technologie        |
|-----------------|--------------------|
| Backend         | Python (Flask)     |
| Base de données | Neo4j (Cypher)     |
| Frontend        | HTML + CSS (Jinja2)|
| Tests           | `pytest` (optionnel)|

---

## 🗂️ Architecture du projet



mon_appli/
├── main.py                      ← Point d’entrée de l’application
├── requirements.txt             ← Liste des dépendances Python
├── README.md                    ← Présentation du projet

├── app/
│   ├── __init__.py              ← Initialise l'application Flask
│   ├── config.py                ← Paramètres de configuration (Neo4j, debug, etc.)
│   ├── db.py                    ← Connexion à la base Neo4j

│   ├── routes/                  ← Routes web (gestion des URLs)
│   │   ├── __init__.py
│   │   ├── residents.py         ← Routes pour gérer les résidents
│   │   ├── rdv.py               ← Routes pour la gestion des rendez-vous
│   │   ├── calendrier.py        ← Routes pour le calendrier
│   │   └── dashboard.py         ← Accueil / vue synthétique

│   ├── models/                  ← Accès à la base de données (requêtes Cypher)
│   │   ├── __init__.py
│   │   ├── resident_model.py
│   │   ├── rdv_model.py
│   │   └── calendrier_model.py

│   ├── services/                ← Logique métier, validations, utilitaires
│   │   ├── validation.py        ← Validation des données de formulaire
│   │   ├── business_rules.py    ← Règles métier spécifiques
│   │   └── date_utils.py        ← Fonctions de manipulation de dates

│   ├── templates/               ← Fichiers HTML (templates Jinja2)
│   │   ├── base.html
│   │   ├── residents/
│   │   │   └── add_resident.html
│   │   ├── rdv/
│   │   │   └── add_rdv.html
│   │   ├── calendrier/
│   │   │   └── index.html
│   │   └── dashboard.html

│   └── static/                  ← Ressources front-end (CSS, JS, images)
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── script.js

├── tests/                       ← Tests unitaires
│   ├── test_residents.py
│   ├── test_rdv.py
│   └── ...



---

test de md