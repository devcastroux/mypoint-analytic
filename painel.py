import pandas as pd
import streamlit as st

from alertas import gerar_alertas, resumo_por_funcionario
from analise import calcular_horas, carregar_pontos_java

st.set_page_config(page_title="MyPoint Analytics", page_icon="⏱️", layout="wide")


@st.cache_data(ttl=300)
def carregar_dados():
    df = calcular_horas(carregar_pontos_java())
    df["data"] = pd.to_datetime(df["data"])
    return df


st.title("⏱️ MyPoint Analytics")
st.caption("Análise de ponto e alertas de jornada (dados fictícios para demonstração)")

try:
    df = carregar_dados()
except Exception as erro:
    st.error("Não consegui ler o banco. O MySQL está ligado?")
    st.code(str(erro))
    st.stop()

if df.empty:
    st.warning("Nenhum registro de ponto encontrado.")
    st.stop()

# ---------- filtros (barra lateral) ----------
st.sidebar.header("Filtros")
nomes = sorted(df["nome"].unique())
escolhidos = st.sidebar.multiselect("Funcionários", nomes, default=nomes)

data_min = df["data"].min().date()
data_max = df["data"].max().date()
periodo = st.sidebar.date_input(
    "Período", value=(data_min, data_max), min_value=data_min, max_value=data_max
)
if isinstance(periodo, tuple) and len(periodo) == 2:
    inicio, fim = periodo
else:
    st.sidebar.info("Selecione a data inicial e a final.")
    st.stop()

filtro = (
    df["nome"].isin(escolhidos)
    & (df["data"].dt.date >= inicio)
    & (df["data"].dt.date <= fim)
)
dados = df[filtro].copy()
if dados.empty:
    st.warning("Nenhum registro com esses filtros.")
    st.stop()

alertas = gerar_alertas(dados)

# ---------- indicadores ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros analisados", len(dados))
c2.metric("Alertas", len(alertas))
c3.metric("Funcionários com alerta", alertas["nome"].nunique())
c4.metric("Média de horas por dia", f"{dados['horas_trabalhadas'].mean():.2f} h")

st.divider()

# ---------- gráficos ----------
esq, dir_ = st.columns(2)
with esq:
    st.subheader("Alertas por tipo")
    if alertas.empty:
        st.info("Nenhum alerta no período.")
    else:
        st.bar_chart(alertas["tipo"].value_counts())
with dir_:
    st.subheader("Média de horas por funcionário")
    st.bar_chart(dados.groupby("nome")["horas_trabalhadas"].mean().round(2))

# ---------- ranking ----------
st.subheader("Ranking de ocorrências por funcionário")
if alertas.empty:
    st.info("Sem ocorrências para mostrar.")
else:
    st.dataframe(resumo_por_funcionario(alertas))

    # ---------- lista de alertas ----------
    st.subheader("Lista de alertas")
    tipos = sorted(alertas["tipo"].unique())
    tipos_sel = st.multiselect("Tipo de alerta", tipos, default=tipos)
    lista = alertas[alertas["tipo"].isin(tipos_sel)].copy()
    lista["data"] = pd.to_datetime(lista["data"]).dt.strftime("%d/%m/%Y").fillna("—")
    st.dataframe(lista, hide_index=True)
    st.download_button(
        "Baixar alertas (CSV)",
        lista.to_csv(index=False).encode("utf-8-sig"),
        file_name="alertas.csv",
        mime="text/csv",
    )