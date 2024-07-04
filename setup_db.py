from app import db, app

# Initialize Flask app context


# Create all database tables
with app.app_context():
    db.create_all()
    
