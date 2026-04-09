from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_restful import Api, Resource
from auth import ADMIN_PASSWD, login_required, admin_required
from tmdb import fetch_movie, search_movies_tmdb, fetch_movie_credits, get_recommendations ,get_top_rated_movies
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Favourites, Review, Rating
import requests
import random
import os
import uuid

app = Flask(__name__, template_folder = "html/template", static_folder = "static")


#store database inside the project directory
db_folder = os.path.join(os.getcwd(), "database")
db_path = os.path.join(db_folder, "database.db")

#ensure the database directory exists
os.makedirs(db_folder, exist_ok = True)

#configuring SQL database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
backendApi = Api(app)





#creating tables
def create_tables():
    with app.app_context():
        db.create_all()
        print(f"Database created at {db_path}")

create_tables()


#cookie - if anyone is logged in 
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
api = Api(app)


reviews = []
ratings = {}
reports = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    #admin login 
    if request.method == 'POST':
        user = request.form.get('Username')
        pw = request.form.get('Password')

        print(f"Login attempt for user: {user}")

        # currently to login as admin 
        # username = admin 
        # password = adminke
        
        db_user = User.query.filter_by(username = user).first()
        
        if db_user.admin:
            session['role'] = 'admin'
        else:
            session['role'] = 'user'

        # store username in session
        session['user'] = db_user.username

        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('Username')
        pw = request.form.get('Password')
        
        print("Creating new users with username:", user, "password", pw)


        # Check if user already exists
        existing_user = User.query.filter_by(username=user).first()
        if existing_user:
            return 'Username already exists', 400
        
        
        #Add new user
        new_user = User(username = user, password = pw)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=session['user']).first()
    user_id = user.id

    favourites = Favourites.query.filter_by(userID=user_id).all()
    
    favs = [f.movieID for f in favourites]
    if not favs:
        movies = get_top_rated_movies()
        
    if not favs:
        movies = get_top_rated_movies()
    else:
        all_recommended = []
        for movie_id in favs:
            recommended = get_recommendations(movie_id)
            all_recommended.extend(recommended)

        seen = set()
        unique_recommended = []
        for movie in all_recommended:
            if movie['id'] not in seen:
                seen.add(movie['id'])
                unique_recommended.append(movie)
        
        random.shuffle(unique_recommended)
        movies = unique_recommended[:20]
    
    formatted_movies = []
    for m in movies:
        formatted_movies.append({
            "id": m.get("id"),
            "title": m.get("title"),
            "poster_path": f"https://image.tmdb.org/t/p/w300{m.get('poster_path')}" if m.get("poster_path") else None
        })
    
    if session.get('role') == 'admin':
        return render_template('admin_search.html')
    else:
        return render_template('home.html', movies=formatted_movies)

@app.route('/account')
@login_required
def account():
    user = User.query.filter_by(username=session['user']).first()
    user_id = user.id

    favourites = Favourites.query.filter_by(userID=user_id).all()

    favourite_movies = []

    for f in favourites:
        # 2. f.movieID is an integer (e.g., 550)
        # You MUST fetch the movie details dictionary from the API using that ID
        movie_data = fetch_movie(f.movieID) 
        
        if movie_data:
            favourite_movies.append({
                "id": movie_data.get("id"),
                "title": movie_data.get("title"),
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get("poster_path") else None
            })

    return render_template('account.html', movies=favourite_movies)

@app.route('/movie/<int:movie_id>', methods = ['GET','POST'])
@login_required
def movie_page(movie_id):
    movie = fetch_movie(movie_id)
    credits = fetch_movie_credits(movie_id)

    if not movie or not credits:
        return "Movie not found", 404
    
    cast = credits.get('cast', [])
    crew = credits.get('crew', [])

    # 5 actors
    actors = [
        {
            'name' : c['name'],
            'profile_path': c.get('profile_path', ''),
            'id': c.get('id', '')
        }  
        for c in cast [:8]
    ] 
    
    directors = [c['name'] for c in crew if c['job']=='Director']
    writers = [
        c['name'] for c in crew 
        if c['job'] in ['Writer', 'Screenplay', 'Story']
    ]
    
    genres = movie.get('genres')
    genre_name = [c['name'] for c in genres]

    user = session['user']
    

    return render_template(
        'info.html',
        movie=movie,
        actors=actors,
        directors=directors,
        writers=writers, 
        genres=genre_name
    )

@app.route('/search')
@login_required
def search():
    query = request.args.get('q')

    if not query:
        return redirect(url_for('home'))

    results = search_movies_tmdb(query)

    if not results:
        return render_template('search.html', movies=[])

    return render_template('search.html', movies=results)

@app.route('/reviews')
@login_required
def reviews_page():
    # Get all reviews from the database
    all_reviews = Review.query.all()

    # Join with user info to get username
    reviews_data = []
    for r in all_reviews:
        user = User.query.filter_by(id=r.userID).first()
        reviews_data.append({
            "title": f"Movie ID: {r.movieID}",  # Or fetch movie title if needed
            "Aname": user.username if user else "Unknown",
            "description": r.content,
            "review": "Reviewed"  # Or show a rating if you want
        })

    return render_template('admin_review.html', reviews=reviews_data)
# change when other areas are done
# api for searching movies, else return all movies
class MovieAPI(Resource):
    @login_required
    def get(self, movie_id=None):
        if movie_id:
            movie = fetch_movie(movie_id)
            if not movie:
                return {'error':'Movie not found'}, 404
            return movie, 200
        
        query = request.args.get('q')
        if query:
            results = search_movies_tmdb(query)
            return {'results':results}, 200
        
        return {'error':'No query provided'}, 400

#api for getting, creating and deleting users
class UserAPI(Resource):

    #get method retrive all users from database
    def get(self):
        # Check if username query parameter is provided
        username = request.args.get('username')
        
        if username:
            # Get specific user by username
            user = User.query.filter_by(username=username).first()
            if not user:
                return {"error": "User not found"}, 404
            return jsonify({
                "id": user.id,
                "username": user.username,
                "admin": user.admin,
            })
        else:
            # Return all users (original behavior)
            users = User.query.all()
            return jsonify([{
                "id": u.id,
                "username": u.username,
                "password": u.password,
                "admin": u.admin,
            } for u in users])
    
    #create method
    def post(self):
        data = request.get_json()

        if not data.get("username") or not data.get("password"):
            return{"message": "Username and password are required"},400

        existing_user = User.query.filter_by(username = data["username"]).first()
        if existing_user:
            return 'Username already exists', 400


        new_user = User(
            username = data["username"],
            password = data["password"],
            admin = False
        )


        db.session.add(new_user)
        db.session.commit()
        return{
            "message":"new user successfully added", 
            "user":
            { 
                "id":new_user.id, 
                "username":new_user.username 
            }
            },201

    #update method
    def put(self):
        data = request.get_json()

        if not data.get("username"):
            return{"message":"Username is required to update the user"}, 400
        
        user = User.query.filter_by(username=data["username"]).first()
        if not user:
            return{"error": "User not Found"}, 404

        #update username if provided and not duplicate
        if data.get("newUsername"):
            if User.query.filter_by(username=data["newUsername"]).first():
                return{"message":"New username alreadly exists"}, 409 
            user.username = data["newUsername"]
    

        #update password if provided
        if data.get("newPassword"):
            user.password = data["newPassword"]

        db.session.commit()
        return {
            "message": "User updated successfully",
            "user":
            {
                "id": user.id,
                "username": user.username
            }
        }, 200

    #delete method
    def delete(self):
        data = request.get_json()
        if not data.get("username"):
            return{"message":"Username is required to delete the user"}, 404
        
        user = User.query.filter_by(username=data["username"]).first()
        if not user:
            return{"error": "User not Found"}, 404

        db.session.delete(user)
        db.session.complete()

        return {"message": f"User '{data['username']}' deleted successfully"}, 200
backendApi.add_resource(UserAPI, "/api/users")

# api for getting, posting and deleteing favourites
class FavouriteAPI(Resource):
    def get(self):
        favourites = Favourites.query.all()
        return jsonify([{
            "id": f.id,
            "userID": f.userID,
            "movieID": f.movieID
        }for f in favourites])
        
    
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            return{"message": "Requires a userID and movieID to post a rating"},400

        existing_favourite = Favourites.query.filter_by(userID=data["userID"], movieID=data["movieID"]).first()
        if existing_favourite:
            return {"error": "Favourite already exists"}, 400


        new_favourite = Favourites(
            userID = data["userID"],
            movieID = data["movieID"],
        )


        db.session.add(new_favourite)
        db.session.commit()
        return {
            "message": "New favourite successfully added",
            "favourite": {
                "id": new_favourite.id,
                "userID": new_favourite.userID,
                "movieID": new_favourite.movieID
            }
        }, 201

    
    def delete(self):
        data = request.get_json()

        
        if not data.get("userID") or not data.get("movieID"):
            return{"message": "user and move ID required to delete the favourite"}, 404

        #find favourite

        favourite = Favourites.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]
        ).first()

        if not favourite:
            return {"error": "Favourite not found"}, 404


        db.session.delete(favourite)
        db.session.commit()

        return {"message": f"User '{data['id']}' deleted successfully"}, 200
backendApi.add_resource(FavouriteAPI, "/api/favourites")

# api for getting and posting reviews
class ReviewAPI(Resource):
    #@login_required
    def get(self):
        reviews = Review.query.all()
        return jsonify([{   
            "id": r.id,
            "userID": r.userID,
            "movieID": r.movieID,
            "content": r.content,
            } for r in reviews])
    
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            return{"message": "Requires a userID and movieID to post a review"},400

        existing_review = Review.query.filter_by(userID=data["userID"], movieID=data["movieID"]).first()
        if existing_review:
            return 'Username already exists', 400


        new_review = Review(
            userID = data["userID"],
            movieID = data["movieID"],
            content = data["content"]
        )


        db.session.add(new_review)
        db.session.commit()
        return {
            "message": "New review successfully added",
            "review": {
                "id": new_review.id,
                "userID": new_review.userID,
                "movieID": new_review.movieID,
                "content": new_review.content
                }
        }, 201
        
    
    def put(self):
        data = request.get_json()

        if not data or not data.get("userID") or not data.get("movieID"):
            return {"message": "userID and movieID are required to update a review"}, 400

        # Find the review
        review = Review.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]
        ).first()

        if not review:
            return {"error": "Review not found"}, 404

        # Update content if provided
        if data.get("newReview"):
            review.content = data["newReview"]

        db.session.commit()

        return {
            "message": "Review updated successfully",
            "review": {
                "id": review.id,
                "userID": review.userID,
                "movieID": review.movieID,
                "content": review.content
            }
        }, 200

    def delete(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            return{"message": "user and move ID required to delete a review"}, 404

        #find review

        review = Review.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]
        ).first()

        if not review:
            return {"error": "Favourite not found"}, 404


        db.session.delete(review)
        db.session.commit()

        return{
            "message": "Review deleted successfully",
            "review": {
                "userID": review.userID,
                "movieID": review.movieID
            }
        }, 200
backendApi.add_resource(ReviewAPI, "/api/reviews")
        
# api for rating movies
class RatingAPI(Resource):
    def get(self):
        ratings = Rating.query.all()
        return jsonify([{
        "id": rat.id,
        "userID": rat.userID,
        "movieID": rat.movieID,
        "score": rat.score,
    } for rat in ratings])
    
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            return{"message": "Requires a userID and movieID to post a rating"},400

        existing_rating = Rating.query.filter_by(userID=data["userID"], movieID=data["movieID"]).first()
        if existing_rating:
            return {"error": "Rating already exists"}, 400


        new_rating = Rating(
            userID = data["userID"],
            movieID = data["movieID"],
            score = data["score"],
        )


        db.session.add(new_rating)
        db.session.commit()
        return {
            "message": "New rating successfully added",
            "rating": {
                "id": new_rating.id,
                "userID": new_rating.userID,
                "movieID": new_rating.movieID,
                "score": new_rating.score
            }
        }, 201
    
    def put(self):
        data = request.get_json()

        if not data or not data.get("userID") or not data.get("movieID") or data.get("newRating") is None:
            return {"message": "userID and movieID, newRating are required to update a rating"}, 400

        # find zee rating
        rating = Rating.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]

        ).first()

        if not rating:
            return {"error": "Review not found"}, 404

        # Update content if provided
        rating.score = data["newRating"]

        db.session.commit()

        return {
            "message": "New rating successfully added",
            "rating": {
                "id": rating.id,
                "userID": rating.userID,
                "movieID": rating.movieID,
                "score": rating.score
            }
        }, 201  
backendApi.add_resource(RatingAPI, "/api/ratings")


@app.route('/api/admin/test')
@admin_required
def admin_secret():
    return "If you see this, you are an Admin!"



print("DB path:", os.path.abspath(db_path))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True, host = '0.0.0.0', port = 8000)