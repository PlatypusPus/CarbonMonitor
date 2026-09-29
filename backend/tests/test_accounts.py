"""Account lifecycle and organization isolation through the real HTTP routes."""
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.organization import EmailToken, Organization
from models.role import Role
from models.user import User
from models.activity_record import ActivityRecord


def test_verified_accounts_and_organization_boundaries():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Role(name='admin'), Role(name='facility_manager')])
        db.commit()

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = session
    client = TestClient(app)
    password = 'Account-password-2026!'
    mails = []

    def signup(email):
        result = client.post('/api/account/signup', json={'email': email, 'password': password,
            'full_name': 'Account owner', 'organization_name': email.split('@')[0]})
        assert result.status_code == 201, result.text
        return re.search(r'#token=(\S+)', mails[-1][2]).group(1)

    def login(email, secret=password):
        result = client.post('/api/auth/login', json={'email': email, 'password': secret})
        assert result.status_code == 200, result.text
        return {'Authorization': 'Bearer ' + result.json()['access_token']}

    try:
        with patch('routers.account.send_account_email', side_effect=lambda *args: mails.append(args)):
            first = signup('owner@example.com')
            assert client.post('/api/auth/login', json={'email': 'owner@example.com', 'password': password}).status_code == 403
            assert client.post('/api/account/resend-verification', json={'email': 'owner@example.com'}).status_code == 429
            with Session(engine) as db:
                assert db.query(EmailToken).one().token_hash != first
            assert client.post('/api/account/verify-email', json={'token': first}).status_code == 200
            assert client.post('/api/account/verify-email', json={'token': first}).status_code == 400
            owner = login('owner@example.com')
            facility = client.get('/api/facilities', headers=owner).json()[0]['id']
            owner_id = client.get('/api/auth/me', headers=owner).json()['id']

            second = signup('member@example.com')
            assert client.post('/api/account/verify-email', json={'token': second}).status_code == 200
            member = login('member@example.com')
            for route in ['/api/activity', '/api/activity/drafts', '/api/emissions/summary', '/api/emissions/latest', '/api/anomalies', '/api/calculations/']:
                response = client.get(route, headers=member)
                assert response.status_code == 200 and response.json() == [], (route, response.text)
            assert client.get('/api/facilities/' + facility, headers=member).status_code == 403
            assert client.patch('/api/users/' + owner_id, headers=member, json={'full_name': 'Intruder'}).status_code == 404
            assert len(client.get('/api/users', headers=member).json()) == 1
            assert client.post('/api/account/invitations', headers=member,
                json={'email': 'someone@example.com', 'facility_id': facility}).status_code == 403

            # An actual record belonging to the first organization stays hidden.
            with Session(engine) as db:
                owner_row = db.query(User).filter_by(email='owner@example.com').one()
                record = ActivityRecord(facility_id=owner_row.facility_id, activity_type='electricity', quantity=100,
                    unit='kWh', source='manual', confirmed_by_user=True,
                    period_start=datetime(2026, 1, 1), period_end=datetime(2026, 2, 1))
                db.add(record)
                db.commit()
                record_id = str(record.id)
            assert client.get('/api/activity', headers=member).json() == []
            assert client.get('/api/activity/' + record_id, headers=member).status_code == 403
            assert client.delete('/api/activity/' + record_id, headers=member).status_code == 403
            assert client.post('/api/calculations/' + record_id + '/calculate', headers=member).status_code == 403
            assert client.request('DELETE', '/api/account/profile', headers=owner,
                json={'password': password, 'confirmation': 'DELETE'}).status_code == 409

            assert client.post('/api/account/invitations', headers=owner,
                json={'email': 'member@example.com', 'facility_id': facility}).status_code == 201
            invitation = re.search(r'#token=(\S+)', mails[-1][2]).group(1)
            assert client.post('/api/account/join', headers=owner, json={'token': invitation}).status_code == 403
            preview = client.post('/api/account/invitations/preview', headers=member, json={'token': invitation})
            assert preview.status_code == 200 and preview.json()['organization'] == 'owner'
            assert client.post('/api/account/join', headers=member, json={'token': invitation}).status_code == 200
            assert client.get('/api/auth/me', headers=member).status_code == 401
            assert client.post('/api/auth/refresh').status_code == 401
            member = login('member@example.com')
            assert client.post('/api/account/join', headers=member, json={'token': invitation}).status_code == 400
            assert client.get('/api/auth/me', headers=member).json()['role'] == 'facility_manager'
            assert len(client.get('/api/activity', headers=member).json()) == 1
            assert client.patch('/api/account/profile', headers=member, json={'full_name': 'Updated member'}).status_code == 200
            assert client.get('/api/account/profile', headers=member).json()['full_name'] == 'Updated member'
            assert client.post('/api/account/password', headers=member,
                json={'current_password': 'wrong', 'new_password': password + '2'}).status_code == 403
            assert client.post('/api/account/password', headers=member,
                json={'current_password': password, 'new_password': password + '2'}).status_code == 200
            assert client.get('/api/auth/me', headers=member).status_code == 401
            assert client.post('/api/auth/login', json={'email': 'member@example.com', 'password': password}).status_code == 401
            member = login('member@example.com', password + '2')
            assert client.request('DELETE', '/api/account/profile', headers=member,
                json={'password': password + '2', 'confirmation': 'DELETE'}).status_code == 204
            assert client.get('/api/auth/me', headers=member).status_code == 401
            assert len(client.get('/api/activity', headers=owner).json()) == 1
            assert client.get('/api/users', headers=owner).status_code == 200

            expired = signup('expired@example.com')
            with Session(engine) as db:
                db.query(EmailToken).filter_by(email='expired@example.com').update({'expires_at': datetime.now(timezone.utc) - timedelta(days=1)})
                db.commit()
            assert client.post('/api/account/verify-email', json={'token': expired}).status_code == 400

        with patch('routers.account.send_account_email', side_effect=HTTPException(503, 'Mail unavailable')):
            result = client.post('/api/account/signup', json={'email': 'failed@example.com', 'password': password,
                'full_name': 'Failed', 'organization_name': 'Failed organization'})
            assert result.status_code == 503
            with Session(engine) as db:
                assert db.query(User).filter_by(email='failed@example.com').count() == 0
                assert db.query(Organization).filter_by(name='Failed organization').count() == 0
    finally:
        app.dependency_overrides.clear()
        client.close()
        engine.dispose()
