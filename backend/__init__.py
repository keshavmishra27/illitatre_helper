import os
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
try:
    import google.generativeai as genai
except ImportError:
    genai = None



# --- Initialize Extensions (Globally, unbound) ---
db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app(test_config=None):
    env_path = Path(__file__).resolve().parent.parent / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "super_secret_123")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///site.db") 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "uploads")
    app.config['PROCESSED_FOLDER'] = os.path.join(os.getcwd(), "processed")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    
    if test_config:
        app.config.update(test_config)

    # --- Initialize Extensions with App Context ---
    db.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    # Configure Gemini API (Hybrid setup)
    api_key = os.getenv("GOOGLE_API_KEY")

    if api_key and genai:
        genai.configure(api_key=api_key)
        app.config["GEMINI_API_KEY"] = api_key
    
    else:
        app.config['GEMINI_API_KEY'] = None
        print(" WARNING: GOOGLE_API_KEY not found. Gemini Cloud models disabled.")

    # --- Register Blueprints ---
    from . import models # Ensure models are imported before create_all
    from .routes import main_blueprint
    app.register_blueprint(main_blueprint)

    # Initialize the database and create tables
    with app.app_context():
        db.create_all()


    return app


