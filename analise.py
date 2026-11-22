import pandas as pd
from conexao import conectar

COLUNAS_HORA = ["entrada_manha", "saida_almoco", "entrada_almoco", "saida_tarde"]


def carregar_pontos():
    """Lê a tabela registros_ponto (1 linha por dia, 4 horários) - dados fictícios."""
    sql = """
        SELECT u.id AS usuario_id, u.nome, r.data,
               r.entrada_manha, r.saida_almoco, r.entrada_almoco, r.saida_tarde
        FROM registros_ponto r
        JOIN usuarios u ON u.id = r.usuario_id
        ORDER BY u.nome, r.data
    """
    conn = conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            colunas = [c[0] for c in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=colunas)
    finally:
        conn.close()

    for col in COLUNAS_HORA:
        df[col] = pd.to_timedelta(df[col])
    return df


def calcular_horas(df):
    manha = df["saida_almoco"] - df["entrada_manha"]
    tarde = df["saida_tarde"] - df["entrada_almoco"]
    df["horas_trabalhadas"] = (manha + tarde).dt.total_seconds() / 3600
    df["intervalo_min"] = (df["entrada_almoco"] - df["saida_almoco"]).dt.total_seconds() / 60
    return df


def pontos_java_para_tabela(df):
    """Converte 1 batida por linha (texto) em 1 linha por dia com 4 horários."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data_ponto"], format="%d/%m/%Y")
    df["hora"] = pd.to_timedelta(df["hora_ponto"])
    df = df.sort_values(["usuario_id", "data", "hora"])
    df["n"] = df.groupby(["usuario_id", "data"]).cumcount()
    df = df[df["n"] < 4]  # batidas além da 4ª no dia são ignoradas

    largo = (
        df.pivot(index=["usuario_id", "nome", "data"], columns="n", values="hora")
        .rename(columns=dict(enumerate(COLUNAS_HORA)))
        .reset_index()
    )
    largo.columns.name = None
    for col in COLUNAS_HORA:
        if col not in largo.columns:
            largo[col] = pd.NaT
    return largo[["usuario_id", "nome", "data"] + COLUNAS_HORA]


def carregar_pontos_java():
    """Lê a tabela pontos_registrados (1 linha por batida), gravada pelo sistema Java."""
    sql = """
        SELECT u.id AS usuario_id, u.nome, p.data_ponto, p.hora_ponto
        FROM pontos_registrados p
        JOIN usuarios u ON u.email = p.email_funcionario
    """
    conn = conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            colunas = [c[0] for c in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=colunas)
    finally:
        conn.close()
    return pontos_java_para_tabela(df)


if __name__ == "__main__":
    df = calcular_horas(carregar_pontos_java())
    print(df.head(10))
    print(f"\n{len(df)} registros")
    print("\nMédia de horas por funcionário:")
    print(df.groupby("nome")["horas_trabalhadas"].mean().round(2))