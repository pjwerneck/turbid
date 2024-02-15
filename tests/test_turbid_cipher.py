import random
import string
import sys

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from turbid import InvalidID
from turbid import TurbIDCipher

alphabet_alnum = string.digits + string.ascii_letters
alphabet_hex = "0123456789abcdef"

py_int_ids = st.integers(min_value=0, max_value=sys.maxsize)
py_lengths = st.integers(min_value=20, max_value=32)
py_key_lengths = st.just(128) | st.just(192) | st.just(256)
py_alphabets = st.just(alphabet_alnum) | st.just(alphabet_hex)
py_invalid_alphabets = (
    st.text(min_size=1, max_size=1)
    | st.text(min_size=96, max_size=97)
    | st.text(min_size=97, max_size=98)
    | st.text(min_size=98, max_size=99)
)
py_keys = st.text(min_size=128, max_size=128)

# two different keys
py_key_pairs = st.tuples(py_keys, py_keys)


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_encrypt_and_decrypt(int_id, length, alphabet, key_length, key):
    cipher = TurbIDCipher(
        key=key,
        tweak="obscure",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )
    str_id = cipher.encrypt(int_id)

    assert isinstance(str_id, str)
    assert len(str_id) == length

    decoded_int_id = cipher.decrypt(str_id)

    assert decoded_int_id == int_id


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_tampered_length_fails(int_id, length, alphabet, key_length, key):
    cipher = TurbIDCipher(
        key=key,
        tweak="murky",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )
    str_id = cipher.encrypt(int_id)

    tampered_str_id = str_id[:-1]

    with pytest.raises(InvalidID) as exc:
        cipher.decrypt(tampered_str_id)

    assert str(exc.value) == "ID length does not match the expected length."


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_tampered_id_fails(int_id, length, alphabet, key_length, key):
    cipher = TurbIDCipher(
        key=key,
        tweak="fuzzy",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )
    str_id = cipher.encrypt(int_id)
    tampered_str_id = str_id[:4] + str_id[4:][::-1]

    with pytest.raises(InvalidID) as exc:
        cipher.decrypt(tampered_str_id)

    assert str(exc.value).startswith("ID corrupted or invalid.")


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_same_key_different_tweak_fails(int_id, length, alphabet, key_length, key):
    cipher1 = TurbIDCipher(
        key=key, length=length, tweak="cloudy", alphabet=alphabet, key_length=key_length
    )
    cipher2 = TurbIDCipher(
        key=key, length=length, tweak="hazy", alphabet=alphabet, key_length=key_length
    )

    str_id1 = cipher1.encrypt(int_id)
    str_id2 = cipher2.encrypt(int_id)

    assert str_id1 != str_id2

    with pytest.raises(InvalidID) as exc1:
        cipher1.decrypt(str_id2)

    with pytest.raises(InvalidID) as exc2:
        cipher2.decrypt(str_id1)

    assert str(exc1.value) == str(exc2.value)
    assert str(exc1.value).startswith("ID corrupted or invalid.")


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys, py_keys)
def test_same_tweak_different_key_fails(
    int_id, length, alphabet, key_length, key1, key2
):
    assume(key1 != key2)

    cipher1 = TurbIDCipher(
        key=key1, length=length, tweak="misty", alphabet=alphabet, key_length=key_length
    )
    cipher2 = TurbIDCipher(
        key=key2, length=length, tweak="misty", alphabet=alphabet, key_length=key_length
    )

    str_id1 = cipher1.encrypt(int_id)
    str_id2 = cipher2.encrypt(int_id)

    assert str_id1 != str_id2

    with pytest.raises(InvalidID) as exc1:
        cipher1.decrypt(str_id2)

    with pytest.raises(InvalidID) as exc2:
        cipher2.decrypt(str_id1)

    assert str(exc1.value) == str(exc2.value)
    assert str(exc1.value).startswith("ID corrupted or invalid.")


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_repeated_encryption(int_id, length, alphabet, key_length, key):
    cipher = TurbIDCipher(
        key=key,
        tweak="repeated",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )
    str_id1 = cipher.encrypt(int_id)
    str_id2 = cipher.encrypt(int_id)
    assert str_id1 == str_id2


@given(py_int_ids, py_lengths, py_alphabets, py_key_lengths, py_keys)
def test_different_instances_same_encryption(int_id, length, alphabet, key_length, key):
    cipher1 = TurbIDCipher(
        key=key,
        tweak="same",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )
    cipher2 = TurbIDCipher(
        key=key,
        tweak="same",
        length=length,
        alphabet=alphabet,
        key_length=key_length,
    )

    str_id1 = cipher1.encrypt(int_id)
    str_id2 = cipher2.encrypt(int_id)
    assert str_id1 == str_id2


@given(py_lengths, py_alphabets, st.integers(min_value=1, max_value=256), py_keys)
def test_invalid_key_length(length, alphabet, key_length, key):
    if key_length in (128, 192, 256):
        return
    with pytest.raises(ValueError):
        TurbIDCipher(
            key=key,
            tweak="invalid_key_length",
            length=length,
            alphabet=alphabet,
            key_length=key_length,
        )


@given(py_lengths, py_invalid_alphabets, py_key_lengths, py_keys)
def test_invalid_alphabet(length, alphabet, key_length, key):
    with pytest.raises(ValueError):
        TurbIDCipher(
            key=key,
            tweak="invalid_alphabet",
            length=length,
            alphabet=alphabet,
            key_length=key_length,
        )


# with short ids and alphabets that have many digits and few letters, decrypting
# a random string can result in an all digits string. The cipher uses a check
# digit to detect that as an invalid ID. This test tries to find such a random
# string and confirm if the check digit added during encryption catches the
# invalid value.
@settings(deadline=500)
@given(st.integers(5, 9), st.random_module())
def test_check_digit_catches_invalid_id(length, random_seeder):
    key = "any key works for this test"
    alphabet = "0123456789abcdef"
    cipher = TurbIDCipher(
        key=key,
        tweak="misty",
        length=length,
        alphabet=alphabet,
        key_length=128,
    )

    # first, lets find a random string that when decrypted will result in an
    # all digits string, but not match the expected value
    while True:
        str_id = "".join(random.choice(alphabet) for _ in range(length))
        decrypted_value = cipher._ff3.decrypt(str_id)
        if (
            decrypted_value.isdigit()
            and cipher.encrypt(int(str(decrypted_value[:-1]))) != str_id
        ):
            break

    with pytest.raises(InvalidID) as exc:
        cipher.decrypt(str_id)

    assert str(exc.value) == "ID corrupted or invalid."
