import csv
from collections import deque
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "dados.csv"
FALLBACK_DATA_PATH = BASE_DIR / "database" / "dados.csv"


LIMITES = {
    "reserva_alerta": 45,
    "reserva_critica": 35,
    "radiacao_alerta": 0.50,
    "radiacao_critica": 0.70,
    "comunicacao_alerta": 60,
    "comunicacao_critica": 30,
    "temperatura_alerta": 28,
}


SEVERIDADE_ORDEM = {
    "critico": 0,
    "alerta": 1,
    "normal": 2,
}


def valor_float(linha, campo):
    valor = texto(linha, campo)
    return float(valor) if valor else 0.0


def texto(linha, campo):
    valor = linha.get(campo, "")
    return valor.strip() if valor else ""


def carregar_dados(caminho=DATA_PATH):
    if not caminho.exists():
        caminho = FALLBACK_DATA_PATH

    modulos = {}
    telemetria = []
    eventos = []

    with caminho.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            tipo = linha["tipo"].strip().lower()

            if tipo == "modulo":
                nome = linha["modulo"].strip()
                modulos[nome] = {
                    "status_binario": int(linha["status"]),
                    "descricao": texto(linha, "descricao"),
                }

            elif tipo == "telemetria":
                telemetria.append(
                    {
                        "horario": texto(linha, "horario"),
                        "geracao_kwh": valor_float(linha, "geracao_kwh"),
                        "consumo_kwh": valor_float(linha, "consumo_kwh"),
                        "reserva_pct": valor_float(linha, "reserva_pct"),
                        "temp_interna_c": valor_float(linha, "temp_interna_c"),
                        "temp_externa_c": valor_float(linha, "temp_externa_c"),
                        "radiacao_msv": valor_float(linha, "radiacao_msv"),
                        "qualidade_comunicacao_pct": valor_float(
                            linha, "qualidade_comunicacao_pct"
                        ),
                        "vento_kmh": valor_float(linha, "vento_kmh"),
                        "observacao": texto(linha, "descricao"),
                    }
                )

            elif tipo == "evento":
                eventos.append(
                    {
                        "id": texto(linha, "event_id"),
                        "severidade": texto(linha, "severidade").lower(),
                        "evento": texto(linha, "evento"),
                        "descricao": texto(linha, "descricao"),
                    }
                )

    return modulos, telemetria, eventos, caminho


def criar_hierarquia(modulos):
    return {
        "energia": {
            "solar": "geracao_kwh",
            "baterias": "reserva_pct",
            "estado": modulos["energia"]["status_binario"],
        },
        "habitat": {
            "oxigenio": "suporte_vida",
            "temperatura": "temp_interna_c",
            "comunicacao": "qualidade_comunicacao_pct",
        },
        "operacao": {
            "laboratorio": modulos["laboratorio"]["status_binario"],
            "armazenamento": modulos["armazenamento"]["status_binario"],
        },
    }


def criar_matriz_leituras(telemetria):
    return [
        [
            leitura["horario"],
            leitura["geracao_kwh"],
            leitura["consumo_kwh"],
            leitura["reserva_pct"],
            leitura["radiacao_msv"],
            leitura["qualidade_comunicacao_pct"],
        ]
        for leitura in telemetria
    ]


def classificar_modulos(modulos):
    tabela = {}
    essenciais = {"suporte_vida", "energia", "comunicacao", "habitat"}

    for nome, dados in modulos.items():
        if dados["status_binario"] == 1:
            status = "normal"
        elif nome in essenciais:
            status = "critico"
        else:
            status = "alerta"
        tabela[nome] = status

    return tabela


def adicionar_alerta(fila, pilha, severidade, origem, mensagem, recomendacao):
    alerta = {
        "severidade": severidade,
        "origem": origem,
        "mensagem": mensagem,
        "recomendacao": recomendacao,
    }
    fila.append(alerta)

    if severidade == "critico":
        pilha.append(alerta)


def detectar_inconsistencias(telemetria):
    inconsistencias = []

    for indice in range(1, len(telemetria)):
        anterior = telemetria[indice - 1]
        atual = telemetria[indice]
        deficit = atual["consumo_kwh"] > atual["geracao_kwh"]
        reserva_subiu = atual["reserva_pct"] > anterior["reserva_pct"]

        if deficit and reserva_subiu:
            inconsistencias.append(
                f"{atual['horario']}: reserva subiu de "
                f"{anterior['reserva_pct']:.0f}% para {atual['reserva_pct']:.0f}% "
                "mesmo com consumo maior que geracao."
            )

    return inconsistencias


def prever_reserva_linear(telemetria):
    # Regressao linear simples feita manualmente, sem bibliotecas externas.
    y = [leitura["reserva_pct"] for leitura in telemetria]
    x = list(range(len(y)))
    n = len(x)
    soma_x = sum(x)
    soma_y = sum(y)
    soma_xy = sum(xi * yi for xi, yi in zip(x, y))
    soma_x2 = sum(xi * xi for xi in x)

    divisor = n * soma_x2 - soma_x * soma_x
    inclinacao = (n * soma_xy - soma_x * soma_y) / divisor if divisor else 0
    intercepto = (soma_y - inclinacao * soma_x) / n
    proximo_ciclo = n
    previsto = intercepto + inclinacao * proximo_ciclo

    return round(previsto, 2), round(inclinacao, 2)


def gerar_alertas(modulos, telemetria, eventos):
    fila_alertas = deque()
    pilha_criticos = []
    tabela_modulos = classificar_modulos(modulos)
    ultima = telemetria[-1]

    for modulo, status in tabela_modulos.items():
        if status == "critico":
            adicionar_alerta(
                fila_alertas,
                pilha_criticos,
                "critico",
                modulo,
                f"Modulo essencial {modulo} esta inoperante.",
                "Ativar redundancia e direcionar recursos para modo de seguranca.",
            )
        elif status == "alerta":
            adicionar_alerta(
                fila_alertas,
                pilha_criticos,
                "alerta",
                modulo,
                f"Modulo {modulo} esta em estado de atencao.",
                "Monitorar modulo e preparar manutencao preventiva.",
            )

    if ultima["reserva_pct"] < LIMITES["reserva_critica"] and ultima["consumo_kwh"] > ultima["geracao_kwh"]:
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "critico",
            "energia",
            "Reserva energetica critica e consumo acima da geracao.",
            "Desligar cargas nao essenciais e priorizar suporte a vida e comunicacao de emergencia.",
        )
    elif ultima["reserva_pct"] < LIMITES["reserva_alerta"] or ultima["consumo_kwh"] > ultima["geracao_kwh"]:
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "alerta",
            "energia",
            "Energia em tendencia desfavoravel.",
            "Reduzir consumo do laboratorio e aumentar monitoramento das baterias.",
        )

    if ultima["radiacao_msv"] >= LIMITES["radiacao_critica"] or ultima["vento_kmh"] > 60:
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "critico",
            "ambiente",
            "Radiacao elevada ou vento extremo detectado.",
            "Manter tripulacao no habitat protegido e suspender atividade externa.",
        )
    elif ultima["radiacao_msv"] >= LIMITES["radiacao_alerta"] and ultima["temp_interna_c"] > LIMITES["temperatura_alerta"]:
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "alerta",
            "ambiente",
            "Radiacao e temperatura interna acima do ideal.",
            "Reforcar controle termico e revisar blindagem do habitat.",
        )

    if (
        modulos["comunicacao"]["status_binario"] == 0
        or ultima["qualidade_comunicacao_pct"] < LIMITES["comunicacao_critica"]
    ):
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "critico",
            "comunicacao",
            "Comunicacao comprometida.",
            "Ativar antena reserva e transmitir pacote minimo de telemetria.",
        )
    elif not ultima["qualidade_comunicacao_pct"] >= LIMITES["comunicacao_alerta"]:
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "alerta",
            "comunicacao",
            "Qualidade de comunicacao abaixo do recomendado.",
            "Reorientar antena e reduzir trafego nao essencial.",
        )

    for inconsistencia in detectar_inconsistencias(telemetria):
        adicionar_alerta(
            fila_alertas,
            pilha_criticos,
            "alerta",
            "dados",
            f"Inconsistencia detectada: {inconsistencia}",
            "Validar sensores de energia antes de tomar decisao automatica definitiva.",
        )

    for evento in eventos:
        if evento["severidade"] == "critico":
            pilha_criticos.append(
                {
                    "severidade": "critico",
                    "origem": "evento",
                    "mensagem": f"{evento['id']} - {evento['evento']}: {evento['descricao']}",
                    "recomendacao": "Revisar evento critico no historico operacional.",
                }
            )

    return sorted(fila_alertas, key=lambda a: SEVERIDADE_ORDEM[a["severidade"]]), pilha_criticos, tabela_modulos


def classificar_missao(alertas, previsao_reserva):
    existe_critico = any(alerta["severidade"] == "critico" for alerta in alertas)
    existe_alerta = any(alerta["severidade"] == "alerta" for alerta in alertas)

    if existe_critico or previsao_reserva < LIMITES["reserva_critica"]:
        return "CRITICO"
    if existe_alerta or previsao_reserva < LIMITES["reserva_alerta"]:
        return "ALERTA"
    return "NORMAL"


def codigo_binario_modulos(modulos):
    bits = "".join(str(dados["status_binario"]) for dados in modulos.values())
    return bits, int(bits, 2)


def exibir_relatorio():
    modulos, telemetria, eventos, caminho = carregar_dados()
    hierarquia = criar_hierarquia(modulos)
    matriz = criar_matriz_leituras(telemetria)
    alertas, pilha_criticos, tabela_modulos = gerar_alertas(modulos, telemetria, eventos)
    previsao, inclinacao = prever_reserva_linear(telemetria)
    status_missao = classificar_missao(alertas, previsao)
    bits, decimal = codigo_binario_modulos(modulos)

    print("=" * 72)
    print("SISTEMA INTELIGENTE DE MONITORAMENTO ESPACIAL")
    print("=" * 72)
    print(f"Arquivo lido: {caminho.relative_to(BASE_DIR)}")
    print(f"Status geral da missao: {status_missao}")
    print(f"Codigo binario dos modulos: {bits} (decimal {decimal})")
    print()

    print("Tabela de status dos modulos:")
    for modulo, status in tabela_modulos.items():
        print(f"- {modulo}: {status}")
    print()

    print("Hierarquia operacional:")
    for grupo, dados in hierarquia.items():
        print(f"- {grupo}: {dados}")
    print()

    print("Matriz de leituras [horario, geracao, consumo, reserva, radiacao, comunicacao]:")
    for linha in matriz:
        print(f"- {linha}")
    print()

    print("Previsao de reserva energetica:")
    print(f"- Metodo: regressao linear simples sobre historico de reserva")
    print(f"- Tendencia media por ciclo: {inclinacao} ponto(s) percentual(is)")
    print(f"- Reserva prevista para o proximo ciclo: {previsao}%")
    if previsao < LIMITES["reserva_critica"]:
        print("- Decisao: economia maxima deve permanecer ativada.")
    elif previsao < LIMITES["reserva_alerta"]:
        print("- Decisao: reduzir consumo e observar baterias.")
    else:
        print("- Decisao: manter monitoramento padrao.")
    print()

    print("Alertas priorizados:")
    if not alertas:
        print("- Nenhum alerta ativo.")
    for alerta in alertas:
        print(f"- [{alerta['severidade'].upper()}] {alerta['origem']}: {alerta['mensagem']}")
        print(f"  Recomendacao: {alerta['recomendacao']}")
    print()

    print("Pilha de eventos criticos analisados (topo primeiro):")
    if not pilha_criticos:
        print("- Nenhum evento critico registrado.")
    while pilha_criticos:
        evento = pilha_criticos.pop()
        print(f"- {evento['mensagem']}")


if __name__ == "__main__":
    exibir_relatorio()
