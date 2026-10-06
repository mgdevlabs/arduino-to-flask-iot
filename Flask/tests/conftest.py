import pytest
from app.data_storage import data_store

@pytest.fixture(autouse=True)
def reset_data_store():
    data_store.update(temperature=None, humidity=None)