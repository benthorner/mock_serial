import pytest

from .mock_serial import MockSerial


@pytest.fixture
def mock_serial():
    mock = MockSerial()
    mock.open()
    yield mock
    mock.close()
