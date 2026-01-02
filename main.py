import time
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse

# ===============================
# CONFIG
# ===============================
CLIENT_KEY = "awuhdxqicla70byg"
CLIENT_SECRET = "PTv0jbHJiGyo81XdNf8jGqsy5FmsB0YY"

APP_BASE_URL = "https://tiktik-app.onrender.com"
REDIRECT_URI = APP_BASE_URL + "/callback"

SCOPES = "video.upload"  # Draft upload
TOKEN_FILE = "tokens.json"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# ===============================
# TikTok verification content
# ===============================
TIKTOK_VERIFY_CONTENT = "tiktok-developers-site-verification=KlnxUsN93VOBSrnPvaq7sWCP5RJhkgGA"

# ===============================
# APP
# ===============================
app = FastAPI(title="TikTok Minimal OAuth")

# -------------------------------
# utils
# -------------------------------
def load_tokens():
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tokens(tokens):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

# -------------------------------
# routes
# -------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>TikTok Minimal OAuth</h2>
    <ul>
      <li><a href="/login">Login with TikTok</a></li>
      <li><a href="/tokens">View Tokens</a></li>
    </ul>
    """

# ✅ TikTok VERIFY PAGE (NO HTML, NO EXTRA TEXT)
@app.get("/terms", response_class=PlainTextResponse)
def terms_verify():
    return TIKTOK_VERIFY_CONTENT

# ✅ รองรับกรณี TikTok เรียก /terms/
@app.get("/terms/", response_class=PlainTextResponse)
def terms_verify_slash():
    return TIKTOK_VERIFY_CONTENT

@app.get("/privacy", response_class=PlainTextResponse)
def privacy():
    return (
        "Privacy Policy\n\n"
        "This application does not collect or sell personal data.\n"
        "Authentication is handled by TikTok OAuth.\n\n"
        "Contact: you@example.com"
    )

@app.get("/login")
def login():
    params = {
        "client_key": CLIENT_KEY,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "state123",
    }
    q = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    return RedirectResponse(f"{AUTH_URL}?{q}")

@app.get("/callback", response_class=HTMLResponse)
def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return "<h3>No authorization code</h3>"

    data = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    r = requests.post(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=60,
    )
    r.raise_for_status()

    token_json = r.json()
    tokens = load_tokens()
    tokens[str(int(time.time()))] = token_json
    save_tokens(tokens)

    return """
    <h3>Authorized ✅</h3>
    <p>Token saved on server.</p>
    <p>You can close this tab.</p>
    """

@app.get("/tokens", response_class=HTMLResponse)
def tokens():
    return "<pre>" + json.dumps(load_tokens(), ensure_ascii=False, indent=2) + "</pre>"
