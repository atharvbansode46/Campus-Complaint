
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def ask_gemini(prompt):
    if client is None:
        return "Gemini API key missing. Check your .env file."

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        return response.text or "No response received."

    except Exception as error:
        print(f"Gemini API error: {error}")
        return "AI service unavailable. Check the terminal for details."
