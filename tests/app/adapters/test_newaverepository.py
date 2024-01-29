import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from tests.mocks.mock_open import mock_open
from tests.mocks.arquivos.newave.arquivos import (
    MockArquivos,
)
from tests.mocks.arquivos.newave.dger import MockDger
from tests.mocks.arquivos.newave.confhd import MockConfhd
from tests.mocks.arquivos.newave.eafpast import MockEafpast
from tests.mocks.arquivos.newave.adterm import MockAdterm
from tests.mocks.arquivos.newave.term import MockTerm
from tests.mocks.arquivos.newave.pmo import MockPMO
from inewave.newave.arquivos import Arquivos
from inewave.newave.dger import Dger
from inewave.newave.confhd import Confhd
from inewave.newave.hidr import Hidr
from inewave.newave.eafpast import Eafpast
from inewave.newave.adterm import Adterm
from inewave.newave.term import Term
from inewave.newave.pmo import Pmo
from app.adapters.newaverepository import factory


DIR_TESTE = "./tests/mocks/arquivos/newave/"


@pytest.mark.asyncio
async def test_arquivos_newave(mocker):
    m: MagicMock = mock_open(read_data="arquivos.py")
    with patch("builtins.open", m):
        repo = factory("FS", DIR_TESTE)
    m: MagicMock = mock_open(read_data="".join(MockArquivos))
    with patch("builtins.open", m):
        arq = repo.arquivos
    assert isinstance(arq, Arquivos)
    assert arq.adterm == "adterm.py"
    assert arq.term == "term.py"
    assert arq.pmo == "pmo.py"

    m: MagicMock = mock_open(read_data="".join(MockDger))
    with patch("builtins.open", m):
        arq = await repo.get_dger()
    assert isinstance(arq, Dger)
    assert arq.agregacao_simulacao_final == 1

    m: MagicMock = mock_open(read_data="".join(MockDger))
    with patch("builtins.open", m):
        arq = await repo.get_dger()
        repo.set_dger(arq)

    m: MagicMock = mock_open(read_data="".join(MockConfhd))
    with patch("builtins.open", m):
        arq = repo.get_confhd()
    assert isinstance(arq, Confhd)
    assert isinstance(arq.usinas, pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockConfhd))
    with patch("builtins.open", m):
        arq = repo.get_confhd()
        repo.set_confhd(arq)

    arq = repo.get_hidr()
    assert isinstance(arq, Hidr)
    assert isinstance(arq.cadastro, pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockEafpast))
    with patch("builtins.open", m):
        arq = repo.get_eafpast()
    assert isinstance(arq, Eafpast)
    assert isinstance(arq.tendencia, pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockAdterm))
    with patch("builtins.open", m):
        arq = repo.get_adterm()
    assert isinstance(arq, Adterm)
    assert isinstance(arq.despachos, pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockTerm))
    with patch("builtins.open", m):
        arq = repo.get_term()
    assert isinstance(arq, Term)
    assert isinstance(arq.usinas, pd.DataFrame)

    m: MagicMock = mock_open(read_data="".join(MockPMO))
    with patch("builtins.open", m):
        arq = repo.get_pmo()
    assert isinstance(arq, Pmo)
    assert isinstance(arq.custo_operacao_series_simuladas, pd.DataFrame)
