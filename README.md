# TurbID

[![Build Status](https://github.com/pjwerneck/turbid/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/pjwerneck/turbid/actions/workflows/pytest.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Overview

TurbID is a Python library that provides ID obfuscation and encryption for
sequential integer primary keys. With TurbID, your database can store clear,
sequential integer primary keys, while your public API and the rest of the world
sees opaque and seemingly random long-form string IDs. This approach avoids the
database performance downsides of long random IDs and sidesteps the privacy and
security risks of clear integer IDs.

Unlike other libraries that merely encode integers with a randomized alphabet,
TurbID uses format-preserving encryption for additional security.

TurbID currently supports SQLAlchemy with an optional extension that provides a
custom column type, but it can be extended to work with other ORMs or
frameworks.

> [!WARNING]
>
> TurbID is not intended for protecting sensitive numeric data, such as credit card numbers or PINs. For these use cases, please use standard, secure encryption methods.

## Installation

TurbID is compatible with Python 3.8+ and available on PyPI. Install it with
pip, or your package manager of choice:

```bash
pip install turbid
```

But you probably want to install with the optional SQLAlchemy extension:

```bash
pip install turbid[sqlalchemy]
```

## SQLAlchemy Usage

With SQLAlchemy, just replace your column's `Integer` column type with `TurbIDType`:

```python

class User(Base):
    __tablename__ = "user"

    user_id = sa.Column(TurbIDType(key=KEY, tweak="user"), primary_key=True)
    name = sa.Column(sa.String(200))

```

If you have foreign keys, do the same for the `ForeignKey` columns, but remember
to use the same `key` and `tweak` values as the referenced column:

```python
class Post(Base):
    __tablename__ = "post"

    post_id = sa.Column(TurbIDType(key=KEY, tweak="post"), primary_key=True)
    user_id = sa.Column(TurbIDType(key=KEY, tweak="user"), sa.ForeignKey("user.user_id"))
    title = sa.Column(sa.String(200))

```

You can use your columns as usual, in joins, filters, data retrieval, etc. In
queries or when updating data you can use either the original integer ID or the
obfuscated string ID, but retrievals will always return the obfuscated string
ID.

## TurbIDCipher Usage

If you don't use SQLAlchemy or you want to encrypt/decrypt IDs at another layer
of your application, like when serializing objects for responses, you can use
the `TurbIDCipher` class directly.

```python
>>> from turbid import TurbIDCipher
>>> import secrets
>>>
>>> key = secrets.token_hex()
>>> tweak = "my_table_name"
>>> obscure_id = TurbIDCipher(key, tweak=tweak)
>>>
>>> # Encrypt an integer ID
>>> encrypted_id = obscure_id.encrypt(12345)
>>> print(f"Encrypted ID: {encrypted_id}")
Encrypted ID: VTxLWjgdCWGjLSIiZtCQCMvu
>>>
>>> # Decrypt the ID back to the original integer
>>> original_id = obscure_id.decrypt(encrypted_id)
>>> print(f"Original ID: {original_id}")
Original ID: 12345
```

## Parameters

The required parameters are:

- **key**:
  - A string that will be hashed to generate the encryption key for the AES cipher.
  - Never expose the key in version control or share it publicly.
  - You can generate a random key suitable for this purpose using the
    `secrets.token_hex` function.
- **tweak**:
  - A string that will be hashed to generate the 7-byte tweak value for FF3-1
    encryption.
  - This parameter is not a secret and is used to differentiate the encrypted
    values of different instances using the same secret `key`.
  - The value **must** be unique per table to avoid ID collisions.

SQLAlchemy extension parameters:

- **prefix**:
  - An optional string that will be prepended to the encrypted ID. This is also
    used as the `tweak` value if an explicit one isn't provided.
  - If you don't want a prefix on your encrypted IDs, you must provide a `tweak` for each table.
  - You can provide both a `tweak` and a `prefix`. In this case, the `prefix`
    will be merely cosmetic and the `tweak` will be used to differentiate the
    encrypted values.

Optional parameters with tested defaults:

- **length=`24`**:
  - The length of the encrypted ID. The default is 24 characters, but the
    minimum and maximum lengths are determined by the alphabet length and the
    maximum value you want to encrypt.
  - A `ValueError` will be raised if the alphabet length is incompatible with
    the specified length.
- **alphabet=`string.digits + string.ascii_letters`**:
  - The alphabet used to encode the encrypted ID. The default is all 10 digits
    and all 52 lowercase and uppercase letters.
  - You can use a different alphabet, as long as it contains all 10 digits and
    no repeated characters.
  - The alphabet length must be compatible with the specified `length`.
- **key_length=`128`**:
  - The length of the AES key in bits. The default is 128 bits, which is the
    recommended key length for AES encryption.
  - Note this refers to the length of the hashed key generated internally, not
    the length of the string you provide as the key material.

## Compatibility and Testing

TurbID is tested with the following values:

- input ids: sampled from `0` to `2^63-1`
- `length`: `20` to `32`, inclusive
- `alphabet`: `string.digits + string.ascii_letters` and `"0123456789abcdef"`
- `key_length`: `128`, `194`, and `256`

It probably works with other values, but you should review the limitations of
the FF3-1 algorithm and the [ff3](https://github.com/mysto/python-fpe) library
and implement tests to ensure it works as expected.

## License

TurbID is licensed under the MIT License. See the [LICENSE](LICENSE) file for
details.
