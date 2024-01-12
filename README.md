# encadeador-service
Serviço para realização de encadeamento de resultados em casos de NEWAVE / DECOMP / DESSEM para a realização de estudos encadeados. Este serviço é fornecido por meio de uma API REST contendo uma única rota, que recebe os argumentos necessários para realizar a transferência de resultados finais de um caso para outro.

Atualmente é esperado que este serviço seja lançado no próprio cluster, com acesso ao sistema de arquivos onde os casos que serão processados se encontram. Além disso, as variáveis que podem ser encadeadas dependem dos casos que estão sendo relacionados, dado que o DECOMP possui variáveis como o Tempo de Viagem, não representado no NEWAVE.


## Instalação

Para realizar a instalação a partir do repositório, é recomendado criar um ambiente virtual e realizar a instalação das dependências dentro do mesmo.

```
$ git clone https://github.com/rjmalves/encadeador-service
$ cd encadeador-service
$ python3 -m venv ./venv
$ source ./venv/bin/activate
$ pip install -r requirements.txt
```

## Configuração

A configuração do serviço pode ser feita através de um arquivo de variáveis de ambiente `.env`, existente no próprio diretório de instalação. O conteúdo deste arquivo:

```
CLUSTER_ID=1
HOST="0.0.0.0"
PORT=5053
ROOT_PATH="/api/v1/chain"
```

Cada deploy do `encadeador-service` deve ter um atributo `CLUSTER_ID` único, para que outros serviços possam controlar atividades em clusters distintos. 

Atualmente as opções suportadas são:

|       Campo       |   Valores aceitos   |
| ----------------- | ------------------- |
| CLUSTER_ID        | `int`               |
| HOST              | `str`               |
| PORT              | `int`               |
| ROOT_PATH         | `str` (URL prefix)  |

## Uso

Para executar o programa, basta interpretar o arquivo `main.py`:

```
$ source ./venv/bin/activate
$ python main.py
```

No terminal é impresso um log de acompanhamento:

```
INFO:     Started server process [2133]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5053 (Press CTRL+C to quit)
INFO:     127.0.0.1:36872 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:36872 - "GET /openapi.json HTTP/1.1" 200 OK
```


Maiores detalhes sobre a rota disponível pode ser visto ao lançar a aplicação localmente e acessar a rota `/docs`, que possui uma página no formato [OpenAPI](https://swagger.io/specification/). Em geral, casos são referenciados por meio do seus caminhos no sistema de arquivos codificados em `base62` e o encadeamento é especificado por um mnemônico da variável a ser encadeada, que é enviado na requisição de encadeamento.


## Variáveis Encadeadas

Atualmente é suportado encadear até 4 variáveis operativas, não necessariamente entre todos os modelos que são utilizados para estudos encadeados.


### Volume Armazenado (VARM)

É assumido que, no ponto inicial do backtest, os volumes iniciais dos modelos são compatíveis. A implementação atual suporta o caso mais comum de execuções mensais de NEWAVE e semanais de DECOMP. Os volumes encadeados são sempre resultados de execuções de DECOMP, valores finais de primeira semana de estudo.

Encadeamentos suportados:

- DECOMP -> NEWAVE

O resultado da primeira semana de estudo da última revisão de DECOMP de um determinado mês é utilizada para encadeamento com os volumes iniciais do NEWAVE do mês seguinte. Os volumes são extraídos do arquivo `relato.rvX` e inseridos no `confhd.dat`.

Como existem usinas com representações diferentes entre NEWAVE e DECOMP, existe um mapeamento constante no código que especifica a transferência de volumes a ser feita neste processo de encadeamento. São exceções implementadas:

1. Mapeamento de usinas do DECOMP para fictícias do NEWAVE

É declarado um mapa específico para usinas que são fictícias no NEWAVE:

```python
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
```

2. Encadeamento de Serra de Mesa

Como a UHE 251 é representada como uma única usina no DECOMP, mas como uma usina real (251) e outra fictícia (291) no NEWAVE, é dado um tratamento especial no encadeamento ao transferir um volume do DECOMP para dois volumes do NEWAVE. Para a UHE 251, é transferido o volume integral decidido pelo DECOMP. Para a UHE 291, é realizada uma correção:

```python
def __correcao_serra_mesa_ficticia(vol: float) -> float:
    return min([100.0, vol / 0.55])
```

3. Mudança na Representação de Ilha Solteira

Em algum momento houve uma mudança na representação de Ilha Solteira (34) e Três Irmãos (43), que eram representadas como Ilha Solteira Equivalente (44). Desta forma, existe um encadeamento que irá enxergar usinas separadas no NEWAVE e a usina equivalente no DECOMP, dado que a transição ocorreu em um novo mês. O tratamento especial para este caso é transferir o volume da UHE 44 para ambas UHEs 34 e 43.

```python
def __encadeia_ilha_solteira_equiv(
    volumes: pd.DataFrame, usinas: pd.DataFrame
) -> pd.DataFrame:
    vol = float(
        volumes.loc[
            volumes["codigo_usina"] == 44, "estagio_1"
        ]
    )
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
```

- DECOMP -> DECOMP

O resultado da primeira semana de estudo do DECOMP anterior é utilizado para os volumes iniciais do próximo DECOMP. O único caso especial tratado neste encadeamento é a mudança na representação de Ilha Solteira, que foi descrita na seção anterior e é implementado por:

```python
def __encadeia_ilha_solteira_equiv(
    volumes: pd.DataFrame, dadger: Dadger
):
    vol = float(
        volumes.loc[volumes["codigo_usina"] == 44, "estagio_1"]
    )
    Log.log().info(f"Caso especial de I. Solteira Equiv: {vol} %")
    dadger.uh(34).volume_inicial = vol
    dadger.uh(43).volume_inicial = vol
    results.append(
        ChainingResult(id=hidr.at[34, "nome_usina"], value=vol)
    )
    results.append(
        ChainingResult(id=hidr.at[43, "nome_usina"], value=vol)
    )
```

### Tempo de Viagem da Água (TVIAGEM)

O tempo de viagem de água atualmente só é suportado no modelo DECOMP, por meio dos registros `VI` no arquivo `dadger.rvX`. Logo, apenas é suportado o encadeamento de `TVIAGEM` entre execuções do modelo DECOMP. O tempo de viagem é representado apenas para as usinas de Três Marias (156) e XXX (162).

- DECOMP -> DECOMP

Para realizar o encadeamento, o resultado de vazão defluente da primeira semana de uma usina é extraído do arquivo `relato.rvX` e é adicionado à primeira posição do registro `VI` da mesma usina no DECOMP seguinte, sendo complementado pelas demais entradas do registro `VI` do `dadger.rvX` do DECOMP anterior.

```python
...
relatorio = relato.relatorio_operacao_uhe
results: List[ChainingResult] = []
# Encadeia cada tempo de viagem
for codigo in __codigos_usinas_tviagem():
    # Extrai o Qdef do relato
    qdef = float(
        relatorio.loc[
            (relatorio["estagio"] == 1)
            & (relatorio["codigo_usina"] == codigo),
            "vazao_defluente_m3s",
        ]
    )
    # Atualiza os tempos de viagem no dadger
    vi: VI = dadger_ant.vi(codigo)
    dadger.vi(codigo).vazao = [qdef] + vi.vazao[:-1]
    results.append(
        ChainingResult(id=hidr.at[codigo, "nome_usina"], value=qdef)
    )
...

```

### Despacho Programado de Usinas a Gás Natural Liquefeito (GNL)

O despacho das usinas térmicas GNL atualmente possui apenas suporte ao encadeamento também entre execuções do modelo DECOMP. Em versões antigas do sistema de encadeamento, era suportada a transferência também no modelo NEWAVE, que foi descontinuada e deve ser reestabelecida em versões futuras.

- DECOMP -> DECOMP

São extraídas informações dos arquivos `dadgnl.rvX` e `relgnl.rvX` do DECOMP anterior e adicionadas ao arquivo `dadgnl.rvX` do DECOMP seguinte, com regras específicas para tratar a entrada de usinas novas em operação e as semanas para as quais foi determinado o despacho.


### Previsão de Energia Natural Afluente (ENA)

O encadeamento da previsão de ENA foi descontinuado na versão atual do serviço e deve ser reestabelecida em versões futuras.


## Rota Fornecida pelo Serviço

A única rota fornecida pelo serviço é `POST /chain`, onde o corpo do objeto `JSON` contém o seguinte formato:

```json
{
    "sources": [
        {
        "id": "IgMI7zzpD0irzRysgz7ia2z2KbKEIQEpZ2GpEhUvJGvNxpMlD65iC9oeOQ4",
        "program": "DECOMP"
        }
    ],
    "destination": {
        "id": "IgMI7zzpD0irzRysgz7ia2z2KbKEIQEpZ2GpEhUvJGvNxpMlD65lJjqJqsv",
        "program": "NEWAVE"
    },
    "variable": "VARM"
}
```

Os campos informados são:

- `sources`: Uma lista de casos excutados anteriormente, em ordem cronológica, que podem ser utilizados para definição das informações de entrada do caso que está sendo encadeado. Um caso é resumido a um atributo `id`, que é o caminho para o diretório do caso codificado em `base62`, e um atributo `program` para o nome do programa. Atualmente somente casos de `DECOMP` são suportados como fonte das variáveis.  
- `destination`: Um caso, representado da mesma maneira do campo anterior, para ser alvo do encadeamento.  
- `variable`: Um dos mnemônicos suportados para definir a variável encadeada.

A resposta, se flexibilização for realizada com sucesso, contém um objeto com uma lista de `ChainingReult`, que são pares do tipo [`id`, `value`], onde o significado de cada campo pode variar conforma a variável encadeada. Para o caso de volumes armazenados, `id` possui o nome da usina e `value` o volume que foi transferido.