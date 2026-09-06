from app import app


def test_home_page_has_google_login():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    text = response.get_data(as_text=True).lower()
    assert 'secure notes' in text
    assert 'continue with google' in text or 'sign in with google' in text


def test_notes_route_requires_login():
    client = app.test_client()
    response = client.get('/notes')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'


def test_api_session_requires_token():
    client = app.test_client()
    response = client.post('/api/session', json={})
    assert response.status_code == 400
