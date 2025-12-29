from flask import Flask
from flask_cors import CORS
import os
import cloudinary
from dotenv import load_dotenv

from database.db_manager import init_db
from routes.main_routes import init_routes
from utils.azure_face_api import init_azure_face_detector

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ⚠️ For production, move this to env as well
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_only_secret")

# ------------- CLOUDINARY CONFIG --------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ------------- AZURE FACE API CONFIG --------------
try:
    azure_api_key = os.getenv("AZURE_FACE_API_KEY")
    azure_endpoint = os.getenv("AZURE_FACE_ENDPOINT")

    if not azure_api_key or not azure_endpoint:
        raise ValueError("Azure Face API credentials missing")

    # Clean endpoint
    azure_endpoint = azure_endpoint.rstrip("/")

    init_azure_face_detector(azure_api_key, azure_endpoint)
    print("✅ Azure Face API initialized successfully")

except Exception as e:
    print(f"⚠️ Azure Face API disabled: {e}")

# Initialize routes
init_routes(app)

# ----------------- START APP ------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
