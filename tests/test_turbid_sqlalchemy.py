import secrets

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from turbid.ext.sqlalchemy import PrefixedTurbIDType
from turbid.ext.sqlalchemy import TurbIDProxy
from turbid.ext.sqlalchemy import TurbIDType

KEY = secrets.token_hex()


class BaseTestCase:
    @pytest.fixture
    def session(self, base_model, user_model, engine, users_json):
        base_model.metadata.create_all(engine)
        session_ = sessionmaker(bind=engine)

        with session_() as inner_session:
            for raw in users_json:
                obj = user_model(
                    name=raw["name"],
                )
                inner_session.add(obj)

            inner_session.commit()

        yield session_()

        base_model.metadata.drop_all(engine)


class TestPrefixedTurbIDType(BaseTestCase):
    @pytest.fixture
    def user_model(self, base_model):
        class User(base_model):
            __tablename__ = "user"

            user_id = sa.Column(
                PrefixedTurbIDType(key=KEY, prefix="us_"),
                autoincrement=True,
                primary_key=True,
            )
            name = sa.Column(sa.String(200))

        return User

    def test_int_id_is_saved_to_db(self, session, user_model):
        user = session.execute(select(user_model)).scalars().first()

        assert isinstance(user.user_id, str)
        assert user.user_id.startswith("us_")
        assert len(user.user_id) == 27

        int_id = user_model.user_id.type._turbid.decrypt(user.user_id[-24:])

        raw_user = session.execute(text(f"SELECT * FROM user WHERE user_id = {int_id}")).first()

        assert raw_user.name == user.name

    def test_query_by_str_id(self, session, user_model):
        int_id = 1
        raw_user = session.execute(text(f"SELECT * FROM user WHERE user_id = {int_id}")).first()

        str_id = user_model.user_id.type._prefix + user_model.user_id.type._turbid.encrypt(int_id)

        assert str_id.startswith("us_")

        user = (
            session.execute(select(user_model).where(user_model.user_id == str_id))
            .scalars()
            .first()
        )

        assert user.name == raw_user.name
        assert user.user_id == str_id


class TestTurbIDType(BaseTestCase):
    @pytest.fixture
    def user_model(self, base_model):
        class User(base_model):
            __tablename__ = "user"

            user_id = sa.Column(
                TurbIDType(key=KEY, tweak="user"),
                primary_key=True,
                autoincrement=True,
            )
            name = sa.Column(sa.String(200))

        return User

    def test_int_id_is_saved_to_db(self, session, user_model):
        user = session.execute(select(user_model)).scalars().first()

        assert isinstance(user.user_id, str)
        assert len(user.user_id) == 24

        int_id = user_model.user_id.type._turbid.decrypt(user.user_id)

        raw_user = session.execute(text(f"SELECT * FROM user WHERE user_id = {int_id}")).first()

        assert raw_user.name == user.name

    def test_query_by_str_id(self, session, user_model):
        int_id = 1
        raw_user = session.execute(text(f"SELECT * FROM user WHERE user_id = {int_id}")).first()

        str_id = user_model.user_id.type._turbid.encrypt(int_id)

        user = (
            session.execute(select(user_model).where(user_model.user_id == str_id))
            .scalars()
            .first()
        )

        assert user.name == raw_user.name
        assert user.user_id == str_id


class TestTurbIDProxy(BaseTestCase):
    @pytest.fixture
    def user_model(self, base_model):
        class User(base_model):
            __tablename__ = "user"

            _id = sa.Column(
                sa.Integer,
                primary_key=True,
                autoincrement=True,
            )
            user_id = TurbIDProxy(_id, key=KEY, tweak="user")
            name = sa.Column(sa.String(200))

        return User

    def test_int_id_is_saved_to_db(self, session, user_model):
        user = session.execute(select(user_model)).scalars().first()

        assert isinstance(user.user_id, str)
        assert len(user.user_id) == 24

        int_id = user_model.user_id._turbid.decrypt(user.user_id)

        raw_user = session.execute(text(f"SELECT * FROM user WHERE _id = {int_id}")).first()

        assert raw_user.name == user.name

    def test_query_by_str_id(self, session, user_model):
        int_id = 1
        raw_user = session.execute(text(f"SELECT * FROM user WHERE _id = {int_id}")).first()

        str_id = user_model.user_id._turbid.encrypt(int_id)

        user = (
            session.execute(select(user_model).where(user_model.user_id == str_id))
            .scalars()
            .first()
        )

        assert user.name == raw_user.name
        assert user.user_id == str_id

    def test_query_order_by(self, session, user_model):
        # Test ordering by encrypted ID
        users = session.execute(select(user_model).order_by(user_model._id.desc())).scalars().all()

        # Order should be preserved when accessing through proxy
        encrypted_ids = [u.user_id for u in users]
        assert encrypted_ids == [user_model.user_id._turbid.encrypt(u._id) for u in users]

    def test_proxy_comparison(self, session, user_model):
        user = session.execute(select(user_model)).scalars().first()
        str_id = user.user_id

        # Test direct comparison
        assert user.user_id == str_id
        assert user.user_id != "invalid_id"
        assert user.user_id != user_model.user_id._turbid.encrypt(999)
