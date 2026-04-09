from app import app, db, users_db

def populate_users_db():
        if users_db.query.count() == 0:
            users = [
                users_db(username = "john", password = "password123", admin = False),
                users_db(username = "jane", password = "securepass", admin = False),
            ]
            
            #ensure no duplicates
            db.session.bulk_save_objects(users)
            db.session.commit()
            print("Populated Users database")
        else:
             print("Database alreadly contains data. No changes made")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        populate_users_db()