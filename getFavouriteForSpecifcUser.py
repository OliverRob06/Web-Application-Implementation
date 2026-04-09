import requests

user_id = 1
url = f"http://localhost:8000/api/favourites?userID={user_id}"

response = requests.get(url)
favourites = response.json()

print(f"Favourites for user {user_id}:")
for f in favourites:
    print(f"MovieID: {f['movieID']}, FavouriteID: {f['id']}")