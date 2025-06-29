import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st



def save_service_account_from_env(secret_name="GOOGLE_SERVICE_ACCOUNT", filename="service_account.json"):
    # json_data = os.environ.get(secret_name)
    # if not json_data:
    #     raise ValueError(f"Environment variable {secret_name} not found.")
    # with open(filename, "w") as f:
    #     f.write(json_data)

    # Read the secret value from Streamlit's internal secrets
    service_json = st.secrets[secret_name]
    
    # Save it to a file for gspread or Google API usage
    with open(filename, "w") as f:
        f.write(service_json)


def connect_to_google_sheet(sheet_name="Evaluation Submissions"):
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    save_service_account_from_env()
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scopes)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def append_row_to_sheet(sheet, evaluation_data):
    row = [
        evaluation_data["faculty"],
        evaluation_data["department"],
        evaluation_data["subject"],
        evaluation_data["observer"],
        evaluation_data["position"],
        evaluation_data["date_time"],
        evaluation_data["means"]["skills"],
        evaluation_data["means"]["relationship"],
        evaluation_data["means"]["mastery"],
        evaluation_data["means"]["management"],
        evaluation_data["means"]["overall"]
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def append_to_google_sheet(sheet,evaluation_data):
   try:
        save_service_account_from_env(secret_name="GOOGLE_SERVICE_ACCOUNT", filename="service_account.json")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("FacultyEval").worksheet(sheet)
       #row = list(data.values())
        row = [
        evaluation_data["faculty"],
        evaluation_data["department"],
        evaluation_data["subject"],
        evaluation_data["observer"],
        evaluation_data["position"],
        evaluation_data["date_time"],
        evaluation_data["means"]["skills"],
        evaluation_data["means"]["relationship"],
        evaluation_data["means"]["mastery"],
        evaluation_data["means"]["management"],
        evaluation_data["means"]["overall"]
            ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
     #   st.success("✅ Data successfully appended to Google Sheet.")
   except Exception as e:
        pass
        #st.error(f"❌ System Error failed. But PDF is generated")
