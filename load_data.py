from app.services.hockey import load_association_data
from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

database_uri = (
    f"postgresql://{os.environ['POSTGRES_USER']}:"
    f"{os.environ['POSTGRES_PASSWORD']}"
    f"@db:54321/{os.environ['POSTGRES_DB']}"
)

app = create_app(database_uri=database_uri)

with app.app_context():
    load_association_data()
