# scripts/idea_source.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def get_todo_ideas(sheet_name="automated-content-maker", worksheet_name="Sheet1"):
    # Define scope and authorize client
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Open sheet
    sheet = client.open(sheet_name).worksheet(worksheet_name)

    # Get all records into a DataFrame
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    # Filter for ideas where productionStatus is 'todo'
    return df[df["productionStatus"] == "todo"]

# Example usage
if __name__ == "__main__":
    ideas_df = get_todo_ideas()
    print(ideas_df)
