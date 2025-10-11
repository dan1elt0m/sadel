from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, SQLModel, create_engine, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from sadel import Sadel


class Hero(Sadel, table=True):
    __tablename__ = "hero"
    _upsert_index_elements = {"id"}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    tmp_file = tmp_path / "database.db"
    temp_file_url = f"sqlite:///{tmp_file}"

    engine = create_engine(temp_file_url, echo=True, future=True)
    SQLModel.metadata.create_all(engine)
    return tmp_file


@pytest.mark.asyncio()
async def test_upsert(temp_db):
    sqlite_url_async = f"sqlite+aiosqlite:///{temp_db}"
    async_engine = create_async_engine(sqlite_url_async, echo=True, future=True)
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    async with AsyncSession(async_engine) as session:
        await Hero.upsert(hero_1, session)
        result = (await session.exec(select(Hero).where(Hero.name == "Deadpond"))).all()
        assert len(result) == 1
        assert result[0].name == "Deadpond"
        assert result[0].secret_name == "Dive Wilson"
        assert result[0].age is None
        assert result[0].id == 1
        assert isinstance(result[0].created_on, datetime)


@pytest.mark.asyncio()
async def test_batch_upsert(temp_db):
    sqlite_url_async = f"sqlite+aiosqlite:///{temp_db}"
    async_engine = create_async_engine(sqlite_url_async, echo=True, future=True)
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
    async with AsyncSession(async_engine) as session:
        await Hero.batch_upsert([hero_1, hero_2, hero_3], session)
        result = (
            await session.exec(
                select(Hero).where(
                    or_(
                        Hero.name == "Deadpond", Hero.name == "Spider-Boy", Hero.name == "Rusty-Man"
                    )
                )
            )
        ).all()
        assert len(result) == 3
        assert result[0].name == "Deadpond"
        assert result[1].name == "Spider-Boy"
        assert result[2].name == "Rusty-Man"


@pytest.mark.asyncio()
async def test_modified_on_upsert(temp_db):
    sqlite_url_async = f"sqlite+aiosqlite:///{temp_db}"
    async_engine = create_async_engine(sqlite_url_async, echo=True, future=True)
    hero_1 = Hero(id=1, name="Deadpond", secret_name="Dive Wilson")
    hero_1_update = Hero(id=1, name="Deadpond", secret_name="Dive Wilson", age=20)
    async with AsyncSession(async_engine) as session:
        await Hero.upsert(hero_1, session)
        await Hero.upsert(hero_1_update, session)
        [result] = (await session.exec(select(Hero).where(Hero.name == "Deadpond"))).all()

    assert isinstance(result.modified_on, datetime)
    assert result.age == 20


@pytest.mark.asyncio()
async def test_validate():
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        Hero(name="Deadpond", secret_name="Dive Wilson", age=datetime.now())


@pytest.mark.asyncio()
async def test_missing_upsert_identifier(temp_db):
    class Woops(Sadel, table=True):
        __tablename__ = "woops"

        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        secret_name: str
        age: Optional[int] = None

    sqlite_url_async = f"sqlite+aiosqlite:///{temp_db}"
    async_engine = create_async_engine(sqlite_url_async, echo=True, future=True)
    loser_1 = Woops(id=1, name="Deadpond", secret_name="Dive Wilson")
    with pytest.raises(ValueError, match="No upsert index elements specified for the model."):
        async with AsyncSession(async_engine) as session:
            await Woops.upsert(loser_1, session)


@pytest.mark.asyncio
async def test_async_metadata_create_all(tmp_path):
    db_file = tmp_path / "async.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", echo=False, future=True)

    class AsyncHero(Sadel, table=True):
        __tablename__ = "async_hero"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str

    # Proper async DDL creation
    async with engine.begin() as conn:
        await conn.run_sync(Sadel.metadata.create_all)

    # Verify table was created
    async with engine.connect() as conn:
        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='async_hero'"
        )
        rows = result.fetchall()
        assert any(r[0] == "async_hero" for r in rows), "async_hero table not created"