import pytest
from app import app, db, Contact

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Contact Manager' in response.data

def test_add_contact_success(client):
    response = client.post('/', data={'name': 'Alice', 'number': '12345'}, follow_redirects=True)
    assert b'Alice' in response.data
    assert b'12345' in response.data

def test_add_duplicate_contact(client):
    client.post('/', data={'name': 'Bob', 'number': '11111'}, follow_redirects=True)
    response = client.post('/', data={'name': 'Bob', 'number': '11111'}, follow_redirects=True)
    assert b'already exists' in response.data

def test_update_contact(client):
    client.post('/', data={'name': 'Charlie', 'number': '22222'}, follow_redirects=True)
    contact = Contact.query.filter_by(name='Charlie').first()
    response = client.post(f'/update/{contact.id}', data={'name': 'Charlie', 'number': '33333'}, follow_redirects=True)
    assert b'33333' in response.data

def test_update_contact_fail(client):
    response = client.post('/update/9999', data={'name': 'Ghost', 'number': '00000'}, follow_redirects=True)
    assert response.status_code == 404

def test_delete_contact(client):
    client.post('/', data={'name': 'Dave', 'number': '44444'}, follow_redirects=True)
    contact = Contact.query.filter_by(name='Dave').first()
    response = client.get(f'/delete/{contact.id}', follow_redirects=True)
    assert b'Dave' not in response.data

def test_delete_contact_fail(client):
    response = client.get('/delete/9999', follow_redirects=True)
    assert response.status_code == 404
