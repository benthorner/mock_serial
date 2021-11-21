class Stub:
    def __init__(
        self,
        *,
        receive_bytes,
        send_bytes=None,
        send_fn=None
    ):
        self.__receive_bytes = receive_bytes
        self.__send_bytes = send_bytes
        self.__calls = 0

        if (send_bytes is None) == (send_fn is None):
            raise TypeError('Specify either send_bytes or send_fn.')

        if send_bytes is not None:
            self.__send_fn = lambda *_: send_bytes
        else:
            self.__send_fn = send_fn

    def __lt__(self, other):
        return len(self.receive_bytes) < len(other.receive_bytes)

    @property
    def receive_bytes(self):
        return self.__receive_bytes

    def call(self):
        self.__calls += 1
        return self.__send_fn(self.__calls)

    @property
    def calls(self):
        return self.__calls

    @property
    def called(self):
        return self.calls > 0

    def __repr__(self):
        if self.__send_bytes:
            return f"{self.receive_bytes} => {self.__send_bytes}"
        else:
            return f"{self.receive_bytes} => fn()"
