from flask import Flask, render_template, request, redirect, url_for, session
from flask_restful import Api, Resource
from auth import ADMIN_PASSWD, login_required, admin_required
from tmdb import fetch_movie, search_movies_tmdb, get_recommendations
import requests
import os
import uuid

app = Flask(__name__, template_folder = "html/template", static_folder = "static")

#cookie - if anyone is logged in 
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
api = Api(app)

# normie user logins before database
users_db = {
    'john': 'password123',
    'jane': 'securepass',
}
favourites = {}
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
        # password = adminkey

        if user == 'admin' and pw == ADMIN_PASSWD:
            # change when database is done
            session['role'] = 'admin'
            session['user'] = user
            return redirect(url_for('home'))
        
        elif user in users_db and users_db[user] == pw:
            # change when database is done
            session['role'] = 'user'
            session['user'] = user
            return redirect(url_for('home'))
        
        else:
            return 'Invalid Credentials', 403

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('Username')
        pw = request.form.get('Password')
        
        # Check if user already exists
        # change when database is done
        if user in users_db:
            return 'Username already exists', 400
        
        # Add new user
        # change when database is done
        users_db[user] = pw
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    if session.get('role') == 'admin':
        return render_template('admin_search.html')  # Admin's home page
    else:
        return render_template('home.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/movie/<int:movie_id>')
@login_required
def movie_page(movie_id):
    movie = fetch_movie(movie_id)

    if not movie:
        return "Movie not found", 404
    
    return render_template('info.html', movie=movie)

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
    
# change when other areas are done
# api for getting, posting and deleteing favourites
class FavouriteAPI(Resource):
    @login_required
    def get(self):
        user = session['user']
        return {'favourites': favourites.get(user, [])}, 200
        
    @login_required
    def post(self):
        user = session['user']
        data = request.json

        if not data:
            return {'error': 'No data provided'}
        
        data['id'] = str(uuid.uuid4())

        favourites.setdefault(user, []).append(data)

        return {'message': 'Added to favourites', 'data':data}, 201

    @login_required
    def delete(self, fav_id):
        user = session['user']

        if user not in favourites:
            return {'error':'No favourites found'}, 404
        
        original_length = len(favourites[user])

        favourites = [
            f for f in favourites[user] if f.get('id') != fav_id
        ]    

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

api.add_resource(FavouriteAPI,
    '/api/favourites',
    '/api/favourites/<string:fav_id>'
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

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8000)