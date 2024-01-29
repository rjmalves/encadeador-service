from tests.mocks.mock_open import mock_open
import pytest
from unittest.mock import MagicMock, patch
from tests.mocks.arquivos.decomp.dadger import MockDadger
from tests.mocks.arquivos.decomp.dadgnl import MockDadgnl
from tests.mocks.arquivos.decomp.arquivos import (
    MockArquivos,
)
from idecomp.decomp.arquivos import Arquivos
from idecomp.decomp.dadger import Dadger
from idecomp.decomp.dadgnl import Dadgnl
from idecomp.decomp.hidr import Hidr
from idecomp.decomp.inviabunic import InviabUnic
from idecomp.decomp.relato import Relato
import pandas as pd
from app.adapters.decomprepository import factory


DIR_TESTE = "./tests/mocks/arquivos/decomp/"


@pytest.mark.asyncio
async def test_arquivos_decomp(mocker):
    m: MagicMock = mock_open(read_data="rv0")
    with patch("builtins.open", m):
        repo = factory("FS", DIR_TESTE)
    m: MagicMock = mock_open(read_data="".join(MockArquivos))
    with patch("builtins.open", m):
        arq = repo.arquivos
    assert isinstance(arq, Arquivos)
    assert arq.dadger == "dadger.py"

    m: MagicMock = mock_open(read_data="".join(MockDadger))
    with patch("builtins.open", m):
        arq = await repo.get_dadger()
        assert isinstance(arq, Dadger)
        assert isinstance(arq.uh(df=True), pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockDadger))
    with patch("builtins.open", m):
        arq = await repo.get_dadger()
        repo.set_dadger(arq)

    m: MagicMock = mock_open(read_data="".join(MockDadgnl))
    with patch("builtins.open", m):
        arq = await repo.get_dadgnl()
        assert isinstance(arq, Dadgnl)
        assert isinstance(arq.gl(df=True), pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockDadgnl))
    with patch("builtins.open", m):
        arq = await repo.get_dadgnl()
        repo.set_dadgnl(arq)

    arq = repo.get_hidr()
    assert isinstance(arq, Hidr)
    assert isinstance(arq.cadastro, pd.DataFrame)

    arq = repo.get_inviabunic()
    assert isinstance(arq, InviabUnic)

    arq = repo.get_relato()
    assert isinstance(arq, Relato)
    assert isinstance(arq.volume_util_reservatorios, pd.DataFrame)
