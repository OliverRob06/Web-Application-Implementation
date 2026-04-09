from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_restful import Api, Resource
from auth import ADMIN_PASSWD, login_required, admin_required
from tmdb import fetch_movie, search_movies_tmdb, fetch_movie_credits, get_recommendations ,get_top_rated_movies
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Favourites
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



    

#CRUD STATMENTS FAVOURITES
@app.route('/favourite/add/<int:movieid>', methods=['POST'])
def addFavourite(userid: int, movieid: int):
    print("attempting to add favourite")
    new_favourite = testfavourites(userID = userid, movieID = movieid)
    db.session.add(new_favourite)
    db.session.commit()
    print("added favourite")
    return redirect(url_for('movie', movieid=movieid))

def removeFavourite(userid: int, movieid: int):
    favourite = testfavourites.query.filterby(userID = userid, movieID = movieid).first()
    if favourite:
        db.session.delete()
        db.session.commit()
    return redirect(url_for('movie', movieid=movieid))




#cookie - if anyone is logged in 
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
api = Api(app)


favourites = {
    'john': [
        {'movie_id': 1493859},
        {'movie_id': 500},
        {'movie_id': 1084242}
    ]
}
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
        
        if db_user and db_user.password == pw:
            session['user'] = db_user.username

            if db_user.admin:
                session['role'] = 'admin'
                return redirect(url_for('home'))
            
            else:
                session['role'] = 'user'
                return redirect(url_for('home'))
        
        else:
            return render_template('login.html'), 'Invalid Credentials'

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
    # get favourited movei and compile recommendations into a list and randomise it
    user = session['user']
    user_favs = favourites.get(user, [])

    if not user_favs:
        movies = get_top_rated_movies()
    
    else:
        all_recommended = []
        for fav_movie in favourites[user]:
            movie_id = fav_movie.get('movie_id')
            if movie_id:
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
    return render_template('account.html')

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
    if request.method == 'POST':
        addFavourite(user.user_id, movie_id)

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
        users = User.query.all()
        return jsonify([{
                "id": u.id,
                "username": u.username,
                "password": u.password,
                "admin": u.admin,
        }for u in users])
    
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
            return{"message":"Username is required to find the user"}, 400
        
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




# change when other areas are done
# api for getting, posting and deleteing favourites
class FavouriteAPI(Resource):
    @login_required
    def get(self):
        favourites = Favourites.query.all()
        return jsonify([{
            "id": f.id,
            "userID": f.userID,
            "movieID": f.movieID
        }for f in favourites])
        

    @login_required
    def delete(self):
        data = request.get_json()

        #validate input
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

# change when other areas are done
# api for getting and posting reviews
class ReviewAPI(Resource):
    @login_required
    def get(self, movie_id):
        movie_reviews = [r for r in reviews if r.get('movie_id') == movie_id]
        return {'reviews': movie_reviews}, 200
    
    @login_required
    def post(self, movie_id):
        data = request.json

        data['id'] = str(uuid.uuid4())
        data['movie_id'] = movie_id
        data['user'] = session['user']

        reviews.append(data)

        return {'message':'Review added'}, 200

# change when other areas are done
# api for rating movies
class RatingAPI(Resource):
    @login_required
    def get(self, movie_id):
        user = session['user']
        return {'rating': ratings.get(user,{}).get(movie_id)}, 200
    
    @login_required
    def post(self, movie_id):
        user = session['user']
        data = request.json

        ratings.setdefault(user, {})[movie_id] = data.get('rating')
        return {'message': 'Rating saved'}, 201

# change when other areas are done
# api for admins reviewing reported reviews
class AdminReportAPI(Resource):
    @login_required
    def get(self):
        if session.get('role') != 'admin':
            return {"error": "Forbidden"}, 403

        return {"reports": reports}, 200

    @login_required
    def delete(self, report_id):
        if session.get('role') != 'admin':
            return {"error": "Forbidden"}, 403

        global reports
        reports = [r for r in reports if r.get("id") != report_id]

        return {"message": "Deleted"}, 200

@app.route('/api/admin/test')
@admin_required
def admin_secret():
    return "If you see this, you are an Admin!"

api.add_resource(MovieAPI,
    '/api/movies',
    '/api/movies/<int:movie_id>'
)



api.add_resource(ReviewAPI,
    '/api/movies/<int:movie_id>/reviews'
)

api.add_resource(RatingAPI,
    '/api/movies/<int:movie_id>/rating'
)

api.add_resource(AdminReportAPI,
    '/api/admin/reports',
    '/api/admin/reports/<string:report_id>'
)

print("DB path:", os.path.abspath(db_path))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True, host = '0.0.0.0', port = 8000)