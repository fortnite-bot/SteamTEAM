import os
import requests

def ai(input_message):
    # Prompt the user for input
    
    # Set up the API request
    url = "https://www.promptpal.net/api/chat-gpt-no-stream"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "You are given the name of a game, give to the best of your abilities the executable name of that game. only answer with the executablew name. nothing agreeing or outside as this message is going straight into a command prompt. for example if i were to ask for fortnite you would give: FortniteClient-Win64-Shipping.exe. Respond in json format but return it as text, so no markdown {\"response\":{\"executable\": \"FortniteClient-Win64-Shipping.exe\", \"name\": \"Fortnite\"}}" + input_message
            }
        ],
        "max_completion_tokens": 128000
    }

    try:
        # Send the POST request
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Extract and log the response text
        response_text = str(data['response']).split('"')[5:6]
        
        return response_text
    except Exception as e:
        print("An error occurred:", str(e))



def close_game(game):
    os.system(f'taskkill /f /im {game}')