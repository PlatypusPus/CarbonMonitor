"""Forgot-password flow: email link, single use, old password and sessions revoked."""
import re
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.role import Role
from models.user import User
from security import hash_password


def test_password_reset_via_email_link():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        role = Role(name='admin')
        db.add(role)
        db.add(User(email='reset@example.com', full_name='Reset', hashed_password=hash_password('Old-password-2026'),
            role=role, email_verified=True))
        db.commit()

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = session
    client = TestClient(app)
    mails = []

    def login(pw):
        return client.post('/api/auth/login', json={'email': 'reset@example.com', 'password': pw}).status_code
    try:
        with patch('routers.account.send_account_email', side_effect=lambda *args: mails.append(args)):
            unknown = client.post('/api/account/forgot-password', json={'email': 'nobody@example.com'})
            known = client.post('/api/account/forgot-password', json={'email': 'reset@example.com'})
            assert unknown.json() == known.json() and len(mails) == 1
            token = re.search(r'#token=(\S+)', mails[0][2]).group(1)
            assert '/reset-password#token=' in mails[0][2]
            assert client.post('/api/account/reset-password', json={'token': token, 'new_password': 'short'}).status_code == 422
            assert client.post('/api/account/reset-password', json={'token': token, 'new_password': 'New-password-2026'}).status_code == 200
            assert client.post('/api/account/reset-password', json={'token': token, 'new_password': 'Other-password-2026'}).status_code == 400
            assert login('Old-password-2026') == 401
            assert login('New-password-2026') == 200
    finally:
        app.dependency_overrides.clear()
