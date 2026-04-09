from app import db, app
from models import User

with app.app_context():
    db.create_all()
    print("Databases have been successfully created")   
