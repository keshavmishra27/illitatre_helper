from flask_sqlalchemy import SQLAlchemy
from . import db

class UserDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="N/A")
    age = db.Column(db.Integer, default=0)
    language = db.Column(db.String(20), default="en")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "age": self.age, "language": self.language}


def store_db_user_details(user_data, user_id=1):
    """✅ Safely updates only provided user fields without overwriting others."""
    user = db.session.get(UserDetail, user_id)
    if not user:
        user = UserDetail(id=user_id)
        db.session.add(user)

    for key, value in user_data.items():
        if hasattr(user, key) and value not in [None, "", "N/A"]:
            setattr(user, key, value)

    db.session.commit()
    return user.to_dict()


def get_db_user_details(user_id=1):
    """✅ Fetch user details safely."""
    user = db.session.get(UserDetail, user_id)
    if user:
        return user.to_dict()
    else:
        return {"name": "N/A", "age": 0, "language": "en"}
