import logging
import os
import pty
from threading import Thread

from .stub import Stub

logger = logging.getLogger(__name__)


class MockSerial:
    QUIT_SIGNAL = b'mockserialquit'

    def __init__(self):
        self.__master, self._slave = pty.openpty()
        self.__stubs = {}
        self.__thread = Thread(target=self.__receive, daemon=True)

    @property
    def port(self):
        return os.ttyname(self._slave)

    @property
    def stubs(self):
        return self.__stubs

    def stub(self, *, name=None, **kwargs):
        new_stub = Stub(**kwargs)
        self.__stubs[name or new_stub.receive_bytes] = new_stub
        return new_stub

    def __match(self, buffer):
        potential_matches = [
            stub for stub in self.stubs.values()
            if stub.receive_bytes.startswith(buffer)
        ]

        if len(potential_matches) > 1:
            logger.debug(
                f"Potential matches: {sorted(potential_matches)}."
            )

            return None

        matches = sorted(
            (
                stub for stub in self.stubs.values()
                if buffer.startswith(stub.receive_bytes)
            ),
            reverse=True
        )

        return matches[0] if matches else None

    def __reply(self, buffer):
        if not buffer:
            return buffer

        stub = self.__match(buffer)

        if not stub:
            return buffer

        send_bytes = stub.call()
        logger.debug(f"Match stub: {stub}.")

        os.write(self.__master, send_bytes)
        logger.debug(f"Buffer write: {send_bytes}.")

        buffer = buffer[len(stub.receive_bytes):]
        return self.__reply(buffer)

    def __receive(self):
        buffer = bytes()

        while self.QUIT_SIGNAL not in buffer:
            # read a good chunk of data each time
            buffer += os.read(self.__master, 32)
            logger.debug(f"Buffer read: {buffer}.")
            buffer = self.__reply(buffer)

        logger.debug("Detached mock serial port.")

    def open(self):
        self.__thread.start()
        logger.debug("Attached to mock serial port.")

    def close(self):
        logger.debug("Detaching mock serial port.")

        # stop the thread trying to read from it
        os.write(self._slave, self.QUIT_SIGNAL)
        self.__thread.join(timeout=1)

        if self.__thread.is_alive():
            logger.warning("Unable to detach mock serial port.")

        tmp_thread = Thread(
            # may hang if thread still reading from it
            target=lambda: os.close(self.__master),
            daemon=True
        )

        logger.debug("Closing mock serial port.")
        tmp_thread.start()
        tmp_thread.join(timeout=1)

        if tmp_thread.is_alive():
            logger.warning("Unable to close mock serial port.")
            return

        os.close(self._slave)
        logger.debug("Closed mock serial port.")
