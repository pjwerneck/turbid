import json
from pathlib import Path

from turbid import TurbIDCipher

HERE = Path(__file__).parent

# this test uses pregenerated values to ensure that the encryption and
# decryption functions are stable and consistent accross versions and dependency
# updates. Do not change or regenerate the values in stable_values.json, only
# add more to them.


def test_stable_values():
    with open(HERE / "stable_values.json") as f:
        data = json.load(f)

    for alphabet, length, key_length, key, tweak, ids in data:
        f = TurbIDCipher(
            key=key,
            tweak=tweak,
            length=length,
            alphabet=alphabet,
            key_length=key_length,
        )
        for int_id, str_id in ids:
            assert f.encrypt(int_id) == str_id
            assert f.decrypt(str_id) == int_id
