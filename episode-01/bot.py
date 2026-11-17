# To run this code you need to install the following dependencies:
# pip install -r requirements.txt

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def generate():
    client = genai.Client()

    model = "gemini-3.1-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Write a one-line poem about the rain."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")

if __name__ == "__main__":
    generate()


