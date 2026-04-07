# to connect with tmdb 
# using git bash usage get session cookie after logging in
# to get movie info
# curl -b "session=cookie" http://127.0.0.1:8000/api/movies/83533



import requests

TMDB_API_KEY = '484a495d1f102f03f5cb345b87410eaa'
BASE_URL = "https://api.themoviedb.org/3"

def fetch_movie(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    return response.json()


def search_movies_tmdb(query):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    return response.json().get("results", [])

def fetch_movie_credits(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"

    params = {
        "api_key": TMDB_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    return response.json()

def get_recommendations(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/recommendations"
    params = {"api_key": TMDB_API_KEY}

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    results = response.json().get("results", [])

    cleaned = []
    for movie in results:
        cleaned.append({
            "id": movie.get("id"),
            "title": movie.get("title"),
            "poster_path": movie.get("poster_path")
        })

    return cleaned

def get_top_rated_movies():
    url = f"{BASE_URL}/movie/top_rated"
    params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
    
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    results = response.json().get("results", [])
    
    cleaned = []
    for movie in results:
        cleaned.append({
            "id": movie.get("id"),
            "title": movie.get("title"),
            "poster_path": movie.get("poster_path")
        })

    return cleaned
