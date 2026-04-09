from app import app, db
from models import User, Favourites

#list of users
users = [
    {"username": "john", "password": "password123"},
    {"username":  "jane", "password": "securepass"},
]

favourites = [
    {"userID": 1, "movieID": 1},
    {"userID": 1, "movieID": 2},
    {"userID": 1, "movieID": 3},
    {"userID": 2, "movieID": 1},
    {"userID": 2, "movieID": 2},
]
    
with app.app_context():
    for user_data in users:
        new_user = User(
            username=user_data["username"],
            password=user_data["password"], 
        )
        db.session.add(new_user)
    
    for favourite_data in favourites:
        new_favourite = Favourites(
            userID = favourite_data["userID"],
            movieID = favourite_data["movieID"],
        )
        db.session.add(new_favourite)


        
    db.session.commit()
    print("Database populated with initial tables")