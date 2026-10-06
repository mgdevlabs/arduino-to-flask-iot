import pytest
from types import SimpleNamespace
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

def mock_port(device, description="", hwid=""):
    return SimpleNamespace(device=device, description=description, hwid=hwid)

# ------------ Arduino detection tests --------------------------

def test_detect_arduino_port_choice(monkeypatch):
    ports = [
        mock_port("COM1", "Some COM port (COM1)"),
        mock_port("COM3", "Arduino Uno (COM3)")
    ]
    monkeypatch.setattr(ds.list_ports, "comports", lambda: ports)
    assert ds.detect_arduino().device == "COM3"

def test_detect_arduino_no_match_error(monkeypatch):
    ports = [
        mock_port("COM1", "Some COM port (COM1)"),
        mock_port("COM3", "Other COM port (COM3)")
    ]
    monkeypatch.setattr(ds.list_ports, "comports", lambda: ports)

    with pytest.raises(RuntimeError):
        ds.detect_arduino()

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


