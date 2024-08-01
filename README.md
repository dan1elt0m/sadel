# Sadel 

Sadel simplifies upserting records to your database 
by extending [SQLModel](https://sqlmodel.tiangolo.com/). It adds a single line of code to upsert records to your database. 
It also supports batch upserting records. In addition, it automatically adds and manages `created_on` and `modified_on` 
columns to your table for auditing purposes and validates the record before upserting. 


### Features 
- (Batch) upsert records with a single line of code.
- Asyncio support
- For auditing, automatically adds and manages `created_on` and `modified_on` columns to your table 
- Validates your data before upserting using Pydantic validate_model method (not supported in SQLModel)

#### Example upsert
```python
from sadel import Sadel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Field, create_engine, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

class Hero(Sadel, table=True):
    __tablename__ = "hero"  # type: ignore
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

### Installation
```bash
pip install sadel
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