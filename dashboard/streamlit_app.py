import os
import json
import requests
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import altair as alt

API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Painel de Vendas", layout="wide")

st.title("Painel Automatizado de Dados")

# Filters
with st.expander("Filtros", expanded=True):
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        start = st.date_input("Início", value=date.today() - timedelta(days=30))
    with col2:
        end = st.date_input("Fim", value=date.today())
    with col3:
        q = st.text_input("Busca (produto ou SKU)", value="")
    with col4:
        category = st.text_input("Categoria (nome)", value="")

# Summary
try:
    r = requests.get(f"{API_URL}/dashboard/summary", params={"start": start.isoformat(), "end": end.isoformat()}, timeout=10)
    r.raise_for_status()
    summary = r.json()
except Exception as e:
    st.warning(f"Falha ao carregar resumo: {e}")
    summary = {"total_sales": 0, "revenue": 0, "ticket_medio": 0, "series": [], "top_products": []}

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Quantidade Vendida", summary.get("total_sales", 0))
with c2:
    st.metric("Receita", f"R$ {summary.get('revenue', 0):,.2f}")
with c3:
    st.metric("Ticket Médio", f"R$ {summary.get('ticket_medio', 0):,.2f}")

# Charts
series = pd.DataFrame(summary.get("series", []))
if not series.empty:
    chart = alt.Chart(series).mark_line().encode(x='date:T', y='revenue:Q').properties(title="Receita por dia")
    st.altair_chart(chart, use_container_width=True)

# Top produtos
top_df = pd.DataFrame(summary.get("top_products", []))
if not top_df.empty:
    st.subheader("Top Produtos (por receita)")
    st.dataframe(top_df)

# Upload Excel
st.subheader("Importar Excel/CSV")
uploaded = st.file_uploader("Selecione um .xlsx ou .csv", type=["xlsx", "csv"])
if uploaded:
    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
    try:
        r = requests.post(f"{API_URL}/import", files=files, timeout=120)
        r.raise_for_status()
        job = r.json()
        st.success(f"Import iniciado. Job: {job.get('job_id')}")
    except Exception as e:
        st.error(f"Falha no import: {e}")

# Products table with search + pagination
st.subheader("Produtos")
pg1, pg2, pg3 = st.columns([1,1,6])
with pg1:
    page = st.number_input("Página", min_value=1, value=1, step=1)
with pg2:
    per_page = st.selectbox("Itens/página", options=[10,20,50,100], index=1)

try:
    params = {"page": page, "per_page": per_page}
    if q:
        params["q"] = q
    if category:
        params["category"] = category
    r = requests.get(f"{API_URL}/products", params=params, timeout=10)
    r.raise_for_status()
    products = r.json()
    st.dataframe(pd.DataFrame(products))
except Exception as e:
    st.warning(f"Falha ao carregar produtos: {e}")

# Recent sales
st.subheader("Vendas Recentes")
try:
    r = requests.get(f"{API_URL}/sales", params={"page": 1, "per_page": 50}, timeout=10)
    r.raise_for_status()
    sales = r.json()
    st.dataframe(pd.DataFrame(sales))
except Exception as e:
    st.warning(f"Falha ao carregar vendas: {e}")
