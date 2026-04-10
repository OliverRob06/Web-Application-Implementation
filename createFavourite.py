import requests

# URL of your API endpoint
url = "http://localhost:8000/api/favourites"

# Data to send in the POST request
data = {
    "userID": 1,
    "movieID": 10
}

# Make the POST request
response = requests.post(url, json=data)

# Print status code and response JSON
print("Status code:", response.status_code)
print("Response:", response.json())