import time
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse

# ===============================
# CONFIG (ใส่ตรงนี้เลย)
# ===============================
CLIENT_KEY = "awuhdxqicla70byg"
CLIENT_SECRET = "PTv0jbHJiGyo81XdNf8jGqsy5FmsB0YY"

APP_BASE_URL = "https://tiktik-app.onrender.com"
REDIRECT_URI = APP_BASE_URL + "/callback"

SCOPES = "video.upload"  # Draft upload (แนะนำ)
TOKEN_FILE = "tokens.json"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# ===============================
# TikTok URL Verification (Signature File)
# TikTok บอกให้ upload ไปที่:
# https://tiktik-app.onrender.com/terms/tiktokwLIttPrJS1EvAUJU8iWEmFkYExIP3soq.txt
# ===============================
TIKTOK_VERIFY_FILENAME = "tiktokwLIttPrJS1EvAUJU8iWEmFkYExIP3soq.txt"

# ⚠️ เอา "เนื้อหาในไฟล์" ที่ TikTok ให้ มาใส่ตรงนี้แบบ EXACT (ห้ามมีเว้นวรรค/ขึ้นบรรทัดเกิน)
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
    return f"""
    <h2>TikTok Minimal OAuth</h2>
    <ul>
      <li><a href="/login">Login with TikTok</a></li>
      <li><a href="/tokens">View Tokens</a></li>
      <li><a href="/terms">Terms</a></li>
      <li><a href="/privacy">Privacy</a></li>
      <li><a href="/terms/{TIKTOK_VERIFY_FILENAME}">TikTok Verify File</a></li>
    </ul>
    """

@app.get("/terms", response_class=PlainTextResponse)
def terms():
    return (
        "Terms of Service\n\n"
        "This application is used solely to authorize and upload video content "
        "to TikTok on behalf of the user.\n\n"
        "Contact: you@example.com"
    )

@app.get("/privacy", response_class=PlainTextResponse)
def privacy():
    return (
        "Privacy Policy\n\n"
        "This application does not collect or sell personal data.\n"
        "Authentication is handled by TikTok OAuth.\n\n"
        "Contact: you@example.com"
    )

# ✅ TikTok signature file route (สำคัญสุดสำหรับ Verify URL)
@app.get(f"/terms/{TIKTOK_VERIFY_FILENAME}", response_class=PlainTextResponse)
def tiktok_verify_file():
    # ต้องตรงเป๊ะตามไฟล์ที่ TikTok ให้ (ไม่มี HTML ไม่ต้องมี header อะไรเพิ่ม)
    return TIKTOK_VERIFY_CONTENT

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
    # ✅ fix closing </pre>
    return "<pre>" + json.dumps(load_tokens(), ensure_ascii=False, indent=2) + "</pre>"
