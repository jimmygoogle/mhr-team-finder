from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app(database_uri=None):
    app = Flask(__name__)

    # DATABASE_URL from docker-compose env
    if database_uri is None:
        database_uri = (
            f"postgresql://{os.environ['POSTGRES_USER']}:"
            f"{os.environ['POSTGRES_PASSWORD']}"
            f"@db:5432/{os.environ['POSTGRES_DB']}"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models here so Alembic sees them
    from app import models

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
