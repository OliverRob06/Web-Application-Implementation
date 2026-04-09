from app import app
from models import User, Favourites

with app.app_context():
    print("Users:", User.query.count())
    print("Favourites:", Favourites.query.count())