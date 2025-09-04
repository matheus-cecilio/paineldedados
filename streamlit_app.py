import streamlit as st
import pandas as pd
import httpx
import time

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(layout="wide", page_title="Painel de Vendas")

st.title("📊 Painel de Dados - Sistema de Gestão")
st.markdown("Sistema de gestão e análise de vendas")

def upload_file(file):
    files = {'file': (file.name, file, file.type)}
    try:
        with httpx.Client() as client:
            response = client.post(f"{API_URL}/imports/upload", files=files, timeout=30)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"Erro na API: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Erro de conexão com a API: {e}")
    return None

with st.sidebar:
    st.header("Importar Dados")
    uploaded_file = st.file_uploader("Selecione uma planilha Excel (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        if st.button("▶️ Iniciar Importação"):
            with st.spinner("Enviando arquivo..."):
                result = upload_file(uploaded_file)
            
            if result and result.get('id'):
                job_id = result['id']
                st.success(f"Arquivo enviado! Job ID: `{job_id}`")
                
                progress_bar = st.progress(0, text="Aguardando processamento...")
                
                status = "PENDING"
                while status in ["PENDING", "RUNNING"]:
                    time.sleep(2)
                    try:
                        r = httpx.get(f"{API_URL}/imports/status/{job_id}")
                        r.raise_for_status()
                        status_data = r.json()
                        status = status_data.get('status', 'FAILED')
                        progress_text = f"Processando... Status: {status}"
                        if status == "RUNNING":
                            progress_bar.progress(50, text=progress_text)
                        elif status == "DONE":
                            progress_bar.progress(100, text="Importação Concluída!")
                            st.success("Dados importados com sucesso!")
                        elif status == "FAILED":
                            progress_bar.empty()
                            st.error(f"Falha na importação: {status_data.get('errors')}")
                            break
                    except Exception as e:
                        st.error(f"Erro ao verificar status: {e}")
                        break
            else:
                st.error("Falha ao iniciar a importação.")

st.header("Visão Geral")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita Total", "R$ 287.450", "+12.5%")
col2.metric("Total de Vendas", "1.247", "+8.2%")
col3.metric("Ticket Médio", "R$ 230", "+3.1%")
col4.metric("Clientes Ativos", "892", "-2.4%")

st.header("Análise de Vendas")
# TODO: Fetch data from /dashboard/summary endpoint and display real charts
chart_data = pd.DataFrame(
   pd.np.random.randn(20, 3),
   columns=['a', 'b', 'c'])
st.line_chart(chart_data)