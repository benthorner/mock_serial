import pytest

from mock_serial.stub import Stub


@pytest.mark.parametrize('send_bytes', [
    b'456',
    b''
])
def test_call_send_bytes(send_bytes):
    stub = Stub(receive_bytes=b'123', send_bytes=send_bytes)
    assert stub.call() == send_bytes
    assert stub.call() == send_bytes  # unchanging


@pytest.mark.parametrize('kwargs', [
    {},
    {'send_bytes': b'1', 'send_fn': lambda _n: b'1'}
])
def test_init_bad_args(kwargs):
    with pytest.raises(TypeError) as excinfo:
        Stub(receive_bytes=b'123', **kwargs)

    msg = 'Specify either send_bytes or send_fn.'
    assert str(excinfo.value) == msg
