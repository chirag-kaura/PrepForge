import os
import urllib.parse
from datetime import datetime
from typing import Any, Dict, Optional
import requests
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.user import User


def get_redirect_uri() -> str:
    """
    Automatically detects if running on Render production or localhost.
    """
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url.rstrip('/')}/"
    return "http://localhost:8501"


def get_google_auth_url() -> str:
    """
    Generates the Google OAuth 2.0 authorization URL.
    """
    redirect_uri = get_redirect_uri()
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user_info(code: str) -> Dict[str, Any]:
    """
    Exchanges the authorization code for user profile info from Google.
    """
    redirect_uri = get_redirect_uri()
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    token_resp = requests.post(token_url, data=token_data, timeout=10)
    token_resp.raise_for_status()
    tokens = token_resp.json()

    # Fetch user info using the access token
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    userinfo_resp = requests.get(userinfo_url, headers=headers, timeout=10)
    userinfo_resp.raise_for_status()

    return userinfo_resp.json()


def sync_user_to_db(db: Session, user_info: Dict[str, Any]) -> User:
    """
    Creates or updates the user record in PostgreSQL upon login.
    """
    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            last_login=datetime.utcnow(),
        )
        db.add(user)
    else:
        user.name = name
        user.picture = picture
        user.last_login = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user
