from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#user model represent user in database
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20),nullable = False)
    password = db.Column(db.String(20), nullable = False)
    admin = db.Column(db.Boolean, nullable = False, default = False)

#favourites model to represent favourites in database
class Favourites(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    #foreign keys to link to user and movie
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    movieID = db.Column(db.Integer, nullable = False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(10000), nullable = False)
    movieID = db.Column(db.Integer, nullable = False)
    #foreign key Links To Users
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    score = db.Column(db.Integer, primary_key = False)
    movieID = db.Column(db.Integer, nullable = False)
    #foreign keys to link to user and movie
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

#class reports(db.Model):
 #   id = db.Column(db.Integer, primary_key = True)
 #   user_id = db.Column(db.Integer, db.ForeignKey('users_db.id'), nullable = False)
   # movieID = db.Column(db.Integer, nullable = False)