from fastapi.testclient import TestClient
from app.routers import chain
from app.models.program import Program
from app.models.chainingcase import ChainingCase
from app.models.chainingvariable import ChainingVariable
from app.models.chainingrequest import ChainingRequest
from inewave.newave import Confhd
from idecomp.decomp import Relato
from tests.mocks.arquivos.newave.confhd import MockConfhd
from tests.mocks.arquivos.decomp.relato import MockRelato

client = TestClient(chain.router)


def test_chain_decomp_newave_varm():
    # . encoded
    path = "k"
    source = ChainingCase(id=path, program=Program.DECOMP)
    destination = ChainingCase(id=path, program=Program.NEWAVE)
    variable = ChainingVariable.VARM
    req = ChainingRequest(
        sources=[source], destination=destination, variable=variable
    )
    response = client.post("/chain/", content=req.model_dump_json())
    assert response.status_code == 200
    res_json = response.json()
    assert "result" in res_json

    chd = Confhd.read("".join(MockConfhd))
    usinas_newave = [u.strip() for u in chd.usinas["nome_usina"].tolist()]
    rel = Relato.read("".join(MockRelato))
    df_vol = rel.volume_util_reservatorios
    for chain_res in res_json["result"]:
        if chain_res["id"] in df_vol["nome_usina"]:
            assert (
                df_vol.loc[
                    df_vol["nome_usina"] == chain_res["id"], "estagio_1"
                ].iloc[0]
                == chain_res["value"]
            )

        assert chain_res["id"] in usinas_newave


def test_chain_decomp_decomp_varm():
    # . encoded
    path = "k"
    source = ChainingCase(id=path, program=Program.DECOMP)
    destination = ChainingCase(id=path, program=Program.DECOMP)
    variable = ChainingVariable.VARM
    req = ChainingRequest(
        sources=[source], destination=destination, variable=variable
    )
    response = client.post("/chain/", content=req.model_dump_json())
    assert response.status_code == 200
    res_json = response.json()
    assert "result" in res_json

    rel = Relato.read("".join(MockRelato))
    df_vol = rel.volume_util_reservatorios
    for chain_res in res_json["result"]:
        if chain_res["id"] in df_vol["nome_usina"]:
            assert (
                df_vol.loc[
                    df_vol["nome_usina"] == chain_res["id"], "estagio_1"
                ].iloc[0]
                == chain_res["value"]
            )


def test_chain_decomp_decomp_tviagem():
    # . encoded
    path = "k"
    source = ChainingCase(id=path, program=Program.DECOMP)
    destination = ChainingCase(id=path, program=Program.DECOMP)
    variable = ChainingVariable.TVIAGEM
    req = ChainingRequest(
        sources=[source], destination=destination, variable=variable
    )
    response = client.post("/chain/", content=req.model_dump_json())
    assert response.status_code == 200
    res_json = response.json()
    assert "result" in res_json
    rel = Relato.read("".join(MockRelato))
    df_oper = rel.relatorio_operacao_uhe
    for chain_res in res_json["result"]:
        assert (
            df_oper.loc[
                df_oper["nome_usina"] == chain_res["id"], "vazao_defluente_m3s"
            ].iloc[0]
            == chain_res["value"]
        )
