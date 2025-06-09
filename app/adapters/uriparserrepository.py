from abc import ABC, abstractmethod
from typing import Dict, Union, Type

import base62  # type: ignore

from app.internal.httpresponse import HTTPResponse


class AbstractURIParsingRepository(ABC):
    """ """

    @classmethod
    @abstractmethod
    def parse(cls, uri: str) -> Union[str, HTTPResponse]:
        pass


class Base62URIParsingRepository(AbstractURIParsingRepository):
    @classmethod
    def parse(cls, uri: str) -> Union[str, HTTPResponse]:
        try:
            path = base62.decodebytes(uri).decode("utf-8")
            return path
        except Exception:
            return HTTPResponse(code=400, detail="given URI is not in base62")


SUPPORTED_FORMATS: Dict[str, Type[AbstractURIParsingRepository]] = {
    "BASE62": Base62URIParsingRepository
}
DEFAULT = Base62URIParsingRepository


def factory(kind: str) -> Type[AbstractURIParsingRepository]:
    return SUPPORTED_FORMATS.get(kind, DEFAULT)
