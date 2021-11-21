# mock_serial

A mock utility for testing serial devices.

Credit to [Dolf Andringa](http://allican.be/blog/2017/01/15/python-dummy-serial-port.html) for the technique. 🏆

## Install

```
pip install mock_serial
```

Note: this package [does not work on Windows](https://stackoverflow.com/questions/52062977/unable-to-import-termios-package).

## Usage

First setup a basic session with a `MockSerial` device.

```python
from mock_serial import MockSerial

device = MockSerial()
device.open()

from serial import Serial
serial = Serial(device.port)

...

serial.close()
device.close()
```

Alternatively, a pytest fixture is included automatically.

```
from serial import Serial

def test_example(mock_serial):
  serial = Serial(device.port)

  ...

  serial.close()
```


### `.stub()`

Use the `.stub()` method to simulate device behaviour.

```python
stub = device.stub(
  receive_bytes=b'123',
  send_bytes=b'456'
)

...

serial.write(b'123')
assert serial.read(3) == b'456'

assert stub.called
assert stub.calls == 1
```

You can also give your stub a name for easy retrieval.

```python
device.stub(
  name='foo',
  receive_bytes=b'123',
  send_bytes=b'456'
)

...

assert device.stubs['foo'].called
```

`stub()` can simulate a variety of device behaviours:

- **Lazy matching**. MockSerial will defer sending a response until only one stub could match. This can be useful if certain byte sequences are ambiguous e.g. if another stub had `receive_bytes = b'123456'` then MockSerial will wait until it can rule out matching the "longer" stub in future.

- **Partial matching**. MockSerial doesn't need to match all the data it's read in one go. This can be useful if your code or library doesn't wait for replies e.g. `b'123'` followed quickly by `b'456'` may be received as `b'123456'`, but will be correctly matched if there are stubs for them both.

Note: you must ensure there is a stub to match each part of the byte sequence, **otherwise MockSerial will stop responding**. MockSerial does not support "regex" or "placeholder" matching.

## Advanced

MockSerial supports overriding stubs by `name` or `receive_bytes`. This can be useful if you want to define most of your stubs once, but override the `send_bytes` for one or two of them in specific tests.

```python
device.stub(
  receive_bytes=b'123',
  send_bytes=b'456'
)

...

device.stub(
  receive_bytes=b'123',
  send_bytes=b'789'
)

serial.write(b'123')
assert serial.read(3) == b'789'
```

Stubs can also return a dynamic response by passing a `send_fn` instead of `send_bytes`. The function should accept a single argument: the number of times the stub has been called, including the current call.

```python
device.stub(
  receive_bytes=b'123',
  send_fn=lambda n: bytes(str(n), encoding='utf-8') + b'23'
)

serial.write(b'123123')
assert serial.read(6) == b'123223'
```

## Debugging

MockSerial has lots of `DEBUG` logs so you can see what it's doing. It may also log a warning if it has trouble closing. This can be helpful if you're trying to debug how it's interacting with your code.

```python
import logging, sys

logging.basicConfig(
  stream=sys.stdout,
  level=logging.DEBUG,
  format="%(levelname)s - %(message)s"
)

...
```

This is a rough example of what the logs look like.

```
DEBUG - Attached to mock serial port.
DEBUG - Buffer read: b'123'.
DEBUG - Potential matches: [b'1234' => b'456', b'1235' => fn()].
DEBUG - Buffer read: b'12341235'.
DEBUG - Match stub: b'1234' => b'456'.
DEBUG - Buffer write: b'456'.
DEBUG - Match stub: b'1235' => fn().
DEBUG - Buffer write: b'123'.
DEBUG - Detaching mock serial port.
DEBUG - Buffer read: b'mockserialquit'.
DEBUG - Detached mock serial port.
DEBUG - Closing mock serial port.
DEBUG - Closed mock serial port.
```

As you can see, MockSerial sends itself a special control sequence when closing. This signals to the worker thread to detach from the mock serial port, which is (sometimes) necessary in order to close it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

See [LICENCE](LICENCE).
