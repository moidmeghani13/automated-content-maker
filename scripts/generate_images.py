import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai
import requests
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
image_api_key = os.getenv("PIAPI_API_KEY")

# Authenticate Gemini
client = genai.Client(api_key=api_key)

# Authenticate Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open("automated-content-maker").worksheet("Sheet1")

# Prompt Gemini to expand scene caption into an image prompt
def expand_caption_to_image_prompt(idea, title, style, caption):
    prompt = f"""
    You are helping generate AI images for a short video project.

    Here's the context:
    - Title: {title}
    - Idea: {idea}
    - Style: {style}

    Based on the following scene caption:
    "{caption}"

    Generate a short and vivid image generation prompt for a realistic AI image, filmed as if from a GoPro.
    The viewer should feel like they're seeing through the character's eyes, with visible hands in the frame.
    Make sure the prompt emphasizes realism and action. Be sure to include specific details that would make the image visually striking and engaging.
    The prompt should be concise, clear, and focused on creating a visually impactful image that fits the scene caption. Focus on the idea and the style making sure the scene is in line wirh the overall theme.
    

    Output only the prompt, no extra text.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()

# Generate image using PIAPI and return image URL
def generate_image_url(prompt):
    url = "https://api.piapi.ai/api/v1/task"
    payload = json.dumps({
        "model": "Qubico/flux1-schnell",
        "task_type": "txt2img",
        "input": {
            "prompt": prompt,
        }
    })
    headers = {
        'X-API-Key': image_api_key,
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    print(f"PIAPI response: {data}")
    if response.status_code != 200 or "output" not in data:
        print(f"Error generating image: {data.get('error', 'Unknown error')}")
        return ""
    return data.get("output", {}).get("url", "")

# Main logic to loop through 'todo' ideas and generate images
def main():
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    print(f"Found {len(df)} rows in the sheet.")

    for idx, row in df.iterrows():
        if row["productionStatus"] != "todo":
            continue

        idea = row["idea"]
        title = row["title"]
        style = row.get("style", "")
        row_number = idx + 2  # Adjust for header

        for scene_index in range(1, 5):
            caption_key = f"scene{scene_index}_caption"
            link_key = f"scene{scene_index}_clip_link"

            caption = row.get(caption_key, "").strip()
            if not caption or row.get(link_key):
                continue  # Skip if no caption or image already exists

            image_prompt = expand_caption_to_image_prompt(idea, title, style, caption)
            print(f"Generating image for row {row_number}, scene{scene_index}: {image_prompt}")
            if not image_prompt:
                print(f"No image prompt generated for row {row_number}, scene{scene_index}. Skipping.")
                continue
            image_url = generate_image_url(image_prompt)
            print(f"Generated image URL for row {row_number}, scene{scene_index}: {image_url}")
            if not image_url:
                print(f"No image URL returned for row {row_number}, scene{scene_index}. Skipping.")
                continue

            if image_url:
                col_number = 5 + (scene_index - 1) * 3 + 1  # Adjusted to get clip_link column
                sheet.update_cell(row_number, col_number, image_url)
                print(f"Updated row {row_number}, scene{scene_index}_clip_link with image URL")

if __name__ == "__main__":
    main()
