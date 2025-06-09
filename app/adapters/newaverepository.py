from abc import ABC, abstractmethod
import pathlib
from os.path import join
from os import curdir
from typing import Dict, Optional, Union, Type
from inewave.newave.caso import Caso
from inewave.newave.arquivos import Arquivos
from inewave.newave.dger import Dger
from inewave.newave.hidr import Hidr
from inewave.newave.confhd import Confhd
from inewave.newave.eafpast import Eafpast
from inewave.newave.adterm import Adterm
from inewave.newave.term import Term
from inewave.newave.pmo import Pmo

from app.internal.settings import Settings
from app.utils.encoding import converte_codificacao
from app.utils.log import Log
from app.internal.httpresponse import HTTPResponse

from tests.mocks.arquivos.newave.arquivos import MockArquivos
from tests.mocks.arquivos.newave.dger import MockDger
from tests.mocks.arquivos.newave.confhd import MockConfhd
from io import StringIO


class AbstractNewaveRepository(ABC):
    @property
    @abstractmethod
    def arquivos(self) -> Union[Arquivos, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_dger(self) -> Union[Dger, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_dger(self, d: Dger) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_hidr(self) -> Union[Hidr, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def get_confhd(self) -> Union[Confhd, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_confhd(self, d: Confhd) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_eafpast(self) -> Union[Eafpast, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_eafpast(self, d: Eafpast) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_adterm(self) -> Union[Adterm, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_adterm(self, d: Adterm) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_term(self) -> Union[Term, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_term(self, d: Term) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_pmo(self) -> Union[Pmo, HTTPResponse]:
        raise NotImplementedError


class RawNewaveRepository(AbstractNewaveRepository):
    def __init__(self, path: str):
        self.__path = path
        try:
            self.__caso = Caso.read(join(self.__path, "caso.dat"))
        except FileNotFoundError:
            Log.log().error("Não foi encontrado o arquivo caso.dat")
        self.__arquivos: Optional[Arquivos] = None
        self.__dger: Union[Dger, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_dger = False
        self.__hidr: Union[Hidr, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_hidr = False
        self.__confhd: Union[Confhd, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_confhd = False
        self.__eafpast: Union[Eafpast, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_eafpast = False
        self.__adterm: Union[Adterm, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_adterm = False
        self.__term: Union[Term, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_term = False
        self.__pmo: Union[Pmo, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_pmo = False

    @property
    def arquivos(self) -> Union[Arquivos, HTTPResponse]:
        if self.__arquivos is None:
            try:
                self.__arquivos = Arquivos.read(
                    join(self.__path, self.__caso.arquivos)
                )
            except FileNotFoundError:
                msg = f"Não foi encontrado o arquivo {self.__caso.arquivos}"
                Log.log().error(msg)
                return HTTPResponse(code=404, detail=msg)
        return self.__arquivos

    async def get_dger(self) -> Union[Dger, HTTPResponse]:
        if self.__read_dger is False:
            self.__read_dger = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_dger = arq.dger
                if not arq_dger:
                    raise FileNotFoundError()
                caminho = str(pathlib.Path(self.__path).joinpath(arq_dger))
                script = str(
                    pathlib.Path(Settings.installdir).joinpath(
                        Settings.encoding_script
                    )
                )
                await converte_codificacao(caminho, script)
                Log.log().info(f"Lendo arquivo {arq_dger}")
                self.__dger = Dger.read(join(self.__path, arq_dger))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo dger.dat"
                self.__dger = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do dger.dat: {e}")
                self.__dger = HTTPResponse(code=500, detail=str(e))
        return self.__dger

    def set_dger(self, d: Dger) -> HTTPResponse:
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_dger = arq.dger
            if not arq_dger:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_dger))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_hidr(self) -> Union[Hidr, HTTPResponse]:
        if self.__read_hidr is False:
            self.__read_hidr = True
            try:
                Log.log().info("Lendo arquivo hidr.dat")
                self.__hidr = Hidr.read(join(self.__path, "hidr.dat"))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo hidr.dat"
                self.__hidr = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error("Erro na leitura do hidr.dat: {e}")
                self.__hidr = HTTPResponse(code=500, detail=str(e))
        return self.__hidr

    def get_confhd(self) -> Union[Confhd, HTTPResponse]:
        if self.__read_confhd is False:
            self.__read_confhd = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_confhd = arq.confhd
                if not arq_confhd:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_confhd}")
                self.__confhd = Confhd.read(join(self.__path, arq_confhd))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo confhd.dat"
                self.__confhd = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do confhd.dat: {e}")
                self.__confhd = HTTPResponse(code=500, detail=str(e))
        return self.__confhd

    def set_confhd(self, d: Confhd):
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_confhd = arq.confhd
            if not arq_confhd:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_confhd))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_eafpast(self) -> Union[Eafpast, HTTPResponse]:
        if self.__read_eafpast is False:
            self.__read_eafpast = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_vazpast = arq.vazpast
                if not arq_vazpast:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_vazpast}")
                self.__eafpast = Eafpast.read(join(self.__path, arq_vazpast))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo eafpast.dat"
                self.__eafpast = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do eafpast.dat: {e}")
                self.__eafpast = HTTPResponse(code=500, detail=str(e))
        return self.__eafpast

    def set_eafpast(self, d: Eafpast):
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_vazpast = arq.vazpast
            if not arq_vazpast:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_vazpast))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_adterm(self) -> Union[Adterm, HTTPResponse]:
        if self.__read_adterm is False:
            self.__read_adterm = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_adterm = arq.adterm
                if not arq_adterm:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_adterm}")
                self.__adterm = Adterm.read(join(self.__path, arq_adterm))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo adterm.dat"
                self.__adterm = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do adterm.dat: {e}")
                self.__adterm = HTTPResponse(code=500, detail=str(e))
        return self.__adterm

    def set_adterm(self, d: Adterm):
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_adterm = arq.adterm
            if not arq_adterm:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_adterm))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_term(self) -> Union[Term, HTTPResponse]:
        if self.__read_term is False:
            self.__read_term = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_term = arq.term
                if not arq_term:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_term}")
                self.__term = Term.read(join(self.__path, arq_term))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo term.dat"
                self.__term = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do term.dat: {e}")
                self.__term = HTTPResponse(code=500, detail=str(e))
        return self.__term

    def set_term(self, d: Term):
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_term = arq.term
            if not arq_term:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_term))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_pmo(self) -> Union[Pmo, HTTPResponse]:
        if self.__read_pmo is False:
            self.__read_pmo = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_pmo = arq.pmo
                if not arq_pmo:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_pmo}")
                self.__pmo = Pmo.read(join(self.__path, arq_pmo))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo pmo.dat"
                self.__pmo = HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do pmo.dat: {e}")
                self.__pmo = HTTPResponse(code=500, detail=str(e))
        return self.__pmo


class TestNewaveRepository(AbstractNewaveRepository):
    def __init__(self, path: str) -> None:
        super().__init__()

    @property
    def arquivos(self) -> Union[Arquivos, HTTPResponse]:
        return Arquivos.read("".join(MockArquivos))

    async def get_dger(self) -> Union[Dger, HTTPResponse]:
        return Dger.read("".join(MockDger))

    def set_dger(self, d: Dger) -> HTTPResponse:
        raise NotImplementedError

    def get_hidr(self) -> Union[Hidr, HTTPResponse]:
        with open(
            join(curdir, "tests", "mocks", "arquivos", "newave", "hidr.dat"),
            "rb",
        ) as f:
            return Hidr.read(f.read())

    def get_confhd(self) -> Union[Confhd, HTTPResponse]:
        return Confhd.read("".join(MockConfhd))

    def set_confhd(self, d: Confhd) -> HTTPResponse:
        sio = StringIO()
        d.write(sio)
        return HTTPResponse(code=200, detail=sio.getvalue())

    def get_eafpast(self) -> Union[Eafpast, HTTPResponse]:
        raise NotImplementedError

    def set_eafpast(self, d: Eafpast):
        raise NotImplementedError

    def get_adterm(self) -> Union[Adterm, HTTPResponse]:
        raise NotImplementedError

    def set_adterm(self, d: Adterm):
        raise NotImplementedError

    def get_term(self) -> Union[Term, HTTPResponse]:
        raise NotImplementedError

    def set_term(self, d: Term):
        raise NotImplementedError

    def get_pmo(self) -> Union[Pmo, HTTPResponse]:
        raise NotImplementedError


def factory(kind: str, *args, **kwargs) -> AbstractNewaveRepository:
    mappings: Dict[str, Type[AbstractNewaveRepository]] = {
        "FS": RawNewaveRepository,
        "TEST": TestNewaveRepository,
    }
    return mappings.get(kind, RawNewaveRepository)(*args, **kwargs)
