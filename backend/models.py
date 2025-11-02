from . import db # Imports db from backend/__init__.py

class UserDetail(db.Model):
    """
    Model for storing a single user's persistent details (Name, Age, Language).
    """
    __tablename__ = "user_details"

    id = db.Column(db.Integer, primary_key=True, default=1) 
    name = db.Column(db.String(100), nullable=False, default="N/A")
    age = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default="en")

    __table_args__ = (
        db.UniqueConstraint('id', name='uix_single_user'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "language": self.language
        }

# --- Database Helper Functions (Moved here to avoid circular imports) ---

def get_db_user_details(user_id=1):
    """
    Retrieves user details from the database or creates a default record 
    if one does not exist, guaranteeing a dictionary is always returned.
    """
    user = db.session.get(UserDetail, user_id)
    
    if user is None:
        # User not found: Create the default user record now
        default_user = UserDetail(id=user_id)
        db.session.add(default_user)
        db.session.commit()
        user = default_user # Set the user variable to the newly created object

    return user.to_dict() # Always return a dictionary

def store_db_user_details(user_data, user_id=1):
    """Stores/updates user details into the database."""
    user = db.session.get(UserDetail, user_id)
    
    if user:
        user.name = user_data['name']
        user.age = user_data['age']
        user.language = user_data['language']
    else:
        user = UserDetail(
            id=user_id,
            name=user_data['name'], 
            age=user_data['age'], 
            language=user_data['language']
        )
        db.session.add(user)
    
    db.session.commit()
    if not db.session.get(UserDetail, user_id):
        default_user = UserDetail(id=user_id)
        db.session.add(default_user)
        db.session.commit()