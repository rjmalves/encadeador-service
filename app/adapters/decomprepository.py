from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, Union
import pathlib
from os.path import join

from idecomp.decomp.caso import Caso
from idecomp.decomp.arquivos import Arquivos
from idecomp.decomp.dadger import Dadger
from idecomp.decomp.dadgnl import Dadgnl
from idecomp.decomp.inviabunic import InviabUnic
from idecomp.decomp.relato import Relato
from idecomp.decomp.relgnl import Relgnl
from idecomp.decomp.hidr import Hidr

from app.internal.settings import Settings
from app.utils.encoding import converte_codificacao
from app.utils.log import Log
from app.internal.httpresponse import HTTPResponse


class AbstractDecompRepository(ABC):
    @property
    @abstractmethod
    def caso(self) -> Union[Caso, HTTPResponse]:
        raise NotImplementedError

    @property
    @abstractmethod
    def arquivos(self) -> Union[Arquivos, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    async def get_dadger(self) -> Union[Dadger, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_dadger(self, d: Dadger) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_dadgnl(self) -> Union[Dadgnl, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def set_dadgnl(self, d: Dadgnl) -> HTTPResponse:
        raise NotImplementedError

    @abstractmethod
    def get_inviabunic(self) -> Union[InviabUnic, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def get_relato(self) -> Union[Relato, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def get_relgnl(self) -> Union[Relgnl, HTTPResponse]:
        raise NotImplementedError

    @abstractmethod
    def get_hidr(self) -> Union[Hidr, HTTPResponse]:
        raise NotImplementedError


class RawDecompRepository(AbstractDecompRepository):
    def __init__(self, path: str):
        self.__path = path
        try:
            self.__caso = Caso.read(join(str(self.__path), "caso.dat"))
        except FileNotFoundError:
            Log.log().error("Não foi encontrado o arquivo caso.dat")
        self.__arquivos: Optional[Arquivos] = None
        self.__dadger: Union[Dadger, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_dadger = False
        self.__dadgnl: Union[Dadgnl, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_dadgnl = False
        self.__relato: Union[Relato, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_relato = False
        self.__relgnl: Union[Relgnl, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_relgnl = False
        self.__inviabunic: Union[InviabUnic, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_inviabunic = False
        self.__hidr: Union[Hidr, HTTPResponse] = HTTPResponse(
            code=404, detail=""
        )
        self.__read_hidr = False

    @property
    def caso(self) -> Caso:
        return self.__caso

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

    async def get_dadger(self) -> Union[Dadger, HTTPResponse]:
        if self.__read_dadger is False:
            self.__read_dadger = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_dadger = arq.dadger
                if not arq_dadger:
                    raise FileNotFoundError()
                caminho = str(pathlib.Path(self.__path).joinpath(arq_dadger))
                script = str(
                    pathlib.Path(Settings.installdir).joinpath(
                        Settings.encoding_script
                    )
                )
                await converte_codificacao(caminho, script)
                Log.log().info(f"Lendo arquivo {arq_dadger}")
                self.__dadger = Dadger.read(join(self.__path, arq_dadger))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo dadger"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do dadger: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__dadger

    def set_dadger(self, d: Dadger) -> HTTPResponse:
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_dadger = arq.dadger
            if not arq_dadger:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_dadger))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    async def get_dadgnl(self) -> Union[Dadgnl, HTTPResponse]:
        if self.__read_dadgnl is False:
            self.__read_dadgnl = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_dadgnl = arq.dadgnl
                if not arq_dadgnl:
                    raise FileNotFoundError()
                caminho = str(pathlib.Path(self.__path).joinpath(arq_dadgnl))
                script = str(
                    pathlib.Path(Settings.installdir).joinpath(
                        Settings.encoding_script
                    )
                )
                await converte_codificacao(caminho, script)
                Log.log().info(f"Lendo arquivo {arq_dadgnl}")
                self.__dadgnl = Dadgnl.read(join(self.__path, arq_dadgnl))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo dadgnl"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do dadgnl: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__dadgnl

    def set_dadgnl(self, d: Dadgnl) -> HTTPResponse:
        try:
            arq = self.arquivos
            if isinstance(arq, HTTPResponse):
                raise FileNotFoundError()
            arq_dadgnl = arq.dadgnl
            if not arq_dadgnl:
                raise FileNotFoundError()
            d.write(join(self.__path, arq_dadgnl))
            return HTTPResponse(code=200, detail="")
        except Exception as e:
            return HTTPResponse(code=500, detail=str(e))

    def get_relato(self) -> Union[Relato, HTTPResponse]:
        if self.__read_relato is False:
            self.__read_relato = True
            try:
                arq = self.caso.arquivos
                if not arq:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo relato.{arq}")
                self.__relato = Relato.read(join(self.__path, f"relato.{arq}"))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo relato"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do relato: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__relato

    def get_relgnl(self) -> Union[Relgnl, HTTPResponse]:
        if self.__read_relgnl is False:
            self.__read_relgnl = True
            try:
                arq = self.caso.arquivos
                if not arq:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo relgnl.{arq}")
                self.__relgnl = Relgnl.read(join(self.__path, f"relgnl.{arq}"))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo relgnl"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do relgnl: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__relgnl

    def get_inviabunic(self) -> Union[InviabUnic, HTTPResponse]:
        if self.__read_inviabunic is False:
            self.__read_inviabunic = True
            try:
                arq = self.caso.arquivos
                if not arq:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo inviab_unic.{arq}")
                self.__inviabunic = InviabUnic.read(
                    join(self.__path, f"inviab_unic.{arq}")
                )
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo inviab_unic"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().info(f"Erro na leitura do inviab_unic: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__inviabunic

    def get_hidr(self) -> Union[Hidr, HTTPResponse]:
        if self.__read_hidr is False:
            self.__read_hidr = True
            try:
                arq = self.arquivos
                if isinstance(arq, HTTPResponse):
                    raise FileNotFoundError()
                arq_hidr = arq.hidr
                if not arq_hidr:
                    raise FileNotFoundError()
                Log.log().info(f"Lendo arquivo {arq_hidr}")
                self.__hidr = Hidr.read(join(self.__path, arq_hidr))
            except FileNotFoundError:
                msg = "Não foi encontrado o arquivo hidr"
                return HTTPResponse(code=404, detail=msg)
            except Exception as e:
                Log.log().error(f"Erro na leitura do hidr: {e}")
                return HTTPResponse(code=500, detail=str(e))
        return self.__hidr


def factory(kind: str, *args, **kwargs) -> AbstractDecompRepository:
    mapping: Dict[str, Type[AbstractDecompRepository]] = {
        "FS": RawDecompRepository
    }
    return mapping.get(kind, RawDecompRepository)(*args, **kwargs)
