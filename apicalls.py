
import requests



def add_favourite(movie_id):
    # 1. Get current user from DB to get their ID
    user = User.query.filter_by(username=session['user']).first()
    
    # 2. Define the API endpoint (Internal call)
    # Using localhost:8000 because that is where your app is running
    url = "http://127.0.0.1:8000/api/favourites"
    
    # 3. Prepare the JSON data exactly as your API expects it
    data = {
        "userID": user.id,
        "movieID": movie_id
    }

    try:
        # 4. Make the POST request to your friend's API
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            flash("Movie added to your favourites via API!")
        elif response.status_code == 400:
            flash("Movie is already in your favourites.")
        else:
            flash("Failed to add favourite via API.")
            
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        flash("Could not connect to the Favorites service.")

    return redirect(url_for('movie_page', movie_id=movie_id))