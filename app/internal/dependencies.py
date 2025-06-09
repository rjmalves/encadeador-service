from typing import Type
from fastapi import HTTPException
from app.internal.settings import Settings
from app.adapters.uriparserrepository import AbstractURIParsingRepository
from app.adapters.uriparserrepository import factory as parser_factory


async def uriParser() -> Type[AbstractURIParsingRepository]:
    s = parser_factory(Settings.uri_pattern)
    if s is None:
        raise HTTPException(
            500, f"URI pattern {Settings.uri_pattern} not supported"
        )
    return s
