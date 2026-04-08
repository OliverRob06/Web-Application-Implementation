from app import app, db, testfavourites

def populate_favourites():
    if testfavourites.query.count() == 0:
        favourite = [
            testfavourites(userID = 1, movieID = 1),
            testfavourites(userID = 1, movieID = 2),
            testfavourites(userID = 1, movieID = 3),
            testfavourites(userID = 2, movieID = 1),
            testfavourites(userID = 2, movieID = 2),
        ]

        db.session.bulk_save_objects(favourite)
        db.session.commit()
        print("Populated Users database")
    else:
        print("Database alreadly contains data. No changes made")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        populate_favourites()