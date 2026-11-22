import pytest
from serial import SerialException

from app import data_storage as ds

class MockSerial:

    def __init__(self, replies=()):
        self.replies= list(replies)
        self.written = []
        self.closed = False

    def write(self, data):
        self.written.append(data)

    def readline(self):
        if not self.replies:
            return b""
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def close(self):
        self.closed = True

# ------------ Arduino port configuration tests --------------------------

def test_connect_uses_port_from_env(monkeypatch):
    opened = []

    def fake_serial(port, baudrate, timeout):
        opened.append((port, baudrate, timeout))
        return MockSerial()

    monkeypatch.setenv("ARDUINO_PORT", "/dev/ttyACM0")
    monkeypatch.setattr(ds, "Serial", fake_serial)
    monkeypatch.setattr(ds.time, "sleep", lambda _: None)

    ds.connect()

    assert opened == [("/dev/ttyACM0", 9600, 1)]

def test_connect_without_port_raises(monkeypatch):
    monkeypatch.delenv("ARDUINO_PORT", raising=False)

    with pytest.raises(RuntimeError, match="ARDUINO_PORT"):
        ds.connect()

# ------------ parse tests --------------------------------------
def test_parse_reading_valid():
    assert ds.parse_reading("12.34;56.78") == (12.34, 56.78)

@pytest.mark.parametrize("line", ["random", "1;2;3", "aaa;bbb", "12.34"])
def test_parse_reading_invalid(line):
    with pytest.raises(ValueError):
        ds.parse_reading(line)

# ------------ poll_once tests ----------------------------------

def test_poll_once_stores_reading():
    ser = MockSerial([b"12.34;56.78\r\n"])
    ds.poll_once(ser)
    assert ser.written == [b"GET\n"]
    assert ds.data_store.get() == {"temperature": 12.34, "humidity": 56.78}

def test_poll_once_saves_reading_to_history(monkeypatch):
    saved = []
    monkeypatch.setattr(ds.history, "record", lambda t, h: saved.append((t, h)))

    ds.poll_once(MockSerial([b"12.34;56.78\r\n"]))

    assert saved == [(12.34, 56.78)]

def test_poll_once_ignores_invalid_line():
    ds.data_store.update(temperature=20.0, humidity=40.0)
    ds.poll_once(MockSerial([b"invalid\r\n"]))
    assert ds.data_store.get() == {"temperature": 20.0, "humidity": 40.0}

def test_poll_once_ignores_empty_line():
    ds.poll_once(MockSerial([]))
    assert ds.data_store.get() == {"temperature": None, "humidity": None}

# ------------ poll_step tests ----------------------------------

def test_poll_step_connects_on_start(monkeypatch):
    mock = MockSerial([b"20.0;40.0\n"])
    monkeypatch.setattr(ds, "connect", lambda: mock)

    assert ds.poll_step(None) is mock
    assert ds.data_store.get() == {"temperature": 20.0, "humidity": 40.0}

def test_poll_step_no_board_clears_data(monkeypatch):
    def no_board():
        raise RuntimeError("No Arduino detected")

    monkeypatch.setattr(ds, "connect", no_board)
    ds.data_store.update(temperature=20.0, humidity=40.0)

    assert ds.poll_step(None) is None
    assert ds.data_store.get() == {"temperature": None, "humidity": None}

def test_poll_step_disconnected_closes_and_clears():
    ser = MockSerial([SerialException("Board disconnected")])
    ds.data_store.update(temperature=20.0, humidity=40.0)

    assert ds.poll_step(ser) is None
    assert ser.closed
    assert ds.data_store.get() == {"temperature": None, "humidity": None}

def test_poll_step_reconnects(monkeypatch):
    monkeypatch.setattr(ds, "connect", lambda: MockSerial([b"20.0;40.0\n"]))
    ds.data_store.update(temperature=None, humidity=None)

    ser = ds.poll_step(None)
    assert ser is not None
    assert ds.data_store.get() == {"temperature": 20.0, "humidity": 40.0}


