from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from flask_restful import Api, Resource
from auth import login_required, admin_required
from tmdb import fetch_movie, search_movies_tmdb, fetch_movie_credits, get_recommendations ,get_top_rated_movies
from models import db, User, Favourites, Review, Report
import random
import requests
import os
from werkzeug.security import generate_password_hash, check_password_hash
from backend_auth import require_login, require_admin
import uuid
from test import tokens
from sqlalchemy import func

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
                    return redirect(url_for('admin_search'))
                else:
                    return redirect(url_for('home'))
            
            return render_template('login_error.html')

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return "Connection Error", 500

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
        
        #hash password
        hashed_password = generate_password_hash(pw)

        #Add new user
        new_user = User(username = user,  password = hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=session.get('user')).first()
    if not user:
        return redirect(url_for('login'))
    
    try:
        response = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}")
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
@login_required
def account():
    user = User.query.filter_by(username=session.get('user')).first()
    
    favourite_movies = []
    try:
        fav_resp = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}")
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
        rev_resp = requests.get(f"http://127.0.0.1:8000/api/reviews?userID={user.id}") 
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
@login_required
def movie_page(movie_id):
    movie = fetch_movie(movie_id)
    credits = fetch_movie_credits(movie_id)
    user = User.query.filter_by(username=session['user']).first()

    # API CALL to check if this movie is a favorite
    is_favourite = False
    try:
        response = requests.get(f"http://127.0.0.1:8000/api/favourites?username={user.username}")
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

    user = session['user']

    reviews = []
    try:
        rev_resp = requests.get(f"http://127.0.0.1:8000/api/reviews?userID={user.id}") 
        if rev_resp.status_code == 200:
            for r in rev_resp.json():
                your_reviews.append({
                    "rating": r.get("rating"),
                    "content": r.get("content"),
                    "username": r.get('userID')
                })
        print(your_reviews)
    except Exception as e:
        print(f"Review API Error: {e}")
    

    return render_template(
        'info.html',
        movie=movie,
        actors=actors,
        directors=directors,
        writers=writers, 
        genres=genre_name,
        is_favourite=is_favourite
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

@app.route('/editUser', methods=['GET', 'POST'])
@login_required
def editUser():
    if request.method == 'POST':
        current_pw_input = request.form.get('currentPassword')
        new_username = request.form.get('newUsername')
        
        user = User.query.filter_by(username=session['user']).first()

        # Check if password is correct
        if user.password != current_pw_input:
            flash("Incorrect current password.")
            return redirect(url_for('editUser'))

        # Check if new username is available
        if User.query.filter_by(username=new_username).first():
            flash("Username already exists.")
            return redirect(url_for('editUser'))

        # Update
        user.username = new_username
        db.session.commit()
        session['user'] = new_username # Update session to match new name
        
        flash("Username updated successfully!")
        return redirect(url_for('account'))

    return render_template('editUser.html')

@app.route('/editPass', methods=['GET', 'POST'])
@login_required
def editPass():
    if request.method == 'POST':
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')
        
        if new_password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('editPass'))

        current_user = User.query.filter_by(username=session['user']).first()
        current_user.password = new_password # Note: In production, use hashing!
        db.session.commit()

        flash("Password updated successfully!")
        return redirect(url_for('account'))

    return render_template('editPass.html')

@app.route('/add_favourite/<int:movie_id>', methods=['POST'])
@login_required
def add_favourite(movie_id):
    user = User.query.filter_by(username=session['user']).first()
    url = "http://127.0.0.1:8000/api/favourites"
    
    data = {
        "userID": user.id,
        "movieID": movie_id
    }

    try:
        # API CALL instead of db.session.add
        response = requests.post(url, json=data)
        if response.status_code == 201:
            return redirect(url_for('movie_page', movie_id=movie_id))
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/remove_favourite/<int:movie_id>', methods=['POST'])
@login_required
def remove_favourite(movie_id):
    user = User.query.filter_by(username=session['user']).first()
    url = "http://127.0.0.1:8000/api/favourites"
    
    data = {
        "userID": user.id,
        "movieID": movie_id
    }

    try:
        response = requests.delete(url, json=data)
        if response.status_code == 200:
            return redirect(url_for('movie_page', movie_id=movie_id))
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
    @require_login

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
        db.session.commit()

        return {"message": f"User '{data['username']}' deleted successfully"}, 200
backendApi.add_resource(UserAPI, "/api/users")

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
        
        #generate token
        token = str(uuid.uuid4())

        #store token to user
        tokens[token] ={
            "user_id": db_user.id,
            "role": "admin" if db_user.admin else "user"
        }

        return {
            "message": "login successful",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "admin": db_user.admin
            },
            "token": token
        }, 200
backendApi.add_resource(LoginAPI, "/api/login")

# api for getting, posting and deleteing favourites
class FavouriteAPI(Resource):
    def get(self):

        username_from_arg = request.args.get('username')
        username_from_session = session.get('user')

        target_name = username_from_arg or username_from_session

        if target_name:
            user = User.query.filter_by(username=target_name).first()
            if user:
                print(target_name)
                favourites = Favourites.query.filter_by(userID=user.id).all()
                return jsonify([{
                    "id": f.id,
                    "userID": f.userID,
                    "movieID": f.movieID
                } for f in favourites])
                        
        else:
            favourites = Favourites.query.all()
            return jsonify([{
                "id": f.id,
                "userID": f.userID,
                "movieID": f.movieID
            }for f in favourites])
            
    
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("movieID"):
            print('test1.2')
            return{"message": "Requires a userID and movieID to post a rating"},401

        existing_favourite = Favourites.query.filter_by(userID=data["userID"], movieID=data["movieID"]).first()
        if existing_favourite:
            print('test1.3')
            return {"error": "Favourite already exists"}, 402
        
        print('test2')


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

        print(favourite)

        if not favourite:
            return {"error": "Favourite not found"}, 404


        db.session.delete(favourite)
        db.session.commit()

        return {"message": f"User '{data['userID']}' deleted successfully"}, 200
backendApi.add_resource(FavouriteAPI, "/api/favourites")

# api for getting and posting reviews
class ReviewAPI(Resource):
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

        return jsonify([
            {
                "id": r.id,
                "userID": r.userID,
                "movieID": r.movieID,
                "content": r.content,
                "rating": r.rating
            }
            for r in reviews
        ])
    
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
        
# change when other areas are done
# api for admins reviewing reported reviews
class ReportAPI(Resource):  
    @require_login
    def get(self):
        reports = Report.query.all()
        return jsonify([{
            "id": r.id,
            "userID": r.userID,
            "reviewID": r.reviewID
        } for r in reports])
    
    def post(self):
        data = request.get_json()

        if not data.get("userID") or not data.get("reviewID"):
            return {"message": "Requires a userID and reviewID to make a report"}, 400

        existing_report = Report.query.filter_by(
            userID=data["userID"], 
            reviewID=data["reviewID"]
        ).first()
        
        if existing_report:
            return {"error": "Report already exists"}, 400

        # FIXED: Create a Report, not a Rating
        new_report = Report(
            userID=data["userID"],
            reviewID=data["reviewID"]
        )

        db.session.add(new_report)
        db.session.commit()
        
        return {
            "message": "New report successfully added",
            "report": {
                "id": new_report.id,
                "userID": new_report.userID,
                "reviewID": new_report.reviewID,
            }
        }, 201
    
    def delete(self):
        data = request.get_json()
        
        if not data.get("reviewID"):
            return {"message": "reviewID required to delete reports"}, 400
        
        # Delete all reports for a specific review (admin action)
        reports = Report.query.filter_by(reviewID=data["reviewID"]).all()
        
        for report in reports:
            db.session.delete(report)
        
        # Optionally delete the review itself
        if data.get("delete_review"):
            review = Review.query.filter_by(id=data["reviewID"]).first()
            if review:
                db.session.delete(review)
        
        db.session.commit()
        
        return {
            "message": f"Deleted {len(reports)} report(s) for review {data['reviewID']}"
        }, 200
backendApi.add_resource(ReportAPI, "/api/reports")

class ReviewsByReportCountAPI(Resource):
    def get(self):
        results = (
            db.session.query(
                Review,
                func.count(Report.id).label("ReportCount")
            )
            .outerjoin(Report, Review.id == Report.reviewID)
            .group_by(Review.id)
            .order_by(func.count(Report.id).desc())
            .all()
        )

        return jsonify([
            {
                "id": review.id,
                "userID": review.userID,
                "movieid": review.movieID,
                "content": review.content,
                "ReportCount": report_count
            }
            for review, report_count in results
        ])
backendApi.add_resource(ReviewsByReportCountAPI, "/api/sortedByReports")        
   

@app.route('/api/admin/test')
@admin_required
def admin_secret():
    return "If you see this, you are an Admin!"

@app.route('/reviews', endpoint='review')
@login_required
@admin_required 
def admin_reviews_list():
    # Get all reports with their associated reviews
    reports = Report.query.all()
    
    # Get unique reviews that have been reported
    reported_reviews = []
    seen_review_ids = set()
    
    for report in reports:
        if report.reviewID not in seen_review_ids:
            seen_review_ids.add(report.reviewID)
            review = Review.query.filter_by(id=report.reviewID).first()
            
            if review:
                user = User.query.filter_by(id=review.userID).first()
                movie_data = fetch_movie(review.movieID)
                
                # Count how many reports this review has
                report_count = Report.query.filter_by(reviewID=review.id).count()
                
                reported_reviews.append({
                    "review_id": review.id,
                    "movie_title": movie_data.get('title', 'Unknown Movie') if movie_data else 'Unknown Movie',
                    "username": user.username if user else "Unknown",
                    "content": review.content,
                    "report_count": report_count,
                    "movie_id": review.movieID
                })
    
    return render_template('admin_review.html', reviews=reported_reviews)

@app.route('/admin/delete/<int:review_id>', methods=['POST'])
@admin_required
def delete_reported_review(review_id):
    Report.query.filter_by(reviewID=review_id).delete()
    Review.query.filter_by(id=review_id).delete()
    db.session.commit()
    return redirect(url_for('review'))

@app.route('/admin/dismiss/<int:review_id>')
@admin_required
def dismiss_reports(review_id):
    Report.query.filter_by(reviewID=review_id).delete()
    db.session.commit()
    return redirect(url_for('review'))

# Change this route to use the logic
@app.route('/admin_review')
@login_required
@admin_required 
def admin_review():
    # Instead of just rendering, redirect to the 'review' function 
    # OR copy the logic from the @app.route('/reviews') here.
    return redirect(url_for('review'))

@app.route('/admin_search')
def admin_search():
    # Render the admin search page
    return render_template('admin_search.html')


print("DB path:", os.path.abspath(db_path))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True, host = '0.0.0.0', port = 8000)