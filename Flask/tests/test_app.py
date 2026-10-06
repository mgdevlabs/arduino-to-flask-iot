import pytest
from app import create_app
from app.data_storage import data_store


@pytest.fixture
def client():
    app = create_app({"TESTING" : True, "START_COMM_THREAD" :  False})
    return app.test_client()

def test_weather_endpoint_no_board(client):
    data_store.update(temperature=None, humidity=None)
    response = client.get("/api/weather")
    assert response.status_code == 200
    assert response.get_json() == {"temperature": None, "humidity": None}

def test_weather_endpoint_mock_data(client):
    data_store.update(temperature=23.4, humidity=32.1)
    response = client.get("/api/weather")
    assert response.get_json() == {"temperature": 23.4, "humidity": 32.1}

def test_weather_endpoint_missing_data(client):
    data_store.update(temperature=11.1)
    response = client.get("/api/weather")
    assert response.get_json() == {"temperature":11.1, "humidity": None}