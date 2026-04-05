from flask import Flask, render_template, request, redirect, url_for, session
from flask_restful import Api, Resource
from auth import ADMIN_PASSWD, admin_required
import os
from functools import wraps
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

#if the user isnt logged in send user to index.html
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # If it's an API request, return JSON instead
            if request.path.startswith('/api/'):
                return {"error": "Unauthorized"}, 401
            
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
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

# change when other areas are done
# api for searching movies, else return all movies
class MovieAPI(Resource):
    @login_required
    def get(self, movie_id=None):
        if movie_id:
            return {'message': f'Get movie {movie_id}'}, 200
        
        query = request.args.get('q')
        if query:
            return {'message': f'Search for {query}'}, 200
        
        return {'message':'All movies'}, 200
    

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



if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8000)