import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from google import genai
import os
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# Function to retrieve 'todo' ideas from the Google Sheet
def get_todo_ideas(sheet_name="automated-content-maker", worksheet_name="Sheet1"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gspread_client = gspread.authorize(creds)
    
    sheet = gspread_client.open(sheet_name).worksheet(worksheet_name)
    
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    
    return df[df["productionStatus"] == "todo"]

# Function to expand idea using Gemini
def expand_idea_with_gemini(idea_text):
    prompt = f"""
    Take the following idea and expand it into 4 distinct scenes. Each scene should be a short, creative, and visually impactful description of an action or observation that would work well as an overlay text on video clips. The scenes should be concise and vivid, capturing the essence of the idea. Each scene should be clear and dramatic, yet short enough to fit on screen as a caption. The descriptions should focus on different aspects of the situation, each one unique but all tied to the central theme of the idea.

    Please ensure that each scene is written as a separate line, with no extra text or explanations. Only the scene descriptions should be listed, each on its own line. Here is an example of how the format should look:

    Example idea: "POV you wake up as a giant"

    Expected output:
    1. "You tower over the city, seeing everything from a bird's-eye view."
    2. "Cars are tiny underfoot, and you could easily pick one up with a single hand."
    3. "People scatter in fear as they realize a giant is among them."
    4. "Your family stands below, looking up, their faces full of shock and awe."

    For the idea: "{idea_text}"

    Please provide the output as 4 distinct scene descriptions, one per line, with no extra text. Do not include any numbers or bullet points. Just the scene descriptions, each on its own line.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # Or whichever model is appropriate
        contents=prompt
    )
    
    # Get the scenes from the response
    scenes = response.text.strip().split("\n")
    return [scene.strip() for scene in scenes if scene.strip()]

# Function to update scenes in the Google Sheet
def update_scenes_in_sheet(idea_row, scenes, sheet_name="automated-content-maker", worksheet_name="Sheet1"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gspread_client = gspread.authorize(creds)

    sheet = gspread_client.open(sheet_name).worksheet(worksheet_name)

    # Update the row with the scenes
    for i, scene in enumerate(scenes, 1):
        # Update scene captions
        sheet.update_cell(idea_row, i*3+3, scene)  # scene1_caption in column 6 (i+5)
        # For clip link and sound, these can be placeholders for now
        sheet.update_cell(idea_row, i*3+4, "")  # scene1_clip_link in column 7 (i+6)
        sheet.update_cell(idea_row, i*3+5, "")  # scene1_sound in column 8 (i+7)

# Main function to pull data and update sheet
def main():
    # Fetch the ideas marked as 'todo'
    ideas_df = get_todo_ideas()
    
    # Assuming you're working with the first idea (you can adjust this as needed)
    if not ideas_df.empty:
        idea_text = ideas_df.iloc[0]["idea"]
        idea_row = ideas_df.index[0] + 2  # Google Sheets is 1-based indexing, and we need to add 2 for row offset

        print(f"Expanding idea: {idea_text}")
        
        # Expand the idea using Gemini
        scenes = expand_idea_with_gemini(idea_text)
        
        # Update the Google Sheet with the generated scenes
        update_scenes_in_sheet(idea_row, scenes)
        print(f"Scenes updated in row {idea_row}")
    else:
        print("No 'todo' ideas found.")

# Run the script
if __name__ == "__main__":
    main()
