# pyright: reportUnknownVariableType=false
from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

import sqlalchemy as sa
from pydantic import ConfigDict
from pydantic.v1 import validate_model
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlmodel import Field, SQLModel


class Sadel(SQLModel):
    """Base class for SQL models."""

    model_config = ConfigDict(validate_assignment=True)  # type: ignore
    created_on: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"server_default": sa.func.now()},
        description=(
            "The date and time the record was created. "
            "Field is optional and not needed when instantiating a new record. "
            "It will be automatically set when the record is created in the database."
        ),
    )

    modified_on: datetime | None = Field(
        default=None,
        sa_type=sa.DateTime(timezone=True),  # pyright: ignore
        sa_column_kwargs={"onupdate": sa.func.now(), "server_default": sa.func.now()},
        description=(
            "The date and time the record was updated. "
            "Field is optional and not needed when instantiating a new record. "
            "It will be automatically set when the record is created in the database."
        ),
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Workaround to validate the model on init, which is not supported by SQLModel
        if hasattr(self, "__config__"):
            _, _, validation_error = validate_model(self.__class__, data)  # pyright: ignore
            if validation_error:
                raise validation_error

    # Specifies the set of index elements which represent the ON CONFLICT target
    _upsert_index_elements: ClassVar[set[str]] = set()

    # Specifies the set of fields to exclude from updating in the resulting
    # UPSERT statement
    _upsert_exclude_fields: ClassVar[set[str]] = set()

    # Common fields which we should exclude when updating.
    _default_upsert_exclude_fields: ClassVar[set[str]] = {"created_on"}

    @classmethod
    async def upsert(cls, item: Sadel, session: sa.orm.Session):
        """upserts a single item"""
        stmt = cls._get_upsert_statement(item)
        await session.exec(stmt)
        await session.commit()

    @classmethod
    async def batch_upsert(cls, items: list[Sadel], session: sa.orm.Session):
        """Batch upserts a list of items."""
        for item in items:
            stmt = cls._get_upsert_statement(item)
            await session.exec(stmt)
        await session.commit()

    @classmethod
    def _get_upsert_statement(cls, item: Sadel) -> Insert:
        """Returns an UPSERT statement for a single item."""
        if not cls._upsert_index_elements:
            raise ValueError("No upsert index elements specified for the model.")

        to_insert = item.model_dump()
        to_insert["created_on"] = (
            sa.func.now()
        )  # set manually, because on_conflict_do_update doesn't trigger default oninsert
        to_update = cls._get_record_to_update(to_insert)
        stmt = insert(cls).values(to_insert)
        return stmt.on_conflict_do_update(
            index_elements=cls._upsert_index_elements,
            set_=to_update,
        )

    @classmethod
    def _get_record_to_update(cls, record: dict[str, Any]) -> dict[str, Any]:
        """Returns a record to be upserted taking into account the excluded fields."""
        exclude_fields = cls._upsert_exclude_fields.copy()
        exclude_fields.update(cls._default_upsert_exclude_fields)

        to_update = record.copy()

        for field in exclude_fields:
            _ = to_update.pop(field, None)  # pyright: ignore

        to_update["modified_on"] = (
            sa.func.now()
        )  # set manually. on_conflict_do_update doesn't trigger onupdate

        return to_update  # type: ignore
