import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timedelta
# Définit les scopes nécessaires
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Authentification avec Google Sheets
def authenticate_gsheet():
    creds = Credentials.from_service_account_file('inv-75001-5846b74316ed.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

# Charger les données de Google Sheets
def load_data(sheet_name):
    client = authenticate_gsheet()
    sheet = client.open("RECETTE ET COUTS ANNEX").worksheet("sheet1")
    data = pd.DataFrame(sheet.get_all_records())
    return data

# Ajouter une nouvelle entrée
def add_entry(nom, quantite):
    client = authenticate_gsheet()
    sheet = client.open("RECETTE ET COUTS ANNEX").worksheet("sheet2")
    sheet.append_row([None, nom, quantite, pd.Timestamp.now()])

def move_old_entries():
    client = authenticate_gsheet()
    inventaire_sheet = client.open("RECETTE ET COUTS ANNEX").worksheet("sheet2")
    historique_sheet = client.open("RECETTE ET COUTS ANNEX").worksheet("sheet3")
    
    # Charger les données de l'inventaire
    inventaire_data = pd.DataFrame(inventaire_sheet.get_all_records())
    
    print("Colonnes disponibles :", inventaire_data.columns)

    # Vérifier si "Date" existe
    if "Date" not in inventaire_data.columns:
        st.error("La colonne 'Date' n'existe pas dans la feuille 'Inventaire'.")
        return
    
    # Convertir la colonne 'Date' en format datetime
    inventaire_data['Date'] = pd.to_datetime(inventaire_data['Date'], errors='coerce')

    # Filtrage des données plus anciennes qu'un mois
    cutoff_date = datetime.now() - timedelta(days=30)
    old_entries = inventaire_data[inventaire_data['Date'] < cutoff_date]
    
    # Si des entrées anciennes existent, les ajouter à l'historique
    if not old_entries.empty:
        for index, row in old_entries.iterrows():
            historique_sheet.append_row(row.tolist())  # Ajoute chaque ligne à l'historique
        # Supprimer les anciennes entrées de l'inventaire
        inventaire_data = inventaire_data[inventaire_data['Date'] >= cutoff_date]
        inventaire_sheet.clear()  # Efface les données existantes
        inventaire_sheet.append_row(list(inventaire_data.columns))  # Ajoute les en-têtes
        for index, row in inventaire_data.iterrows():
            inventaire_sheet.append_row(row.tolist())  # Ajout des lignes restantes

def add_entry(nom, quantite):
    client = authenticate_gsheet()
    sheet = client.open("RECETTE ET COUTS ANNEX").worksheet("sheet2")
    sheet.append_row([None, nom, quantite, pd.Timestamp.now().strftime('%Y-%m-%d')])

# Interface utilisateur Streamlit
st.title("Inventaire de Matières Premières")

# Déplacer les anciennes entrées vers l'historique à chaque lancement
move_old_entries()

# Charger les matières premières depuis sheet1
matieres_data = load_data("sheet1")
matieres = matieres_data['NOM'].tolist()  # Assurez-vous que la colonne a ce nom

# Formulaire pour ajouter une nouvelle matière première
with st.form("ajouter_matiere"):
    nom = st.selectbox("Choisissez une matière première", matieres)  # Utiliser un sélecteur
    quantite = st.number_input("Quantité (0-9)", min_value=0, max_value=9, step=1, value=0)  # Pavé numérique

    # Bouton de soumission
    submitted = st.form_submit_button("Ajouter")
        
    if submitted:
        if nom and quantite >= 0:  # Vérification des données d'entrée
            add_entry(nom, quantite)
            st.success(f"L'entrée pour '{nom}' avec quantité {quantite} a été ajoutée avec succès.")
        else:
            st.error("Veuillez entrer un nom valide et une quantité supérieure ou égale à 0.")

