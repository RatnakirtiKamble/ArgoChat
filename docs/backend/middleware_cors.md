### backend/middleware/cors.py

Purpose: Configure CORS policy for the FastAPI app.

Behavior:
- Adds `CORSMiddleware` with permissive settings:
  - `allow_origins=["*"]`
  - `allow_methods=["*"]`
  - `allow_headers=["*"]`
  - `allow_credentials=True`

Usage:
- Call `setup_cors(app)` after instantiating `FastAPI()`.

Security note:
- For production, restrict `allow_origins` to trusted domains.


