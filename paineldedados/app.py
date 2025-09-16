import streamlit as st
import pandas as pd
import plotly.express as px
from core.invoice import generate_invoice_pdf
from core.supabase_db import listar_vendas, inserir_venda, criar_usuario, autenticar_usuario
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Painel de Vendas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    .stSuccess {
        border-left: 4px solid #28a745;
    }
    .stWarning {
        border-left: 4px solid #ffc107;
    }
    .stError {
        border-left: 4px solid #dc3545;
    }
    .stInfo {
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

st.title('📊 Painel de Vendas')

# Inicializar estado de login
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
    st.session_state.usuario_info = None

# Função para logout
def logout():
    st.session_state.usuario_logado = False
    st.session_state.usuario_info = None
    if 'lista_vendas' in st.session_state:
        st.session_state.lista_vendas = []

# Sidebar
st.sidebar.title("Configurações")

# Sistema de Login/Logout na Sidebar
if not st.session_state.usuario_logado:
    st.sidebar.markdown("### Login / Cadastro")
    
    tab_login, tab_cadastro = st.sidebar.tabs(["Login", "Cadastro"])
    
    with tab_login:
        st.markdown("**Faça login para salvar dados:**")
        email_login = st.text_input("E-mail", key="email_login")
        senha_login = st.text_input("Senha", type="password", key="senha_login")
        
        if st.button("Entrar", key="btn_login"):
            if email_login and senha_login:
                sucesso, usuario, mensagem = autenticar_usuario(email_login, senha_login)
                if sucesso:
                    st.session_state.usuario_logado = True
                    st.session_state.usuario_info = usuario
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)
            else:
                st.error("Preencha e-mail e senha")
    
    with tab_cadastro:
        st.markdown("**Criar nova conta:**")
        nome_cadastro = st.text_input("Nome", key="nome_cadastro")
        email_cadastro = st.text_input("E-mail", key="email_cadastro")
        senha_cadastro = st.text_input("Senha", type="password", key="senha_cadastro")
        
        if st.button("📝 Cadastrar", key="btn_cadastro"):
            if nome_cadastro and email_cadastro and senha_cadastro:
                sucesso, mensagem = criar_usuario(nome_cadastro, email_cadastro, senha_cadastro)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.error("Preencha todos os campos")

else:
    # Usuário logado
    st.sidebar.success(f"Olá, {st.session_state.usuario_info['nome']}!")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

# Instruções
with st.sidebar.expander('Como usar o sistema'):
    st.markdown("""
    **1. Primeira vez? Use dados de exemplo:**
    - Baixe "Dados de Exemplo" 
    - Faça upload para ver o sistema funcionando
    
    **2. Criar sua planilha:**
    - Baixe "Modelo Vazio"
    - Preencha com seus dados
    
    **Formato esperado:**
    - `produto`: Nome do produto
    - `quantidade`: Quantidade vendida
    - `valor unitário`: Preço por unidade
    - `data`: Data da venda (DD/MM/YYYY)
    - `valor total`: Quantidade × Valor unitario
    """)

st.sidebar.markdown("### Arquivos para Download")

# Modelo vazio
with open('sample_data/modelo_vendas.xlsx', 'rb') as f:
    modelo_data = f.read()

st.sidebar.download_button(
    label='Baixar Modelo Vazio',
    data=modelo_data,
    file_name='modelo_vendas.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    help="Planilha vazia para você preencher"
)

# Dados de exemplo
with open('sample_data/dados_exemplo.xlsx', 'rb') as f:
    exemplo_data = f.read()

st.sidebar.download_button(
    label='Baixar Dados de Exemplo',
    data=exemplo_data,
    file_name='dados_exemplo.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    help="Planilha com dados prontos para testar o sistema"
)

# SEÇÃO 1: UPLOAD E ANÁLISE DE PLANILHAS
st.header("Upload de planilha de vendas (XLSX / CSV)")
uploaded = st.file_uploader("Carregar Arquivo", type=['xlsx', 'csv'])

df = None

if uploaded is not None:
    try:
        if uploaded.type == 'text/csv' or str(uploaded.name).lower().endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        
        st.success('✅ Arquivo carregado com sucesso.')
        
        # Padronização das colunas
        column_mapping = {
            'produto': ['produto', 'product', 'item', 'nome'],
            'quantidade': ['quantidade', 'qtd', 'quantity', 'qty'],
            'valor_unitario': ['valor unitário', 'valor unitario', 'preco', 'price', 'unit_price'],
            'data': ['data', 'date', 'data_venda'],
            'valor_total': ['valor total', 'total', 'valor_total']
        }
        
        df_standardized = df.copy()
        for standard_col, possible_cols in column_mapping.items():
            for col in df.columns:
                if col.lower().strip() in possible_cols:
                    df_standardized = df_standardized.rename(columns={col: standard_col})
                    break
        
        # Exibe dados do arquivo
        st.subheader("Dados do arquivo")
        st.dataframe(
            df_standardized, 
            use_container_width=True, 
            height=400,
            hide_index=True
        )
        
        # Gráfico se tiver colunas corretas
        if 'produto' in df_standardized.columns and 'quantidade' in df_standardized.columns:
            if 'valor_unitario' in df_standardized.columns:
                df_standardized['subtotal'] = df_standardized['quantidade'] * df_standardized['valor_unitario']
                fig = px.bar(
                    df_standardized.groupby('produto', as_index=False)['subtotal'].sum().sort_values('subtotal', ascending=False),
                    x='produto', 
                    y='subtotal', 
                    title='Top produtos por receita'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Geração de PDF
        if 'produto' in df_standardized.columns:
            st.subheader('Gerar recibo / nota (PDF)')
            if 'cliente' in df_standardized.columns:
                customers = df_standardized['cliente'].dropna().unique().tolist()
                if customers:
                    sel_customer = st.selectbox('Selecione cliente', options=customers)
                    if st.button('Gerar PDF'):
                        items = df_standardized[df_standardized['cliente']==sel_customer].to_dict(orient='records')
                        items_for_pdf = []
                        for r in items:
                            item = {
                                'description': r.get('produto', 'Produto'),
                                'quantity': r.get('quantidade', 1),
                                'unit_price': r.get('valor_unitario', 0)
                            }
                            items_for_pdf.append(item)
                        
                        outdir = 'uploads'
                        os.makedirs(outdir, exist_ok=True)
                        invoice_no = datetime.now().strftime('%Y%m%d%H%M%S')
                        outpath = os.path.join(outdir, f'nota_{invoice_no}.pdf')
                        generate_invoice_pdf(invoice_no, sel_customer, items_for_pdf, outpath)
                        
                        with open(outpath,'rb') as f:
                            pdf_data = f.read()
                        
                        st.download_button(
                            'Baixar PDF', 
                            data=pdf_data, 
                            file_name=f'nota_{sel_customer}_{invoice_no}.pdf', 
                            mime='application/pdf'
                        )
                        st.success(f'✅ PDF gerado com sucesso!')
                else:
                    st.info("Nenhum cliente encontrado na planilha")
            else:
                st.info("Coluna 'cliente' não encontrada para geração de PDF")
                
    except Exception as e:
        st.error(f'❌ Erro ao processar arquivo: {e}')

# SEÇÃO 2: CADASTRO MANUAL DE VENDAS (APENAS SE LOGADO)
if st.session_state.usuario_logado:
    st.header("Cadastro Manual de Vendas")
    st.info(f"Olá {st.session_state.usuario_info['nome']}, use este formulário para cadastrar suas vendas")

    # Inicializar lista de produtos na sessão
    if 'lista_vendas' not in st.session_state:
        st.session_state.lista_vendas = []

    # Formulário de cadastro
    st.subheader("➕ Adicionar Produto")

    col1, col2, col3 = st.columns(3)

    with col1:
        produto = st.text_input(
            "Produto *", 
            value="",
            placeholder="Digite o nome do produto",
            key="input_produto"
        )

    with col2:
        quantidade = st.number_input(
            "Quantidade *", 
            min_value=0.01, 
            value=None,
            step=0.01,
            placeholder="0.00",
            key="input_quantidade"
        )

    with col3:
        preco_unitario = st.number_input(
            "Preço Unitário (R$) *", 
            min_value=0.01, 
            value=None,
            step=0.01,
            placeholder="0.00",
            key="input_preco"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        cliente = st.text_input(
            "Cliente (opcional)", 
            value="",
            placeholder="Nome do cliente",
            key="input_cliente"
        )

    with col5:
        numero_nota = st.text_input(
            "Nº da Nota (opcional)", 
            value="",
            placeholder="000001",
            key="input_nota"
        )

    with col6:
        data_venda = st.date_input(
            "Data",
            value=datetime.now().date(),
            format="DD/MM/YYYY",
            key="input_data"
        )

    # Botões de ação
    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("Adicionar à Lista", type="primary"):
            if produto and quantidade is not None and preco_unitario is not None:
                valor_total = quantidade * preco_unitario
                nova_venda = {
                    'produto': produto,
                    'quantidade': quantidade,
                    'preco_unitario': preco_unitario,
                    'valor_total': valor_total,
                    'cliente': cliente if cliente else None,
                    'numero_nota': numero_nota if numero_nota else None,
                    'data': data_venda.strftime('%Y-%m-%d')
                }
                st.session_state.lista_vendas.append(nova_venda)
                st.success(f"✅ {produto} adicionado à lista!")
                st.rerun()
            else:
                st.error("❌ Preencha os campos obrigatórios: Produto, Quantidade e Preço Unitário")

    with col_btn2:
        if st.button("🗑️ Limpar Lista"):
            st.session_state.lista_vendas = []
            st.success("✅ Lista limpa!")
            st.rerun()

    with col_btn3:
        if st.button("Salvar TODOS no Banco", type="primary"):
            if st.session_state.lista_vendas:
                sucessos = 0
                erros = 0
                
                for venda in st.session_state.lista_vendas:
                    sucesso, mensagem = inserir_venda(
                        produto=venda['produto'],
                        quantidade=venda['quantidade'],
                        preco_unitario=venda['preco_unitario'],
                        cliente=venda['cliente'],
                        numero_nota=venda['numero_nota'],
                        data=venda['data'],
                        usuario_id=st.session_state.usuario_info['id']
                    )
                    
                    if sucesso:
                        sucessos += 1
                    else:
                        erros += 1
                        st.error(f"Erro: {mensagem}")
                
                if sucessos > 0:
                    st.success(f"✅ {sucessos} venda(s) salva(s) com sucesso!")
                    st.session_state.lista_vendas = []  # Limpa a lista após salvar
                    st.rerun()
                
                if erros > 0:
                    st.error(f"❌ {erros} erro(s) ao salvar")
            else:
                st.warning("Adicione produtos à lista antes de salvar")

    # Exibir lista atual
    if st.session_state.lista_vendas:
        st.subheader("Produtos na Lista")
        
        for i, venda in enumerate(st.session_state.lista_vendas):
            col_info, col_remove = st.columns([4, 1])
            
            with col_info:
                st.write(f"**{venda['produto']}** - Qtd: {venda['quantidade']} - R$ {venda['preco_unitario']:.2f} - Total: R$ {venda['valor_total']:.2f}")
                if venda['cliente']:
                    st.write(f"Cliente: {venda['cliente']}")
            
            with col_remove:
                if st.button("❌", key=f"remove_{i}", help="Remover item"):
                    st.session_state.lista_vendas.pop(i)
                    st.rerun()

    # VENDAS CADASTRADAS DO USUÁRIO
    with st.expander("Minhas Vendas Cadastradas"):
        vendas_supabase = listar_vendas(st.session_state.usuario_info['id'])
        
        if vendas_supabase:
            df_vendas = pd.DataFrame(vendas_supabase)
            
            # Remove colunas desnecessárias para exibição
            colunas_para_remover = ['usuario_id', 'created_at', 'id']
            colunas_exibir = [col for col in df_vendas.columns if col not in colunas_para_remover]
            df_vendas_limpo = df_vendas[colunas_exibir]
            
            # Renomear colunas para português
            mapeamento_colunas = {
                'produto': 'Produto',
                'quantidade': 'Quantidade',
                'preco_unitario': 'Preço Unitário',
                'valor_total': 'Valor Total',
                'cliente': 'Cliente',
                'numero_nota': 'Nº Nota',
                'data_venda': 'Data'
            }
            
            df_vendas_exibicao = df_vendas_limpo.rename(columns=mapeamento_colunas)
            
            st.dataframe(df_vendas_exibicao, use_container_width=True, hide_index=True)
            st.info(f"Total de vendas cadastradas: {len(vendas_supabase)}")
        else:
            st.info("Nenhuma venda cadastrada ainda")

else:
    st.header("🔐 Login Necessário")
    st.info("Para cadastrar vendas manualmente no banco de dados, faça login na barra lateral")

st.markdown('---')
st.markdown('Projeto desenvolvido com Python, Streamlit e Supabase.')