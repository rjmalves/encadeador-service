from app.adapters.uriparserrepository import factory
from app.internal.httpresponse import HTTPResponse


def test_parse_base62_success():
    parser = factory("BASE62")
    uri = "4cWOpmdvAEtmXmH"
    res = "/home/teste"
    assert parser.parse(uri) == res


def test_parse_base62_error():
    parser = factory("BASE62")
    uri = "/home/teste??+="
    assert isinstance(parser.parse(uri), HTTPResponse)
