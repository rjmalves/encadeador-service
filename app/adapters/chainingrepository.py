from abc import ABC, abstractmethod
from typing import Dict, List, Union, Callable
import pandas as pd  # type: ignore
from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import VI, UH

from app.models.program import Program
from app.models.chainingresult import ChainingResult
from app.internal.httpresponse import HTTPResponse
from app.models.chainingvariable import ChainingVariable
from app.services.unitofwork import (
    AbstractUnitOfWork,
    NewaveUnitOfWork,
    DecompUnitOfWork,
)
from app.utils.log import Log


class AbstractChainingRepository(ABC):
    """ """

    async def chain(
        self,
        variable: ChainingVariable,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        RULES: Dict[ChainingVariable, Callable] = {
            ChainingVariable.VARM: self.chain_varm,
            ChainingVariable.TVIAGEM: self.chain_tviagem,
            ChainingVariable.GNL: self.chain_gnl,
            ChainingVariable.ENA: self.chain_ena,
        }
        f = RULES.get(variable)
        if f is None:
            return HTTPResponse(code=404, detail=f"{variable} not supported")
        return await f(sources_uow, destination_uow)

    @abstractmethod
    async def chain_varm(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        pass

    @abstractmethod
    async def chain_tviagem(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        pass

    @abstractmethod
    async def chain_gnl(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        pass

    @abstractmethod
    async def chain_ena(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        pass


class NEWAVEChainingRepository(AbstractChainingRepository):
    """ """

    async def chain_varm(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        def __numero_uhe_decomp(numero_newave: int) -> int:
            mapa_ficticias_NW_DC = {
                318: 122,
                319: 57,
                294: 162,
                295: 156,
                308: 155,
                298: 148,
                292: 252,
                302: 261,
                303: 257,
                306: 253,
            }
            if numero_newave in mapa_ficticias_NW_DC.keys():
                return mapa_ficticias_NW_DC[numero_newave]
            else:
                return numero_newave

        def __coluna_para_encadear() -> str:
            # TODO - voltar a suportar caso de NW semanal
            # if self._caso_atual.revisao == 0:
            if True:
                return "estagio_1"
            else:
                return list(volumes.columns)[-2]

        def __encadeia_ilha_solteira_equiv(
            volumes: pd.DataFrame, usinas: pd.DataFrame
        ) -> pd.DataFrame:
            vol = volumes.loc[
                volumes["codigo_usina"] == 44, __coluna_para_encadear()
            ].iloc[0]

            Log.log().info(f"Caso especial de I. Solteira Equiv: {vol} %")
            usinas.loc[usinas["codigo_usina"] == 34, "inicial"] = vol
            usinas.loc[usinas["codigo_usina"] == 43, "inicial"] = vol
            results.append(
                ChainingResult(id=hidr.at[34, "nome_usina"], value=vol)
            )
            results.append(
                ChainingResult(id=hidr.at[43, "nome_usina"], value=vol)
            )
            return usinas

        def __correcao_serra_mesa_ficticia(vol: float) -> float:
            return min([100.0, vol / 0.55])

        def __separou_ilha_solteira_equiv(
            volumes: pd.DataFrame, usinas: pd.DataFrame
        ) -> bool:
            # Saber se tem I. Solteira Equiv. no DECOMP mas tem as
            # usinas separadas no NEWAVE
            usinas_newave = usinas["codigo_usina"].tolist()
            usinas_decomp = volumes["codigo_usina"].tolist()
            return all(
                [
                    44 not in usinas_newave,
                    43 in usinas_newave,
                    34 in usinas_newave,
                    44 in usinas_decomp,
                    43 not in usinas_decomp,
                    34 not in usinas_decomp,
                ]
            )

        def __interpola_volume() -> float:
            # TODO - implementar para maior precisão
            raise NotImplementedError

        SERRA_MESA_FICT_DC = 251
        SERRA_MESA_FICT_NW = 291

        decomps_uow = [s for s in sources_uow if s.program == Program.DECOMP]
        if len(decomps_uow) == 0:
            return HTTPResponse(
                code=422, detail="must have at least 1 DECOMP source"
            )
        last_decomp_uow = decomps_uow[-1]
        assert isinstance(last_decomp_uow, DecompUnitOfWork)

        Log.log().info("Encadeando VARM - DECOMP -> NEWAVE")
        with last_decomp_uow:
            relato = last_decomp_uow.files.get_relato()
        if isinstance(relato, HTTPResponse):
            return relato

        volumes = relato.volume_util_reservatorios
        if volumes is None:
            return HTTPResponse(
                code=500, detail="erro na leitura dos volumes do relato"
            )

        assert isinstance(destination_uow, NewaveUnitOfWork)
        with destination_uow:
            arq_hidr = destination_uow.files.get_hidr()
            arq_confhd = destination_uow.files.get_confhd()
        if isinstance(arq_confhd, HTTPResponse):
            return arq_confhd
        if isinstance(arq_hidr, HTTPResponse):
            return arq_hidr

        hidr = arq_hidr.cadastro
        usinas = arq_confhd.usinas
        if usinas is None:
            return HTTPResponse(
                code=500, detail="erro na leitura das usinas do confhd"
            )

        results: List[ChainingResult] = []
        # Atualiza cada armazenamento
        for _, linha in usinas.iterrows():
            num = linha["codigo_usina"]
            num_dc = __numero_uhe_decomp(num)
            # Confere se tem o reservatório
            if num_dc not in set(volumes["codigo_usina"]):
                continue
            vol = volumes.loc[
                volumes["codigo_usina"] == num_dc, __coluna_para_encadear()
            ].iloc[0]

            if num_dc == SERRA_MESA_FICT_DC:
                vf = __correcao_serra_mesa_ficticia(vol)
                num_nw = SERRA_MESA_FICT_NW
                usinas.loc[
                    usinas["codigo_usina"] == num_nw,
                    "volume_inicial_percentual",
                ] = vf
                results.append(
                    ChainingResult(id=hidr.at[num_nw, "nome_usina"], value=vf)
                )

            usinas.loc[
                usinas["codigo_usina"] == num, "volume_inicial_percentual"
            ] = vol
            results.append(
                ChainingResult(id=hidr.at[num, "nome_usina"], value=vol)
            )

        # Trata o caso de I. Solteira Equiv.
        if __separou_ilha_solteira_equiv(volumes, usinas):
            usinas = __encadeia_ilha_solteira_equiv(volumes, usinas)

        with destination_uow:
            res = destination_uow.files.set_confhd(arq_confhd)
            if res.code != 200:
                return res

        return results

    async def chain_tviagem(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        return HTTPResponse(code=405, detail="TVIAGEM not allowed for NEWAVE")

    async def chain_gnl(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        return HTTPResponse(code=501, detail="GNL not implemented for NEWAVE")

    async def chain_ena(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        return HTTPResponse(code=501, detail="ENA not implemented for NEWAVE")


class DECOMPChainingRepository(AbstractChainingRepository):
    """ """

    async def chain_varm(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        decomps_uow = [s for s in sources_uow if s.program == Program.DECOMP]
        if len(decomps_uow) == 0:
            return HTTPResponse(
                code=422, detail="must have at least 1 DECOMP source"
            )
        last_decomp_uow = decomps_uow[-1]
        assert isinstance(last_decomp_uow, DecompUnitOfWork)

        Log.log().info("Encadeando VARM - DECOMP -> DECOMP")

        def __separou_ilha_solteira_equiv(
            volumes: pd.DataFrame, dadger: Dadger
        ) -> bool:
            # Saber se tem I. Solteira Equiv. no DECOMP mas tem as
            # usinas separadas no próximo DECOMP
            vols_relato = volumes["codigo_usina"].tolist()

            existe_equiv_relato = 44 in vols_relato
            existem_separadas_relato = all(
                [34 in vols_relato, 43 in vols_relato]
            )
            existe_equiv_dadger = dadger.uh(44) is not None
            existem_separadas_dadger = (dadger.uh(34) is not None) and (
                dadger.uh(43) is not None
            )
            return all(
                [
                    existe_equiv_relato,
                    not existem_separadas_relato,
                    not existe_equiv_dadger,
                    existem_separadas_dadger,
                ]
            )

        def __encadeia_ilha_solteira_equiv(
            volumes: pd.DataFrame, dadger: Dadger
        ):
            vol = volumes.loc[volumes["codigo_usina"] == 44, "estagio_1"].iloc[
                0
            ]

            Log.log().info(f"Caso especial de I. Solteira Equiv: {vol} %")
            for codigo_uh in [34, 43]:
                uh = dadger.uh(codigo_uh)
                assert isinstance(uh, UH)
                uh.volume_inicial = vol
                nome_usina: str = hidr.at[codigo_uh, "nome_usina"]
                results.append(ChainingResult(id=nome_usina, value=vol))

        with last_decomp_uow:
            relato = last_decomp_uow.files.get_relato()
        if isinstance(relato, HTTPResponse):
            return relato

        assert isinstance(destination_uow, DecompUnitOfWork)

        with destination_uow:
            dadger = await destination_uow.files.get_dadger()
            arq_hidr = destination_uow.files.get_hidr()
        if isinstance(dadger, HTTPResponse):
            return dadger
        if isinstance(arq_hidr, HTTPResponse):
            return arq_hidr

        hidr = arq_hidr.cadastro
        volumes = relato.volume_util_reservatorios
        if volumes is None:
            return HTTPResponse(
                code=500, detail="erro na leitura dos volumes do relato"
            )

        results: List[ChainingResult] = []
        # Encadeia cada armazenamento
        for _, linha in volumes.iterrows():
            num = linha["codigo_usina"]

            # Caso especial de I. Solteira Equiv.
            if num == 44 and __separou_ilha_solteira_equiv(volumes, dadger):
                __encadeia_ilha_solteira_equiv(volumes, dadger)
                continue

            vol = volumes.loc[
                volumes["codigo_usina"] == num, "estagio_1"
            ].iloc[0]

            uh = dadger.uh(num)
            assert isinstance(uh, UH)
            uh.volume_inicial = vol
            results.append(
                ChainingResult(id=hidr.at[num, "nome_usina"], value=vol)
            )

        with destination_uow:
            res = destination_uow.files.set_dadger(dadger)
            if res.code != 200:
                return res

        return results

    async def chain_tviagem(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        def __codigos_usinas_tviagem() -> List[int]:
            return [156, 162]

        decomps_uow = [s for s in sources_uow if s.program == Program.DECOMP]
        if len(decomps_uow) == 0:
            return HTTPResponse(
                code=422, detail="must have at least 1 DECOMP source"
            )
        last_decomp_uow = decomps_uow[-1]
        assert isinstance(last_decomp_uow, DecompUnitOfWork)

        Log.log().info("Encadeando TVIAGEM - DECOMP -> DECOMP")
        with last_decomp_uow:
            dadger_ant = await last_decomp_uow.files.get_dadger()
            relato = last_decomp_uow.files.get_relato()
        if isinstance(dadger_ant, HTTPResponse):
            return dadger_ant
        if isinstance(relato, HTTPResponse):
            return relato

        assert isinstance(destination_uow, DecompUnitOfWork)

        with destination_uow:
            dadger = await destination_uow.files.get_dadger()
            arq_hidr = destination_uow.files.get_hidr()
        if isinstance(dadger, HTTPResponse):
            return dadger
        if isinstance(arq_hidr, HTTPResponse):
            return arq_hidr

        hidr = arq_hidr.cadastro

        relatorio = relato.relatorio_operacao_uhe
        if relatorio is None:
            return HTTPResponse(
                code=500,
                detail="erro na leitura do relatório das UHEs do relato",
            )

        results: List[ChainingResult] = []
        # Encadeia cada tempo de viagem
        for codigo in __codigos_usinas_tviagem():
            # Extrai o Qdef do relato
            qdef = relatorio.loc[
                (relatorio["estagio"] == 1)
                & (relatorio["codigo_usina"] == codigo),
                "vazao_defluente_m3s",
            ].iloc[0]

            # Atualiza os tempos de viagem no dadger
            vi_ant = dadger_ant.vi(codigo)
            vi_novo = dadger.vi(codigo)
            assert isinstance(vi_ant, VI)
            assert isinstance(vi_novo, VI)
            vazoes_anteriores = vi_ant.vazao
            assert isinstance(vazoes_anteriores, list)
            vi_novo.vazao = [qdef] + vazoes_anteriores[:-1]
            results.append(
                ChainingResult(id=hidr.at[codigo, "nome_usina"], value=qdef)
            )

        with destination_uow:
            res = destination_uow.files.set_dadger(dadger)
            if res.code != 200:
                return res

        return results

    async def chain_gnl(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        decomps_uow = [s for s in sources_uow if s.program == Program.DECOMP]
        if len(decomps_uow) == 0:
            return HTTPResponse(
                code=422, detail="must have at least 1 DECOMP source"
            )
        last_decomp_uow = decomps_uow[-1]
        assert isinstance(last_decomp_uow, DecompUnitOfWork)

        Log.log().info("Encadeando GNL - DECOMP -> DECOMP")

        with last_decomp_uow:
            dad_anterior = await last_decomp_uow.files.get_dadgnl()
            rel = last_decomp_uow.files.get_relgnl()
        if isinstance(dad_anterior, HTTPResponse):
            return dad_anterior
        if isinstance(rel, HTTPResponse):
            return rel

        assert isinstance(destination_uow, DecompUnitOfWork)

        with destination_uow:
            dad = await destination_uow.files.get_dadgnl()
        if isinstance(dad, HTTPResponse):
            return dad

        usinas_termicas = rel.usinas_termicas
        if usinas_termicas is None:
            return HTTPResponse(
                code=500,
                detail="erro na leitura das usinas termicas do relgnl",
            )
        cods = usinas_termicas["codigo_usina"].unique()
        usinas = usinas_termicas["nome_usina"].unique()
        mapa_codigo_usina = {c: u for c, u in zip(cods, usinas)}

        registros_nl = dad.nl()
        assert isinstance(registros_nl, list)
        codigos = [r.codigo_usina for r in registros_nl]

        registros = dad.gl()
        assert isinstance(registros, list)
        registros_anteriores = dad_anterior.gl()
        assert isinstance(registros_anteriores, list)

        results: List[ChainingResult] = []
        for c in codigos:
            # Para cada semana i (exceto a última), o registro GL do DadGNL do
            # caso atual deve ter o valor do respectivo registro GL do DadGNL
            # do caso anterior na semana i + 1
            registros_usina = [r for r in registros if r.codigo_usina == c]
            registros_usina_anterior = [
                r for r in registros_anteriores if r.codigo_usina == c
            ]
            # Se a usina não existia no deck anterior, ignora
            if len(registros_usina_anterior) == 0:
                continue
            cols_despacho = [f"geracao_patamar_{i}" for i in [1, 2, 3]]
            for r in registros_usina:
                # Para a última semana, o registro GL do DadGNL atual deve vir
                # do RelGNL do caso anterior, onde a semana de início tenha o
                # mesmo valor.
                if r == registros_usina[-1]:
                    op = rel.relatorio_operacao_termica
                    if op is None:
                        return HTTPResponse(
                            code=500,
                            detail="erro na leitura do relatorio de operacao "
                            "termica do relgnl",
                        )
                    data_inicio = r.data_inicio
                    if data_inicio is None:
                        return HTTPResponse(
                            code=500,
                            detail="erro na leitura da data de inicio do "
                            "registro GL do dadgnl",
                        )
                    data = (
                        data_inicio[:2]
                        + "/"
                        + data_inicio[2:4]
                        + "/"
                        + data_inicio[4:]
                    )
                    # Procura pela linha em op filtrando por nome, data
                    # e pegando as colunas dos despachos
                    nome = mapa_codigo_usina[c]
                    filtro = (op["nome_usina"] == nome) & (
                        op["data_inicio_semana"] == data
                    )
                    geracoes = op.loc[filtro, cols_despacho].to_numpy()
                    r.geracao = [g for g in geracoes[0]]
                    results.append(ChainingResult(id=nome, value=geracoes[-1]))
                else:
                    # Procura pelo registro anterior com a mesma data
                    reg_ant = [
                        ra
                        for ra in registros_usina_anterior
                        if ra.data_inicio == r.data_inicio
                    ][0]
                    r.geracao = reg_ant.geracao

        with destination_uow:
            res = destination_uow.files.set_dadgnl(dad)
            if res.code != 200:
                return res

        return results

    async def chain_ena(
        self,
        sources_uow: List[AbstractUnitOfWork],
        destination_uow: AbstractUnitOfWork,
    ) -> Union[List[ChainingResult], HTTPResponse]:
        return HTTPResponse(code=405, detail="ENA not allowed for DECOMP")


SUPPORTED_PROGRAMS = {
    Program.NEWAVE: NEWAVEChainingRepository,
    Program.DECOMP: DECOMPChainingRepository,
}
DEFAULT = DECOMPChainingRepository


def factory(
    destination: Program, *args, **kwargs
) -> AbstractChainingRepository:
    return SUPPORTED_PROGRAMS.get(destination, DEFAULT)(*args, **kwargs)
