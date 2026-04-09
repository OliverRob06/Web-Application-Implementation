import requests

# URL of your API endpoint
url = "http://localhost:8000/api/reviews"

# Optional: filter by userID
params = {"userID": 1}  # remove or change to get all reviews

# Make the GET request
response = requests.get(url, params=params)

# Parse JSON response
reviews = response.json()

# Print reviews nicely
for review in reviews:
    print(f"ID: {review['id']}, UserID: {review['userID']}, MovieID: {review['movieID']}, Content: {review['content']}")