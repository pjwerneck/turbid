import json
import string
import sys
from itertools import product

from hypothesis import strategies as st

from turbid import TurbIDCipher

alphabets = [string.digits + string.ascii_letters, "0123456789abcdef"]
lengths = list(range(20, 33))
key_lengths = [128, 192, 256]
keys = [
    "e423ae07e96c7e87f59d4fcfc80b22b72f0dcc5aa98f151b617b5605265ba2bb",
    "c8352defca90299e2d926cb5f233245a3511219e5e7661374bf79ed96f2b6422",
]
tweaks = ["f5ed4be0", "2ef99918"]

py_integers = st.integers(min_value=0, max_value=sys.maxsize)

ints = [py_integers.example() for _ in range(100)]


ciphers = []

for alphabet, length, key_length, key, tweak in product(
    alphabets, lengths, key_lengths, keys, tweaks
):
    ids = []
    f = TurbIDCipher(
        key=key, tweak=tweak, length=length, alphabet=alphabet, key_length=key_length
    )
    for int_id in ints:
        str_id = f.encrypt(int_id)
        assert f.decrypt(str_id) == int_id

        ids.append((int_id, str_id))

    ciphers.append((alphabet, length, key_length, key, tweak, ids))


with open("tests/stable_values.json", "w") as f:
    json.dump(ciphers, f, indent=2, default=str)
