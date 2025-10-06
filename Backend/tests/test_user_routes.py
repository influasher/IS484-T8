import unittest
import uuid
import types
import sys
from datetime import datetime, timezone
from flask import Flask, jsonify
import flask_jwt_extended.view_decorators as vdec

try:
    from app.routes import user as mod
except Exception:
    import user as mod

class _User:
    """Simple user model stub with SQLAlchemy-like query API."""
    _store = []
    # Column-like attribute to support expressions in app.routes.user (User.id == <uuid>)
    class _Column:
        def __eq__(self, other):  # SQLAlchemy-like comparison compatibility
            return True
    id = _Column()


class _DBStub:
    class session:
        @staticmethod
        def add(obj):
            if isinstance(obj, _User):
                _User._store.append(obj)
            elif isinstance(obj, _ClientPreferences):
                _ClientPreferences._store.append(obj)

        @staticmethod
        def flush():
            pass

        @staticmethod
        def commit():
            pass

class _User:
    _store = []
    # Column-like attribute to support expressions in app.routes.user (User.id == <uuid>)
    class _Column:
        def __eq__(self, other):  # SQLAlchemy-like comparison compatibility
            return True
    id = _Column()

    def __init__(self, id, username, first_name, last_name, email, role, rm_id=None, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.rm_id = rm_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at

    def is_rm(self): return str(self.role).upper() == "RM"
    def is_client(self): return str(self.role).upper() == "CLIENT"

    class query:
        _first_override = None

        @classmethod
        def _items_list(cls):
            return list(_User._store)

        @classmethod
        def filter(cls, *args, **kwargs):
            class _Q:
                def first(self_inner):
                    return _User.query._first_override
            return _Q()

        @classmethod
        def filter_by(cls, **kwargs):
            items = cls._items_list()
            for k, v in kwargs.items():
                if k == "id":
                    items = [u for u in items if str(u.id) == str(v)]
                elif k == "role":
                    items = [u for u in items if str(u.role).upper() == str(v).upper()]
                elif k == "rm_id":
                    items = [u for u in items if (u.rm_id is not None and str(u.rm_id) == str(v))]
                else:
                    items = [u for u in items if getattr(u, k, None) == v]

            class _Q:
                def all(self_inner): return list(items)
                def first(self_inner): return items[0] if items else None
            return _Q()

        @classmethod
        def all(cls):
            return cls._items_list()

        @classmethod
        def get(cls, id_):
            for u in cls._items_list():
                if str(u.id) == str(id_):
                    return u
            return None


class _ClientPreferences:
    _store = []

    def __init__(self, user_id, holding=0.0, overall_pl=0.0, stop_loss_tolerance=None,
                 risk_cap=None, sectors=None, max_single_position_percent=None,
                 max_sector_allocation_percent=None, min_cash_reserve_percent=None):
        self.user_id = user_id
        self.holding = holding
        self.overall_pl = overall_pl
        self.stop_loss_tolerance = stop_loss_tolerance
        self.risk_cap = risk_cap
        self.sectors = sectors or []
        self.max_single_position_percent = max_single_position_percent
        self.max_sector_allocation_percent = max_sector_allocation_percent
        self.min_cash_reserve_percent = min_cash_reserve_percent

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "holding": self.holding,
            "overall_pl": self.overall_pl,
            "stop_loss_tolerance": self.stop_loss_tolerance,
            "risk_cap": self.risk_cap,
            "sectors": self.sectors,
            "max_single_position_percent": self.max_single_position_percent,
            "max_sector_allocation_percent": self.max_sector_allocation_percent,
            "min_cash_reserve_percent": self.min_cash_reserve_percent,
        }

    def apply_risk_profile_defaults(self):
        if self.risk_cap is None:
            self.risk_cap = "Moderate"
        if not self.sectors:
            self.sectors = []

    class query:
        @classmethod
        def filter_by(cls, **kwargs):
            items = [p for p in _ClientPreferences._store]
            for k, v in kwargs.items():
                if k == "user_id":
                    items = [p for p in items if str(p.user_id) == str(v)]
                else:
                    items = [p for p in items if getattr(p, k, None) == v]

            class _Q:
                def first(self_inner): return items[0] if items else None
            return _Q()


class UserRoutesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.testing = True

        # --- PATCH JWT VERIFICATION TO NO-OP ---
        self._orig_verify = vdec.verify_jwt_in_request
        vdec.verify_jwt_in_request = lambda *a, **k: None

        # ...existing patching...
        self.orig_db = mod.db
        self.orig_User = mod.User
        self.orig_Prefs = mod.ClientPreferences
        self.orig_jwt_required = mod.jwt_required
        self.orig_get_jwt_identity = mod.get_jwt_identity
        self.orig_format_response = mod.format_response

        mod.db = _DBStub
        mod.User = _User
        mod.ClientPreferences = _ClientPreferences

        mod.jwt_required = lambda *a, **k: (lambda f: f)

        self._current_identity = None
        mod.get_jwt_identity = lambda: self._current_identity
        mod.format_response = lambda data, msg, code: (jsonify({"data": data, "message": msg}), code)

        fake_portfolio = types.SimpleNamespace(
            get_client_portfolio_summary=lambda uid: {
                "total_portfolio_value": 123.0,
                "total_unrealized_pnl": 45.0,
            }
        )
        sys.modules['app.services.portfolio_service'] = fake_portfolio

        _User._store.clear()
        _ClientPreferences._store.clear()

        self.rm1 = _User(uuid.uuid4(), "rm1", "RM", "One", "rm1@example.com", "RM")
        self.rm2 = _User(uuid.uuid4(), "rm2", "RM", "Two", "rm2@example.com", "RM")
        self.c1 = _User(uuid.uuid4(), "c1", "C", "One", "c1@x.com", "CLIENT", rm_id=self.rm1.id)
        self.c2 = _User(uuid.uuid4(), "c2", "C", "Two", "c2@x.com", "CLIENT", rm_id=self.rm2.id)
        self.c3 = _User(uuid.uuid4(), "c3", "C", "Three", "c3@x.com", "CLIENT", rm_id=None)
        _User._store.extend([self.rm1, self.rm2, self.c1, self.c2, self.c3])

        self.app.register_blueprint(mod.user_bp, url_prefix="/user")
        self.client = self.app.test_client()

    def tearDown(self):
        # restore JWT verification
        vdec.verify_jwt_in_request = self._orig_verify

        # ...existing restores...
        mod.db = self.orig_db
        mod.User = self.orig_User
        mod.ClientPreferences = self.orig_Prefs
        mod.jwt_required = self.orig_jwt_required
        mod.get_jwt_identity = self.orig_get_jwt_identity
        mod.format_response = self.orig_format_response
        _User._store.clear()
        _ClientPreferences._store.clear()

    def _as_identity(self, user):
        self._current_identity = str(user.id)
        _User.query._first_override = user

    def test_get_clients_as_rm_success(self):
        self._as_identity(self.rm1)
        r = self.client.get("/user/clients")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["id"], str(self.c1.id))

    def test_get_clients_as_non_rm_forbidden(self):
        self._as_identity(self.c1)
        r = self.client.get("/user/clients")
        self.assertEqual(r.status_code, 403)
        self.assertIn("Access denied", r.get_json()["message"])

    def test_get_user_rm_can_view_own_client(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{self.c1.id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["data"]["id"], str(self.c1.id))

    def test_get_user_rm_cannot_view_other_rms_client(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{self.c2.id}")
        self.assertEqual(r.status_code, 403)

    def test_get_user_rm_can_view_self(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{self.rm1.id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["data"]["id"], str(self.rm1.id))

    def test_get_user_client_can_view_self_only(self):
        self._as_identity(self.c1)
        r_ok = self.client.get(f"/user/{self.c1.id}")
        self.assertEqual(r_ok.status_code, 200)
        r_no = self.client.get(f"/user/{self.c2.id}")
        self.assertEqual(r_no.status_code, 403)

    def test_get_user_invalid_id_format(self):
        self._as_identity(self.rm1)
        r = self.client.get("/user/not-a-uuid")
        self.assertEqual(r.status_code, 400)

    def test_get_user_not_found(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{uuid.uuid4()}")
        self.assertEqual(r.status_code, 404)

    def test_create_client_as_rm_success(self):
        self._as_identity(self.rm1)
        payload = {
            "username": "newc",
            "first_name": "New",
            "last_name": "Client",
            "email": "new@x.com",
            "holding": 1000.0,
            "overall_pl": 10.0,
            "stop_loss_tolerance": -15.0,
            "risk_cap": "Moderate",
            "sectors": ["Tech"],
            "max_single_position_percent": 20.0,
            "max_sector_allocation_percent": 40.0,
            "min_cash_reserve_percent": 10.0,
        }
        r = self.client.post("/user/create-clients", json=payload)
        self.assertEqual(r.status_code, 200)
        body = r.get_json()["data"]
        self.assertIn("user", body)
        self.assertIn("preferences", body)
        self.assertEqual(body["user"]["role"], "CLIENT")
        self.assertEqual(body["user"]["rm_id"], str(self.rm1.id))
        self.assertTrue(any(u.username == "newc" for u in _User._store))
        self.assertTrue(any(str(p.user_id) == body["user"]["id"] for p in _ClientPreferences._store))

    def test_create_client_non_rm_forbidden(self):
        self._as_identity(self.c1)
        r = self.client.post("/user/create-clients", json={"username": "x"})
        self.assertEqual(r.status_code, 403)

    def test_update_client_mutates_user_and_prefs(self):
        _ClientPreferences._store.append(_ClientPreferences(user_id=self.c1.id, holding=0.0, overall_pl=0.0, sectors=[]))
        self._as_identity(self.rm1)
        payload = {
            "username": "c1_updated",
            "first_name": "C1",
            "last_name": "Updated",
            "email": "c1u@x.com",
            "rm_id": str(self.rm1.id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "holding": 999.0,
            "overall_pl": 12.3,
            "stop_loss_tolerance": -12.0,
            "risk_cap": "Aggressive",
            "sectors": ["Energy"],
        }
        r = self.client.put(f"/user/{self.c1.id}", json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()["data"]
        self.assertEqual(data["user"]["username"], "c1_updated")
        pref = _ClientPreferences.query.filter_by(user_id=self.c1.id).first()
        self.assertEqual(pref.holding, 999.0)
        self.assertEqual(pref.risk_cap, "Aggressive")
        self.assertEqual(pref.sectors, ["Energy"])

    def test_update_client_not_found(self):
        self._as_identity(self.rm1)
        r = self.client.put(f"/user/{uuid.uuid4()}", json={"username": "nope"})
        self.assertEqual(r.status_code, 404)

    def test_get_preferences_as_rm_for_own_client_overrides_with_portfolio(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{self.c1.id}/preferences")
        self.assertEqual(r.status_code, 200)
        prefs = r.get_json()["data"]
        self.assertEqual(prefs["holding"], 123.0)
        self.assertEqual(prefs["overall_pl"], 45.0)
        p = _ClientPreferences.query.filter_by(user_id=self.c1.id).first()
        self.assertIsNotNone(p)

    def test_get_preferences_rm_cannot_access_other_rms_client(self):
        self._as_identity(self.rm1)
        r = self.client.get(f"/user/{self.c2.id}/preferences")
        self.assertEqual(r.status_code, 403)

    def test_get_preferences_client_can_access_self(self):
        self._as_identity(self.c1)
        r = self.client.get(f"/user/{self.c1.id}/preferences")
        self.assertEqual(r.status_code, 200)

    def test_get_preferences_client_cannot_access_other(self):
        self._as_identity(self.c1)
        r = self.client.get(f"/user/{self.c2.id}/preferences")
        self.assertEqual(r.status_code, 403)

    def test_get_preferences_invalid_uuid(self):
        self._as_identity(self.rm1)
        r = self.client.get("/user/not-a-uuid/preferences")
        self.assertEqual(r.status_code, 400)

    def test_put_preferences_create_and_update(self):
        self._as_identity(self.rm1)
        payload = {
            "holding": 10.0,
            "overall_pl": 5.0,
            "stop_loss_tolerance": -10.0,
            "risk_cap": "Conservative",
            "sectors": ["Tech", "Energy"],
            "max_single_position_percent": 25.0,
            "max_sector_allocation_percent": 40.0,
            "min_cash_reserve_percent": 12.0,
        }
        r1 = self.client.put(f"/user/{self.c1.id}/preferences", json=payload)
        self.assertEqual(r1.status_code, 200)
        out1 = r1.get_json()["data"]
        self.assertEqual(out1["risk_cap"], "Conservative")
        self.assertEqual(out1["sectors"], ["Tech", "Energy"])

        payload2 = {"risk_cap": "Aggressive", "sectors": ["Utilities"]}
        r2 = self.client.put(f"/user/{self.c1.id}/preferences", json=payload2)
        self.assertEqual(r2.status_code, 200)
        out2 = r2.get_json()["data"]
        self.assertEqual(out2["risk_cap"], "Aggressive")
        self.assertEqual(out2["sectors"], ["Utilities"])


if __name__ == "__main__":
    unittest.main()
