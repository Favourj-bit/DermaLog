from dotenv import load_dotenv
import os
import requests
from mimetypes import guess_type

# Load the environment variables from .env file
load_dotenv()

# Now you can access the API_KEY environment variable
API_KEY = os.getenv('API_KEY')
API_URL = 'https://api.robomua.com/api/skinshade'

# Function to send the image to the roboMUA API and return the results

def analyze_image_with_api(image_path):
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        raise ValueError("Could not determine the MIME type of the image")
    headers = {
        'x-api-key': API_KEY
    }
    files = {
        'file': (os.path.basename(image_path), open(image_path, 'rb'), mime_type)
    }
    response = requests.post(API_URL, headers=headers, files=files)
    if response.status_code == 200:
        result = response.json()  # or `response.text` if the response is not in JSON format
        return result['skinShade'], result['toneRange']
    else:
        raise Exception(f"Error in API call: {response.status_code} - {response.text}")

# Example usage
if __name__ == "__main__":
    image_path = '/Users/favourjames/Pictures/picture.jpeg'
    result = analyze_image_with_api(image_path)
    print(result)  # Print the results to the console for now
