from models import db, User
from app import app

with app.app_context():
    # Check if the columns already exist
    existing_columns = db.inspect(User).columns.keys()
    
    if 'age' not in existing_columns:
        db.session.execute('ALTER TABLE user ADD COLUMN age INTEGER')
    
    if 'profile_picture' not in existing_columns:
        db.session.execute('ALTER TABLE user ADD COLUMN profile_picture VARCHAR(150)')
    
    db.session.commit()
