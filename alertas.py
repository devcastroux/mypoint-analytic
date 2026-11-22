import pandas as pd

COLUNAS_HORA = ["entrada_manha", "saida_almoco", "entrada_almoco", "saida_tarde"]

# Regras (ajuste como quiser)
ENTRADA_PREVISTA = pd.Timedelta(hours=8)
TOLERANCIA = pd.Timedelta(minutes=10)   # tolerância de atraso na entrada
INTERVALO_MINIMO_MIN = 60               # almoço mínimo de 1h
JORNADA_MAXIMA_H = 10                   # 8h normais + até 2h extras por dia
MIN_DIAS_PADRAO_SUSPEITO = 10           # dias mínimos para checar "sempre o mesmo horário"


def gerar_alertas(df):
    """Recebe o DataFrame de calcular_horas() e devolve uma linha por alerta."""
    alertas = []

    def adicionar(mascara, tipo, detalhe):
        achados = df[mascara]
        for _, linha in achados.iterrows():
            alertas.append({
                "nome": linha["nome"],
                "data": linha["data"],
                "tipo": tipo,
                "detalhe": detalhe(linha),
            })

    # 1) Batida faltando em algum dos 4 horários
    faltando = df[COLUNAS_HORA].isna().any(axis=1)
    adicionar(
        faltando, "batida_faltando",
        lambda l: "sem: " + ", ".join(c for c in COLUNAS_HORA if pd.isna(l[c])),
    )

    # 2) Atraso na entrada (acima da tolerância)
    atraso = df["entrada_manha"] > ENTRADA_PREVISTA + TOLERANCIA
    adicionar(
        atraso, "atraso",
        lambda l: f"entrou {str(l['entrada_manha']).split(' ')[-1][:5]}",
    )

    # 3) Intervalo de almoço menor que o mínimo
    almoco_curto = df["intervalo_min"] < INTERVALO_MINIMO_MIN
    adicionar(
        almoco_curto, "almoco_curto",
        lambda l: f"intervalo de {l['intervalo_min']:.0f} min",
    )

    # 4) Jornada acima do limite
    longa = df["horas_trabalhadas"] > JORNADA_MAXIMA_H
    adicionar(
        longa, "jornada_longa",
        lambda l: f"{l['horas_trabalhadas']:.1f} h trabalhadas",
    )

    resultado = pd.DataFrame(alertas, columns=["nome", "data", "tipo", "detalhe"])

    # 5) Padrão suspeito: entrada sempre no mesmo horário exato (por funcionário)
    suspeitos = []
    for nome, grupo in df.groupby("nome"):
        entradas = grupo["entrada_manha"].dropna()
        if len(entradas) >= MIN_DIAS_PADRAO_SUSPEITO and entradas.nunique() == 1:
            suspeitos.append({
                "nome": nome,
                "data": None,
                "tipo": "horario_identico",
                "detalhe": f"{len(entradas)} dias com a mesma entrada exata",
            })
    if suspeitos:
        resultado = pd.concat([resultado, pd.DataFrame(suspeitos)], ignore_index=True)

    return resultado.sort_values(["nome", "data"], na_position="last").reset_index(drop=True)


def resumo_por_funcionario(alertas):
    """Quantidade de cada tipo de alerta por funcionário, do mais problemático ao menos."""
    tabela = alertas.pivot_table(
        index="nome", columns="tipo", values="detalhe", aggfunc="count", fill_value=0
    )
    tabela["total"] = tabela.sum(axis=1)
    return tabela.sort_values("total", ascending=False)


if __name__ == "__main__":
    from analise import carregar_pontos, calcular_horas

    df = calcular_horas(carregar_pontos())
    alertas = gerar_alertas(df)

    print(f"{len(alertas)} alertas em {len(df)} registros\n")
    print("Alertas por tipo:")
    print(alertas["tipo"].value_counts())
    print("\nRanking por funcionário:")
    print(resumo_por_funcionario(alertas).to_string())
    print("\nÚltimos alertas:")
    print(alertas.tail(10).to_string())