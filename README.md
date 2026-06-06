# Sistema Inteligente de Monitoramento Espacial

## Equipe

- Nome da equipe: Pedro Henrique Canavezi
- Integrantes e RMs: Pedro Henrique Canavezi/// RM: 570298

## Resumo do problema

O projeto simula o monitoramento de uma missao espacial experimental. O sistema le dados de telemetria, interpreta o estado de modulos criticos, identifica riscos operacionais, gera alertas automaticos e recomenda acoes para manter a seguranca da missao.

O cenario analisado inclui seis modulos principais: suporte de vida, energia, comunicacao, habitat, laboratorio e armazenamento. Tambem sao avaliados energia gerada, energia consumida, reserva das baterias, temperatura, radiacao, vento e qualidade de comunicacao.

## Arquivos do projeto

- `src/sistema.py`: codigo Python principal.
- `data/dados.csv`: dados simulados exigidos para entrega.
- `database/dados.csv`: copia dos mesmos dados para compatibilidade com a estrutura inicial do repositorio.
- `docs/relatorio.pdf`: relatorio da solucao.
- `docs/link-video.txt`: link do video de apresentacao.
- `docs/uso_ia.md`: registro do uso de IA no desenvolvimento.

## Estruturas de dados usadas

- Listas: armazenam a serie historica de telemetria, como geracao, consumo, reserva, radiacao e comunicacao.
- Fila: organiza alertas pendentes na ordem de deteccao antes da priorizacao por severidade.
- Pilha: registra eventos criticos analisados, permitindo consultar primeiro o evento critico mais recente.
- Dicionarios: permitem acessar rapidamente o estado de cada modulo pelo nome.
- Hierarquia: representa grupos da missao, como energia, habitat e operacao.
- Matriz: representa leituras por horario e variavel no formato `[horario, geracao, consumo, reserva, radiacao, comunicacao]`.

## Regras logicas principais

A expressao booleana principal do diagnostico e:

```text
missao_critica =
    (modulo_essencial_falhou OR reserva_critica OR comunicacao_critica OR radiacao_critica)
    AND NOT sensores_invalidados
```

Regras aplicadas no codigo:

- Se um modulo essencial estiver com valor binario `0`, o sistema gera alerta critico.
- Se a reserva de energia estiver abaixo de 35% AND o consumo estiver maior que a geracao, a missao entra em estado critico.
- Se a radiacao estiver elevada OR o vento estiver extremo, atividades externas devem ser suspensas.
- Se a comunicacao estiver inoperante OR a qualidade estiver abaixo de 30%, a antena reserva deve ser ativada.
- Se uma inconsistencia de dados for detectada, o sistema recomenda validar sensores antes de tomar decisao automatica definitiva.

## Tecnica de previsao

Foi utilizada regressao linear simples, calculada manualmente sem bibliotecas avancadas. A variavel analisada e a reserva energetica da missao.

O sistema usa os valores historicos de reserva para calcular a tendencia media por ciclo e prever a reserva do proximo horario. Essa previsao influencia a recomendacao final: caso a reserva prevista fique abaixo dos limites definidos, o sistema recomenda economia de energia e priorizacao de modulos essenciais.

## Como executar

No terminal, na raiz do repositorio:

```bash
python src/sistema.py
```

## Exemplo de entrada

Trecho de `data/dados.csv`:

```csv
tipo,horario,modulo,status,geracao_kwh,consumo_kwh,reserva_pct
modulo,,comunicacao,0,,,,
telemetria,20:00,,,25,76,32
telemetria,24:00,,,29,82,38
```

O ultimo registro contem uma inconsistencia proposital: a reserva sobe de 32% para 38% mesmo com consumo maior que geracao.

## Exemplo de saida

```text
Status geral da missao: CRITICO
Codigo binario dos modulos: 110111 (decimal 55)
[CRITICO] comunicacao: Comunicacao comprometida.
Recomendacao: Ativar antena reserva e transmitir pacote minimo de telemetria.
```

## Recomendacoes geradas pelo sistema

- Ativar redundancia em caso de falha de modulo essencial.
- Priorizar suporte de vida e comunicacao de emergencia.
- Desligar cargas nao essenciais quando a energia estiver critica.
- Suspender atividade externa em caso de radiacao elevada ou vento extremo.
- Validar sensores quando houver inconsistencia nos dados.

## Link do video

Preencher com o link do YouTube como "Nao listado".

## Conclusoes e aprendizados

O projeto demonstra como estruturas de dados, regras logicas e analise simples podem apoiar decisoes em um ambiente critico. A simulacao mostra que um sistema de monitoramento precisa interpretar dados numericos, diagnosticar anomalias, priorizar alertas e justificar recomendacoes tecnicas de forma clara.
