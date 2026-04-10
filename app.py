from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from flask_restful import Api, Resource
#from auth import login_required, admin_required
from tmdb import fetch_movie, search_movies_tmdb, fetch_movie_credits, get_recommendations ,get_top_rated_movies
from models import db, User, Favourites, Review, Report, APIkey
import random
import requests
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy import func
from auth import require_api_key

app = Flask(__name__, template_folder = "html/template", static_folder = "static")


API_KEY = None


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


with app.app_context():
    user_key = APIkey.query.filter_by(role="user").first()
    admin_key = APIkey.query.filter_by(role="admin").first()

    USER_API_KEY = user_key.key if user_key else None
    ADMIN_API_KEY = admin_key.key if admin_key else None
    print(user_key,"userkey")
    print(admin_key, "adminkey")

    USER_HEADERS = {"X-API-KEY": USER_API_KEY}
    ADMIN_HEADERS = {"X-API-KEY": ADMIN_API_KEY}


#cookie - if anyone is logged in 
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
api = Api(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        url = "http://127.0.0.1:8000/api/login"
        username = request.form.get('Username')
        password = request.form.get('Password')

        data = {
            "username": username,
            "password": password
        }
        
        try:
            session['user'] = username
            print(session.get('user'))
            
            response = requests.post(url, json=data)

            if response.status_code == 200:
                result = response.json()
                is_admin = result.get('user', {}).get('admin')

                session['user'] = username
                session['role'] = 'admin' if is_admin else 'user'

                if is_admin:
                    return redirect(url_for('reviews'))
                else:
                    return redirect(url_for('home'))
            
            return render_template('login_error.html')

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return "Connection Error", 500

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
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
        
        #hash password
        hashed_password = generate_password_hash(pw)

        #Add new user
        new_user = User(username = user,  password = hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    
    return render_template('signup.html')

@app.route('/home')

def home():
    user = User.query.filter_by(username=session.get('user')).first()
    if not user:
        return redirect(url_for('login'))
    
    try:
        response = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}",headers = USER_HEADERS)
        if response.status_code == 200:
            favourites_data = response.json() # This is the list of dicts from your API
            favs = [f['movieID'] for f in favourites_data]
        else:
            favs = []
    except Exception as e:
        print(f"API Error: {e}")
        favs = []
    
    if not favs:
        movies = get_top_rated_movies()
    else:
        all_recommended = []
        for movie_id in favs:
            all_recommended.extend(get_recommendations(movie_id))
        
        unique_recommended = list({v['id']:v for v in all_recommended}.values())
        random.shuffle(unique_recommended)
        movies = unique_recommended[:20]
    
    formatted_movies = []
    for m in movies:
        formatted_movies.append({
            "id": m.get("id"),
            "title": m.get("title"),
            "poster_path": f"https://image.tmdb.org/t/p/w300{m.get('poster_path')}" if m.get("poster_path") else None
        })

    return render_template('home.html', movies=formatted_movies)

@app.route('/account')

def account():
    user = User.query.filter_by(username=session.get('user')).first()
    
    favourite_movies = []
    try:
        fav_resp = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}",headers = USER_HEADERS)
        if fav_resp.status_code == 200:
            for f in fav_resp.json():
                movie_data = fetch_movie(f['movieID']) 
                if movie_data:
                    favourite_movies.append({
                        "id": movie_data.get("id"),
                        "title": movie_data.get("title"),
                        "poster_path": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None
                    })
        print('favourites received')
    except Exception as e:
        print(f"Fav API Error: {e}")

    # API CALL for Reviews
    your_reviews = []
    try:
        rev_resp = requests.get(f"http://127.0.0.1:8000/api/reviews?userID={user.id}", headers = USER_HEADERS) 
        if rev_resp.status_code == 200:
            for r in rev_resp.json():
                your_reviews.append({
                    "rating": r.get("rating"),
                    "content": r.get("content"),
                    "movie_name": fetch_movie(r.get('movieID')).get('title')
                })
        print(your_reviews)
    except Exception as e:
        print(f"Review API Error: {e}")

    return render_template('account.html', user=user, movies=favourite_movies, reviews=your_reviews)

@app.route('/movie/<int:movie_id>', methods = ['GET','POST'])

def movie_page(movie_id):
    movie = fetch_movie(movie_id)
    credits = fetch_movie_credits(movie_id)
    user = User.query.filter_by(username=session['user']).first()

    # API CALL to check if this movie is a favorite
    is_favourite = False
    try:
        response = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}",headers = USER_HEADERS)
        if response.status_code == 200:
            favs = response.json()
            is_favourite = any(f['movieID'] == movie_id for f in favs)
    except:
        pass
    
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

    reviews = []
    try:
        rev_resp = requests.get(f"http://127.0.0.1:8000/api/reviews?movieID={movie_id}", headers = USER_HEADERS) 
        if rev_resp.status_code == 200:
            for r in rev_resp.json():
                reviews.append({
                    "id": r.get("id"),
                    "rating": r.get("rating"),
                    "content": r.get("content"),
                    "username": User.query.get(r.get("userID")).username
                })
    except Exception as e:
        print(f"Review API Error: {e}")

    return render_template(
        'info.html',
        movie=movie,
        actors=actors,
        directors=directors,
        writers=writers, 
        genres=genre_name,
        is_favourite=is_favourite,
        reviews=reviews
    )

@app.route('/search')

def search():
    query = request.args.get('q')

    if not query:
        return redirect(url_for('home'))

    results = search_movies_tmdb(query)

    if not results:
        return render_template('search.html', movies=[])

    return render_template('search.html', movies=results)

@app.route('/editUser', methods=['GET', 'POST'])


def editUser():
    if request.method == 'POST':
        current_pw_input = request.form.get('currentPassword')
        new_username = request.form.get('newUsername')

        user = User.query.filter_by(username=session['user']).first()

        if not user:
            flash("User not found. Please log in again.")
            return redirect(url_for('login'))

        response = requests.put(
            f"http://localhost:8000/api/users/{user.id}",
            json={
                "currentPassword": current_pw_input,
                "newUsername": new_username
            },
            headers = USER_HEADERS
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
        else:
            data = {"message": "Server returned invalid response"}

        if response.status_code != 200:
            print("error, user name not changed")
            return redirect(url_for('editUser'))

        # Update session only if username changed
        if new_username:
            print(new_username)
            session['user'] = new_username
            print("Username updated successfully!")

        
        return redirect(url_for('account'))

    return render_template('editUser.html')

@app.route('/editPass', methods=['GET', 'POST'])

def editPass():
    if request.method == 'POST':
        current_pw_input = request.form.get('currentPassword')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')
        
        if new_password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('editPass'))

        user = User.query.filter_by(username=session['user']).first()
        if not user:
            print("error user not found")
            return redirect(url_for('login'))
        
        response = requests.put(
            f"http://localhost:8000/api/users/{user.id}",
            json={
                "currentPassword": current_pw_input,
                "newPassword": new_password
            }, headers = USER_HEADERS
        )
        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
        else:
            data = {"message": "Server returned invalid response"}

        if response.status_code != 200:
            print("error, user name not changed")
            return redirect(url_for('editPass'))

        # Update session only if username changed
        if new_password:
            session['user'] = user.username

        print("Password updated successfully!")
        
        return redirect(url_for('account'))

    return render_template('editPass.html')

@app.route('/add_favourite/<int:movie_id>', methods=['POST'])

def add_favourite(movie_id):
    user = User.query.filter_by(username=session['user']).first()
    url = "http://127.0.0.1:8000/api/favourites"
    
    data = {
        "userID": user.id,
        "movieID": movie_id
    }



    try:
        # API CALL instead of db.session.add
        response = requests.post(url, json=data, headers = USER_HEADERS)
        if response.status_code == 201:
            return redirect(url_for('movie_page', movie_id=movie_id))
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/remove_favourite/<int:movie_id>', methods=['POST'])

def remove_favourite(movie_id):
    user = User.query.filter_by(username=session['user']).first()
    url = "http://127.0.0.1:8000/api/favourites"
    
    data = {
        "userID": user.id,
        "movieID": movie_id
    }

  

    try:
        response = requests.delete(url, json=data, headers = USER_HEADERS)
        if response.status_code == 200:
            return redirect(url_for('movie_page', movie_id=movie_id))
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/submit_review/<int:movie_id>', methods=['POST'])

def submit_review(movie_id):
    user = User.query.filter_by(username=session['user']).first()

    url = "http://127.0.0.1:8000/api/reviews"

    data = {
        "userID": user.id,
        "movieID": movie_id,
        'content': request.form.get("content"),
        'rating': int(request.form.get("rating"))
    }

    try:
        response = requests.post(url, json=data)

        if response.status_code == 201:
            return redirect(url_for('movie_page', movie_id=movie_id))

        return jsonify({
            "success": False,
            "error": response.json()
        }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/report_review/<int:review_id>', methods=['POST'])
def report_review(review_id):
    user = User.query.filter_by(username=session['user']).first()
    movie_id = request.form.get('movie_id')
    
    url = "http://127.0.0.1:8000/api/reports"

    data = {
        "reviewID": review_id,
        "userID": user.id
    }

    try:
        response = requests.post(url, json=data)

        if response.status_code == 201:
            return redirect(url_for('movie_page', movie_id=movie_id))
        
        elif response.status_code == 409:
            return redirect(url_for('movie_page', movie_id=movie_id))

        return jsonify({
            "success": False,
            "error": response.json()
        }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# change when other areas are done
# api for searching movies, else return all movies
class MovieAPI(Resource):
    
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
    @require_api_key()
    def get(self, userid = None):
        # Check if username query parameter is provided
        username = request.args.get('username')
        
        if username:
            # Get specific user by username
            user = User.query.filter_by(username=username).first()
            if not user:
                return {"error": "User not found"}, 404
            return ({
                "id": user.id,
                "username": user.username,
                "admin": user.admin,
            })
        else:
            # Return all users (original behavior)
            users = User.query.all()
            return ([{
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


        #hash password
        hashed_password = generate_password_hash(data["password"])
        print (hashed_password)
        new_user = User(
            username = data["username"],
            password = hashed_password,
            admin = False,
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
    @require_api_key()
    def put(self,userid):
        print("ran put")
        data = request.get_json()
        user = User.query.get(userid)

        if not user:
            return {"error":"User not Found"},404

        if not check_password_hash(user.password, data.get("currentPassword")):
            return{"message":"Incorrect Password"}, 400
        

        #update username if provided and not duplicate
        new_username = data.get("newUsername")
        if new_username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != user.id: 
                return{"message":"New username alreadly exists"}, 409 
            user.username = data["newUsername"]
            db.session.commit()
    

        #update password if provided
        newPassword = data.get("newPassword")
        if newPassword:
            user.password = generate_password_hash(newPassword)
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
    @require_api_key(role = "admin")
    def delete(self,userid):
        data = request.get_json()
        if not data.get("username"):
            return{"message":"Username is required to delete the user"}, 404
        
        user = User.query.filter_by(username=data["username"]).first()
        if not user:
            return{"error": "User not Found"}, 404

        db.session.delete(user)
        db.session.commit()

        return {"message": f"User '{data['username']}' deleted successfully"}, 200
backendApi.add_resource(UserAPI, "/api/users/<int:userid>")


class LoginAPI(Resource):
    def post(self):
        data = request.get_json()
        if not data or not data.get("username") or not data.get("password"):
            return{"error": "username and password required"},400
        
        #verify user
        db_user = User.query.filter_by(username = data["username"]).first()
        if not db_user:
            return{"Error":"User not found"}, 404
        
        #verify password
        if not db_user or not check_password_hash(db_user.password, data["password"]):
            return {"error":"invalid details"}, 401
        
        

        return {
            "message": "login successful",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "admin": db_user.admin
            },
        }, 200
backendApi.add_resource(LoginAPI, "/api/login")

# api for getting, posting and deleteing favourites

class FavouriteAPI(Resource):
    @require_api_key()
    def get(self):

        username_from_arg = request.args.get('username')
        username_from_session = session.get('user')

        target_name = username_from_arg or username_from_session

        if target_name:
            user = User.query.filter_by(username=target_name).first()
            if user:
                print(target_name)
                favourites = Favourites.query.filter_by(userID=user.id).all()
                return ([{
                    "id": f.id,
                    "userID": f.userID,
                    "movieID": f.movieID
                } for f in favourites])
                        
        else:
            favourites = Favourites.query.all()
            return ([{
                "id": f.id,
                "userID": f.userID,
                "movieID": f.movieID
            }for f in favourites])
            
    @require_api_key()
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            print('test1.2')
            return{"message": "Requires a userID and movieID to post a rating"},401

        existing_favourite = Favourites.query.filter_by(userID=data["userID"], movieID=data["movieID"]).first()
        if existing_favourite:
            return {"error": "Favourite already exists"}, 402

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

    @require_api_key()
    def delete(self):
        data = request.get_json()
        
        if not data.get("userID") or not data.get("movieID"):
            return{"message": "user and move ID required to delete the favourite"}, 404

        favourite = Favourites.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]
        ).first()

        print(favourite)

        if not favourite:
            return {"error": "Favourite not found"}, 404

        db.session.delete(favourite)
        db.session.commit()

        return {"message": f"User '{data['userID']}' deleted successfully"}, 200
backendApi.add_resource(FavouriteAPI, "/api/favourites")

# api for getting and posting reviews

class ReviewAPI(Resource):
    @require_api_key()
    def get(self):
        movie_id = request.args.get('movieID', type=int)
        user_id = request.args.get('userID', type=int)
        username = request.args.get('username')

        query = Review.query

        # filter by movieID
        if movie_id is not None:
            query = query.filter(Review.movieID == movie_id)

        # filter by userID
        if user_id is not None:
            query = query.filter(Review.userID == user_id)

        # filter by username (convert to userID)
        if username:
            user = User.query.filter_by(username=username).first()
            if not user:
                return {"error": "User not found"}, 404
            query = query.filter(Review.userID == user.id)

        reviews = query.all()

        return ([
            {
                "id": r.id,
                "userID": r.userID,
                "username": User.query.get(r.userID).username,
                "movieID": r.movieID,
                "content": r.content,
                "rating": r.rating
            }
            for r in reviews
        ])
    
    @require_api_key()
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID") or not data.get("content") or data.get("rating") is None:
            return {"message": "Requires userID, movieID, content, and rating"}, 400

        existing_review = Review.query.filter_by(
            userID=data["userID"],
            movieID=data["movieID"]
        ).first()

        if existing_review:
            return {"message": "Review already exists for this user and movie"}, 400

        new_review = Review(
            userID=data["userID"],
            movieID=data["movieID"],
            content=data["content"],
            rating=data["rating"]
        )

        db.session.add(new_review)
        db.session.commit()

        return {
            "message": "Review created successfully",
            "review": {
                'id':new_review.id,
                "userID": new_review.userID,
                "movieID": new_review.movieID,
                "content": new_review.content
                }
        }, 201
        
    @require_api_key(role = "admin")
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


class ReportAPI(Resource):
    @require_api_key()
    def get(self):
        # Only handle GETTING the list here
        results = (
            db.session.query(
                Review,
                func.count(Report.id).label("report_count")
            )
            .join(Report, Review.id == Report.reviewID) # Changed to .join (Inner Join)
            .group_by(Review.id)
            .having(func.count(Report.id) > 0) # Only show if count is 1 or more
            .order_by(func.count(Report.id).desc())
            .all()
        )

        # Return a list directly (Flask-RESTful handles the JSON)
        return [
            {
                "reviewID": review.id,
                "userID": review.userID,
                "movieID": review.movieID,
                "content": review.content,
                "report_count": report_count
            }
            for review, report_count in results
        ]

    def post(self):
        data = request.get_json()

        if not data.get("reviewID"):
            return {"message": "reviewID is required"}, 400
        
        if not data.get("userID"):
            return {"message": "userID is required"}, 400

        review_id = data["reviewID"]
        user_id = data["userID"]

        # Check if this user has already reported this review
        existing_report = Report.query.filter_by(
            reviewID=review_id,
            userID=user_id
        ).first()
        
        if existing_report:
            return {
                "message": "You have already reported this review",
                "already_reported": True
            }, 409  

        new_report = Report(
            reviewID=review_id,
            userID=user_id
        )

        db.session.add(new_report)
        db.session.commit()

        return {
            "message": "Report added successfully",
            "report": {
                "id": new_report.id,
                "reviewID": new_report.reviewID,
                "userID": new_report.userID
            }
        }, 201

    @require_api_key(role = "admin")
    def delete(self):
        # Handle Dismiss and Delete here using query params or JSON body
        dismiss_id = request.args.get("dismiss_review")
        delete_id = request.args.get("delete_review")

        # Inside ReportAPI delete method
        if dismiss_id:
            Report.query.filter_by(reviewID=int(dismiss_id)).delete()
            db.session.commit()
            return {"message": "Dismissed"}, 200

        if delete_id:
            # 1. Delete the reports FIRST (the children)
            Report.query.filter_by(reviewID=int(delete_id)).delete()
            
            # 2. Delete the review SECOND (the parent)
            review_to_del = Review.query.get(int(delete_id))
            if review_to_del:
                db.session.delete(review_to_del)
            
            db.session.commit()
            return {"message": "Deleted"}, 200
                
        return {"error": "No action specified"}, 400
backendApi.add_resource(ReportAPI, "/api/reports")

@app.route('/reviews')


def reviews():

    resp = requests.get("http://127.0.0.1:8000/api/reports")
    data = resp.json()

    reported_reviews = []

    for review in data:
        user = User.query.filter_by(id=review["userID"]).first()
        movie_data = fetch_movie(review["movieID"])

        reported_reviews.append({
            "review_id": review["reviewID"],
            "movie_title": movie_data.get('title') if movie_data else 'Unknown',
            "username": user.username if user else "Unknown",
            "content": review["content"],
            "report_count": review["report_count"],
            "movie_id": review["movieID"]
        })

    return render_template('admin_review.html', reviews=reported_reviews)

@app.route('/admin/dismiss/<int:review_id>', methods=['POST'])

def admin_dismiss(review_id):
    # This triggers the 'dismiss_review' logic in your ReportAPI.delete method
    url = f"http://127.0.0.1:8000/api/reports?dismiss_review={review_id}"
    resp = requests.delete(url, headers = ADMIN_HEADERS) 
    return redirect(url_for('reviews'))

@app.route('/admin/delete_review/<int:review_id>', methods=['POST'])

def admin_delete(review_id):
    url = f"http://127.0.0.1:8000/api/reports?delete_review={review_id}"
    resp = requests.delete(url, headers = ADMIN_HEADERSM)
    
    if resp.status_code == 200:
        flash("Review and reports deleted successfully.")
    else:
        flash("Error: Could not delete review.")
    return redirect(url_for('reviews'))

print("DB path:", os.path.abspath(db_path))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True, host = '0.0.0.0', port = 8000, threaded=True)