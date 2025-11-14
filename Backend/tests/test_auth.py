import re
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

# Import the auth module (supports both "app.routes.auth" and flat "auth.py")
try:
    from app.routes import auth as auth_module
except Exception:
    import auth as auth_module


# ---------- Helpers / Fakes ----------

class RoleStub:
    def __init__(self, value: str):
        self.value = value


class UserObj:
    def __init__(
        self,
        id: int = 1,
        email: str = "user@example.com",
        username: str = "testuser",
        first_name: str = "Test",
        last_name: str = "User",
        role_value: str = "ADMIN",
        is_client: bool = False,
        rm_id=None,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.role = RoleStub(role_value)
        self.rm_id = rm_id
        self._is_client_flag = is_client

    def is_client(self) -> bool:
        return self._is_client_flag


class QueryStub:
    """
    Minimal stub to imitate SQLAlchemy's query chaining:
    - .filter_by(...).first()
    - .filter(...).first()
    """
    def __init__(self, first_value=None):
        self._first_value = first_value

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value


class OTPRecordStub:
    def __init__(self, user: UserObj, expired: bool = False, is_used: bool = False):
        self.user = user
        self._expired = expired
        self.is_used = is_used

    def is_expired(self) -> bool:
        return self._expired

    def mark_as_used(self):
        self.is_used = True


class EmailServiceOK:
    "Email service that records last call and returns True."
    last_call = None

    def __init__(self):
        pass

    def send_otp_email(self, recipient_email: str, otp_code: str, user_name: str) -> bool:
        EmailServiceOK.last_call = {
            "recipient_email": recipient_email,
            "otp_code": otp_code,
            "user_name": user_name,
        }
        return True


class EmailServiceFail:
    "Email service that returns False."
    def send_otp_email(self, recipient_email: str, otp_code: str, user_name: str) -> bool:
        return False


class EmailServiceRaise:
    "Email service that raises an exception."
    def send_otp_email(self, recipient_email: str, otp_code: str, user_name: str) -> bool:
        raise RuntimeError("boom")


# ---------- Pytest Fixtures ----------

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    jwt = JWTManager(app)
    app.register_blueprint(auth_module.auth_bp, url_prefix="/auth")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_blacklist():
    # Ensure blacklist is clean for each test
    try:
        auth_module.blacklist.clear()
    except Exception:
        pass
    yield
    try:
        auth_module.blacklist.clear()
    except Exception:
        pass


# ---------- /login tests ----------

def test_login_missing_email_returns_400(client, monkeypatch):
    resp = client.post("/auth/login", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["message"] == "Email is required"


def test_login_user_not_found_returns_404(client, monkeypatch):
    class UserStub:
        query = QueryStub(first_value=None)

    monkeypatch.setattr(auth_module, "User", UserStub)
    resp = client.post("/auth/login", json={"email": "missing@example.com"})
    assert resp.status_code == 404
    assert resp.get_json()["message"].startswith("User not found")


def test_login_client_without_rm_returns_403(client, monkeypatch):
    user = UserObj(is_client=True, role_value="CLIENT", rm_id=None)
    class UserStub:
        query = QueryStub(first_value=user)

    monkeypatch.setattr(auth_module, "User", UserStub)
    # Email service OK but should not matter (blocked before sending)
    monkeypatch.setattr(auth_module, "EmailService", EmailServiceOK)
    resp = client.post("/auth/login", json={"email": user.email})
    assert resp.status_code == 403
    assert "Access denied" in resp.get_json()["message"]


def test_login_success_sends_otp_and_returns_200(client, monkeypatch):
    user = UserObj(is_client=False, role_value="ADMIN", rm_id=123)

    created_calls = []
    def create_new_otp(user_id, otp_code):
        created_calls.append({"user_id": user_id, "otp_code": otp_code})

    class UserStub:
        query = QueryStub(first_value=user)

    class UserOTPStub:
        create_new_otp = staticmethod(create_new_otp)

    monkeypatch.setattr(auth_module, "User", UserStub)
    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)
    monkeypatch.setattr(auth_module, "EmailService", EmailServiceOK)

    resp = client.post("/auth/login", json={"email": user.email})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "OTP sent successfully"
    assert "OTP sent to" in data["data"]["message"]

    # Ensure OTP was created
    assert len(created_calls) == 1
    # Ensure email was sent with a 6-digit OTP
    assert EmailServiceOK.last_call is not None
    assert EmailServiceOK.last_call["recipient_email"] == user.email
    assert re.fullmatch(r"\d{6}", EmailServiceOK.last_call["otp_code"]) is not None


def test_login_email_send_failure_returns_500(client, monkeypatch):
    user = UserObj(is_client=False, role_value="ADMIN", rm_id=123)

    class UserStub:
        query = QueryStub(first_value=user)

    class UserOTPStub:
        create_new_otp = staticmethod(lambda user_id, otp_code: None)

    monkeypatch.setattr(auth_module, "User", UserStub)
    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)
    monkeypatch.setattr(auth_module, "EmailService", EmailServiceFail)

    resp = client.post("/auth/login", json={"email": user.email})
    assert resp.status_code == 500
    assert "Failed to send OTP email" in resp.get_json()["message"]


def test_login_email_exception_returns_500(client, monkeypatch):
    user = UserObj(is_client=False, role_value="ADMIN", rm_id=123)

    class UserStub:
        query = QueryStub(first_value=user)

    class UserOTPStub:
        create_new_otp = staticmethod(lambda user_id, otp_code: None)

    monkeypatch.setattr(auth_module, "User", UserStub)
    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)
    monkeypatch.setattr(auth_module, "EmailService", EmailServiceRaise)

    resp = client.post("/auth/login", json={"email": user.email})
    assert resp.status_code == 500
    assert "Failed to send OTP email" in resp.get_json()["message"]


# ---------- /verify-otp tests ----------

def test_verify_otp_missing_code_returns_400(client):
    resp = client.post("/auth/verify-otp", json={})
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "OTP code is required"


def test_verify_otp_invalid_code_returns_401(client, monkeypatch):
    class UserOTPStub:
        query = QueryStub(first_value=None)

    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)
    resp = client.post("/auth/verify-otp", json={"otp_code": "000000"})
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid OTP code"


def test_verify_otp_expired_returns_401(client, monkeypatch):
    user = UserObj()
    otp_record = OTPRecordStub(user=user, expired=True)
    class UserOTPStub:
        query = QueryStub(first_value=otp_record)

    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)
    resp = client.post("/auth/verify-otp", json={"otp_code": "123456"})
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "OTP has expired"


def test_verify_otp_success_marks_used_and_returns_token(client, monkeypatch):
    user = UserObj()
    otp_record = OTPRecordStub(user=user, expired=False, is_used=False)

    class UserOTPStub:
        query = QueryStub(first_value=otp_record)

    monkeypatch.setattr(auth_module, "UserOTP", UserOTPStub)

    resp = client.post("/auth/verify-otp", json={"otp_code": "654321"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["message"] == "Login successful"
    assert "access_token" in body["data"]
    assert body["data"]["user"]["email"] == user.email
    assert otp_record.is_used is True


# ---------- /protected tests ----------

def _auth_header_for(app, identity: str):
    with app.app_context():
        token = create_access_token(identity=identity)
    return {"Authorization": f"Bearer {token}"}


def test_protected_requires_auth_returns_401(client):
    resp = client.get("/auth/protected")
    assert resp.status_code == 401  # missing token


def test_protected_user_not_found_returns_404(client, monkeypatch, app):
    class UserStub:
        query = QueryStub(first_value=None)

    monkeypatch.setattr(auth_module, "User", UserStub)

    headers = _auth_header_for(app, identity="999")
    resp = client.get("/auth/protected", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["message"] == "User not found"


def test_protected_success_returns_user_data(client, monkeypatch, app):
    user = UserObj(id=7, email="u7@example.com", username="u7")
    class UserStub:
        query = QueryStub(first_value=user)

    monkeypatch.setattr(auth_module, "User", UserStub)

    headers = _auth_header_for(app, identity=str(user.id))
    resp = client.get("/auth/protected", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email


def test_protected_with_blacklisted_token_returns_401(client, monkeypatch, app):
    # Create a valid token and blacklist it by calling /logout first
    user = UserObj(id=1)
    class UserStub:
        query = QueryStub(first_value=user)

    monkeypatch.setattr(auth_module, "User", UserStub)

    headers = _auth_header_for(app, identity=str(user.id))
    # Blacklist the token by logging out
    resp_logout = client.post("/auth/logout", headers=headers)
    assert resp_logout.status_code == 200

    # Now the same token should be rejected at /protected
    resp = client.get("/auth/protected", headers=headers)
    assert resp.status_code == 401
    assert "revoked" in resp.get_json()["message"]


# ---------- /logout tests ----------

def test_logout_requires_auth_returns_401(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 401  # missing token


def test_logout_blacklists_token_and_returns_200(client, monkeypatch, app):
    before = len(auth_module.blacklist)
    user = UserObj(id=44)
    class UserStub:
        query = QueryStub(first_value=user)

    monkeypatch.setattr(auth_module, "User", UserStub)

    headers = _auth_header_for(app, identity=str(user.id))
    resp = client.post("/auth/logout", headers=headers)
    assert resp.status_code == 200
    after = len(auth_module.blacklist)
    assert after == before + 1

    # Prove practical effect: protected should now reject same token
    resp2 = client.get("/auth/protected", headers=headers)
    assert resp2.status_code == 401
