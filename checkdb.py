from app import app
from models import User, Favourites, Review

with app.app_context():
    print("Users:", User.query.count())
    print("Favourites:", Favourites.query.count())
    print("Reviews:", Review.query.count())