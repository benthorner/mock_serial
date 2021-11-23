import logging
import time

import pytest
from retry import retry as retrier
from serial import Serial

from mock_serial import MockSerial


def retry(fn):
    # logger=None stops failure logs causing a false positive
    retrier(tries=9, delay=.1, logger=None)(fn)()


def hanger(*_):
    while True:
        time.sleep(1)


def test_open_close(
    caplog,
):
    mock_serial = MockSerial()
    caplog.set_level(logging.DEBUG)

    mock_serial.open()
    assert 'DEBUG - Attached to mock serial port.' in caplog.text

    mock_serial.close()
    assert 'DEBUG - Detaching mock serial port.' in caplog.text
    assert 'DEBUG - Detached mock serial port.' in caplog.text
    assert 'DEBUG - Closing mock serial port.' in caplog.text
    assert 'DEBUG - Closed mock serial port.' in caplog.text

    with pytest.raises(OSError):
        Serial(mock_serial.port)


# e.g. if the caller is still sending bytes during the close() sequence
def test_close_detach_hangs(
    caplog,
    mocker,
):
    caplog.set_level(logging.DEBUG)
    mocker.patch('mock_serial.mock_serial.os.read', side_effect=hanger)

    mock_serial = MockSerial()
    mock_serial.open()
    mock_serial.close()

    assert 'DEBUG - Detaching mock serial port.' in caplog.text
    assert 'WARNING - Unable to detach mock serial port.' in caplog.text
    assert 'DEBUG - Closing mock serial port.' in caplog.text


# e.g. if thread still reading (only seems to be a real issue on MacOS).
def test_close_master_hangs(
    caplog,
    mocker
):
    caplog.set_level(logging.DEBUG)
    mocker.patch('mock_serial.mock_serial.os.close', side_effect=hanger)

    mock_serial = MockSerial()
    mock_serial.open()
    mock_serial.close()

    assert 'DEBUG - Detaching mock serial port.' in caplog.text
    assert 'DEBUG - Closing mock serial port.' in caplog.text
    assert 'WARNING - Unable to close mock serial port.' in caplog.text


def test_stub_assert(
    caplog,
    mock_serial,
):
    caplog.set_level(logging.DEBUG)

    stub = mock_serial.stub(
        name='foo',
        receive_bytes=b'123',
        send_bytes=b'456'
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'123')

    def lazy_logger_assertions():
        assert "DEBUG - Buffer read: b'123'." in caplog.text
        assert "DEBUG - Match stub: b'123' => b'456'." in caplog.text
        assert "DEBUG - Buffer write: b'456'." in caplog.text

    assert serial.read(3) == b'456'
    retry(lazy_logger_assertions)

    assert stub == mock_serial.stubs['foo']
    assert stub.called
    assert stub.calls == 1


def test_stub_partial(
    caplog,
    mock_serial,
):
    caplog.set_level(logging.DEBUG)

    mock_serial.stub(
        receive_bytes=b'123',
        send_bytes=b'456',
    )

    mock_serial.stub(
        receive_bytes=b'abc',
        send_bytes=b'def',
    )

    def lazy_logger_assertions():
        assert "DEBUG - Match stub: b'123' => b'456'." in caplog.text
        assert "DEBUG - Match stub: b'abc' => b'def'." in caplog.text
        assert "Potential matches" not in caplog.text

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'abc123')

    assert serial.read(6) == b'def456'
    retry(lazy_logger_assertions)


def test_stub_longest(
    caplog,
    mock_serial,
):
    caplog.set_level(logging.DEBUG)

    mock_serial.stub(
        receive_bytes=b'123',
        send_bytes=b'456'
    )

    mock_serial.stub(
        receive_bytes=b'123456',
        send_bytes=b'789',
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'123')

    def lazy_logger_assertions():
        assert "DEBUG - Potential matches: [" \
                   "b'123' => b'456', " \
                   "b'123456' => b'789'" \
               "]." in caplog.text

    retry(lazy_logger_assertions)
    serial.write(b'456')
    assert serial.read(3) == b'789'


def test_stub_dynamic(
    caplog,
    mock_serial,
):
    caplog.set_level(logging.DEBUG)

    mock_serial.stub(
        receive_bytes=b'123',
        send_fn=lambda n: bytes(str(n), encoding='utf-8') + b'23'
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'123123')

    def lazy_logger_assertions():
        assert "DEBUG - Match stub: b'123' => fn()." in caplog.text
        assert "DEBUG - Buffer write: b'123'." in caplog.text
        assert "DEBUG - Buffer write: b'223'." in caplog.text

    assert serial.read(6) == b'123223'
    retry(lazy_logger_assertions)


def test_stub_override_bytes(
    mock_serial,
):
    old_stub = mock_serial.stub(
        receive_bytes=b'123',
        send_bytes=b'456'
    )

    new_stub = mock_serial.stub(
        receive_bytes=b'123',
        send_bytes=b'345'
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'123')

    assert serial.read(3) == b'345'
    assert new_stub.called
    assert not old_stub.called


def test_stub_override_name(
    mock_serial,
):
    old_stub = mock_serial.stub(
        name='foo',
        receive_bytes=b'123',
        send_bytes=b'456'
    )

    new_stub = mock_serial.stub(
        name='foo',
        receive_bytes=b'12',
        send_bytes=b'345'
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'123')

    assert serial.read(3) == b'345'
    assert new_stub.called
    assert not old_stub.called


def test_stub_no_match(
    caplog,
    mock_serial,
):
    caplog.set_level(logging.DEBUG)

    stub = mock_serial.stub(
        receive_bytes=b'123',
        send_bytes=b'456'
    )

    serial = Serial(mock_serial.port, timeout=1)
    serial.write(b'124')
    serial.write(b'123')

    def lazy_logger_assertions():
        assert "DEBUG - Buffer read: b'124" in caplog.text
        assert "DEBUG - Buffer read: b'124123'." in caplog.text
        assert "DEBUG - Buffer write" not in caplog.text
        assert "DEBUG - Match stub" not in caplog.text

    assert serial.read(3) == b''
    assert not stub.called
    retry(lazy_logger_assertions)
