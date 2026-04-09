from app import app, db
from models import User, Favourites, Review, Rating, Report
from werkzeug.security import generate_password_hash, check_password_hash



#hashing passwords
#john hashed password
john_hashed_pw = generate_password_hash("password123")
#jane hashed password
jane_hashed_pw = generate_password_hash("securepass")
#admin hashed password
admin_hashed_pw = generate_password_hash("adminPW")




#list of users
users = [
    {"username": "john", "password": john_hashed_pw, "admin": False},
    {"username":  "jane", "password": jane_hashed_pw, "admin": False},
    {"username": "admin", "password": admin_hashed_pw, "admin": True},   
]

#user favourites
favourites = [
    {"userID": 1, "movieID": 5},
    {"userID": 1, "movieID": 2},
    {"userID": 1, "movieID": 3},
    {"userID": 2, "movieID": 5},
    {"userID": 2, "movieID": 2},
]

reviews = [
    {"userID": 1, "movieID": 5, "content": "Four Rooms (1995) is a quirky, chaotic anthology anchored by Tim Roth as a beleaguered bellhop, offering wildly inventive and uneven stories that mix dark humor and absurdity, making it a fun but disjointed cinematic ride."},
    {"userID": 1, "movieID": 21, "content": "The Endless Summer is a visually stunning and timeless surf documentary that captures the thrill of chasing waves around the world with infectious joy and wanderlust."},
    {"userID": 2, "movieID": 69, "content": "Walk the Line is a compelling biopic that brilliantly captures Johnny Cash’s raw talent and turbulent life, anchored by powerful performances and soulful music."},
]
    
ratings = [
    {"userID": 1, "movieID": 5, "score": 10},
    {"userID": 1, "movieID": 4, "score": 3},
    {"userID": 1, "movieID": 3, "score": 4},
]

reports = [
    {"userID": 1, "reviewID": 1},
    {"userID": 1, "reviewID": 2},
    {"userID": 1, "reviewID": 1},
    {"userID": 2, "reviewID": 2},
    {"userID": 2, "reviewID": 3},
]
with app.app_context():
    for user_data in users:
        new_user = User(
            username=user_data["username"],
            password=user_data["password"], 
            admin = user_data["admin"],
        )
        db.session.add(new_user)
    
    for favourite_data in favourites:
        new_favourite = Favourites(
            userID = favourite_data["userID"],
            movieID = favourite_data["movieID"],
        )
        db.session.add(new_favourite)
    
    for review_data in reviews:
        new_review = Review(
            userID = review_data["userID"],
            movieID = review_data["movieID"],
            content = review_data["content"],
        )
        db.session.add(new_review)

    for rating_data in ratings:
        new_rating = Rating(
            userID = rating_data["userID"],
            movieID = rating_data["movieID"],
            score = rating_data["score"],
        )
        db.session.add(new_rating)
    
    for report_data in reports:
        new_report = Report(
            userID = report_data["userID"],
            reviewID = report_data["reviewID"]
        )
        db.session.add(new_report)
    
    
        
    db.session.commit()
    print("Database populated with initial tables")