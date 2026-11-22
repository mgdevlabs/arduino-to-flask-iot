import time

from app import history

def test_record_and_read_last_24h():
    now = time.time()
    history.record(21.5, 45.0, ts=now - 120)
    history.record(22.5, 46.0, ts=now - 60)

    points = history.read_last_24h()

    assert len(points) == 2
    assert points[0]["temperature"] == 21.5
    assert points[1]["humidity"] == 46.0

def test_record_removes_samples_older_than_24h():
    now = time.time()
    history.record(10.0, 10.0, ts=now - 25 * 3600)
    history.record(20.0, 20.0, ts=now)

    points = history.read_last_24h()

    assert len(points) == 1
    assert points[0]["temperature"] == 20.0

def test_read_last_24h_without_data():
    assert history.read_last_24h() == []
