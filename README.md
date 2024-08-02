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

> [!WARNING] TurbID is not intended for protecting sensitive data 
> 
> TurbID is designed to obfuscate integer IDs in a reversible and repeatable
> manner that is not easily decoded. It is not suitable for encrypting sensitive
> data, such as passwords, credit card numbers, or personal information. Use
> standard, secure encryption methods for those use cases.


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

## Usage

TBD

## License

TurbID is licensed under the MIT License. See the [LICENSE](LICENSE) file for
details.

