# -*- coding: utf-8 -*-

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base


@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture
def base_model():
    return declarative_base()


@pytest.fixture(scope="session")
def users_json():
    fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "users.json")
    with open(fpath) as f:
        return json.load(f)
