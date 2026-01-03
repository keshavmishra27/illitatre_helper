from flask import Flask
from backend.routes import main_blueprint
from backend import db
import os

app = Flask(
    __name__,
    template_folder="backend/templates",
    static_folder="static"
)

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user_details.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Gemini key from Render ENV
app.config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(main_blueprint)

if __name__ == "__main__":
    app.run()
