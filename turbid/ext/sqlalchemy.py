import string

from sqlalchemy.types import Integer
from sqlalchemy.types import TypeDecorator

from turbid.turbid import InvalidID
from turbid.turbid import TurbIDCipher

alphabet_alnum = string.digits + string.ascii_letters


class TurbIDType(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(
        self,
        *args,
        key: str,
        tweak: str,
        length: int = 24,
        alphabet: str = alphabet_alnum,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._turbid = TurbIDCipher(
            key=key, tweak=tweak, length=length, alphabet=alphabet
        )

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, int):
            return value

        return self._turbid.decrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return self._turbid.encrypt(value)


class PrefixedTurbIDType(TypeDecorator):
    impl = Integer
    cache_ok = True

    def __init__(
        self,
        *args,
        key: str,
        prefix: str,
        length: int = 24,
        alphabet: str = alphabet_alnum,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not prefix:
            raise ValueError(
                "You must provide a non-empty prefix string."
                "If you don't want to use a prefix, use TurbIDType instead."
            )

        self._turbid = TurbIDCipher(
            key=key, tweak=prefix, length=length, alphabet=alphabet
        )

        self._prefix = prefix

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, int):
            return value

        if self._prefix != value[: -self._turbid.length]:
            raise InvalidID("Invalid ID prefix")

        value = value[-self._turbid.length :]

        return self._turbid.decrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return f"{self._prefix}{self._turbid.encrypt(value)}"


class TurbIDProxy:
    def __init__(self, column, key, tweak, length=24, alphabet=alphabet_alnum):
        self._column = column
        self._turbid = TurbIDCipher(
            key=key, tweak=tweak, length=length, alphabet=alphabet
        )

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        return self._turbid.encrypt(getattr(obj, self._column.name))

    def __set__(self, obj, value):
        setattr(obj, self._column.name, self._turbid.decrypt(value))

    def __eq__(self, other):
        return self._column == self._turbid.decrypt(other)
