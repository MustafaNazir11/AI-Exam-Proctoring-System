from flask import Flask
from flask_cors import CORS
import os
import cloudinary
from database.db_manager import init_db
from routes.main_routes import init_routes

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "super_secret_key_123"

# ------------- CLOUDINARY CONFIG --------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
)

# Initialize routes
init_routes(app)

# ----------------- START APP ------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)