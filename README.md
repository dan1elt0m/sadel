[![CodeQL](https://github.com/dan1elt0m/sadel/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/dan1elt0m/sadel/actions/workflows/codeql-analysis.yml)
[![Dependabot Updates](https://github.com/dan1elt0m/sadel/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/dan1elt0m/sadel/actions/workflows/dependabot/dependabot-updates)
[![test](https://github.com/dan1elt0m/sadel/actions/workflows/test.yml/badge.svg)](https://github.com/dan1elt0m/sadel/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/dan1elt0m/sadel/graph/badge.svg?token=NECZRE656C)](https://codecov.io/github/dan1elt0m/sadel)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fdan1elt0m%2Fsadel%2Fmain%2Fpyproject.toml)


# Sadel 

Sadel is a helper class for upserting records with [SQLModel](https://sqlmodel.tiangolo.com/). 
Sadel combines SQLAlchemy(sa) and SQLmodel(del), and in Danish, 'sadel' means 'saddle,' symbolizing taking over the burden of managing upserts."

### Installation
```bash
pip install sadel
```

### Features 
- (Batch) upsert records with a single line of code.
- For auditing, automatically adds and manages `created_on` and `modified_on` columns to your table 
- Validates your data before upserting using Pydantic validate_model method (not supported in SQLModel)
- Asyncio
- Compatible with Alembic

#### Example upsert
```python
from sadel import Sadel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, create_engine, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

class Hero(Sadel, table=True):
    __tablename__ = "hero" 
    _upsert_index_elements = {"id"}

    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None
    
sqlite_url = f"sqlite+aiosqlite::///database.db" 
engine = create_engine(sqlite_url, echo=True, future=True)

async_engine = create_async_engine(sqlite_url_async, echo=True, future=True)
hero = Hero(name="Deadpond", secret_name="Dive Wilson")

async with AsyncSession(async_engine) as session:
    # Upsert the record
    await Hero.upsert(hero, session)
    
    # Fetch the upserted record
    result = (
        (await session.exec(select(Hero).where(Hero.name == "Deadpond")))
        .all()
    )

    print(result)
```
Output:
```text
[Hero(id=1, name='Deadpond', secret_name='Dive Wilson', created_on=datetime.datetime(2024, 8, 1, 19, 39, 7), modified_on=None)]
```
### Example batch upsert
```python
hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)

async with AsyncSession(async_engine) as session:
    await Hero.batch_upsert([hero_1, hero_2, hero_3], session)
    result = (
        (
            await session.exec(
               select(Hero).where(or_(Hero.name == "Deadpond",  Hero.name == "Spider-Boy", Hero.name == "Rusty-Man"))
            )
        )
        .all()
    )
    print(result)
```
Output:
```text
[Hero(id=1, name='Deadpond', secret_name='Dive Wilson', created_on=datetime.datetime(2024, 8, 1, 19, 39, 7), modified_on=None), 
Hero(id=2, name='Spider-Boy", secret_name='Pedro Parqueador', created_on=datetime.datetime(2024, 8, 1, 19, 39, 7), modified_on=None),
Hero(id=3, name='Rusty-Man', secret_name='Tommy Sharp', created_on=datetime.datetime(2024, 8, 1, 19, 39, 7), modified_on=None)]
```


### Contributing
- Fork the repository
- Create a new branch
- Make your changes
- Raise a PR

### Development
```bash
# install dependencies
rye sync 
# run tests, linting, formatting, and type checking, 
rye run all
```

### License
This project is licensed under the terms of the [MIT License](LICENSE)
