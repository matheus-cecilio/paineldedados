import streamlit as st
import pandas as pd
import plotly.express as px
from core.invoice import generate_invoice_pdf
from core.supabase_db import (
    criar_usuario, autenticar_usuario,
    criar_planilha, adicionar_itens_planilha, listar_planilhas,
    obter_itens_planilha, excluir_planilha,
    add_item_planilha, excluir_itens_planilha, limpar_itens_planilha,
    renomear_planilha, atualizar_item_planilha, logout_usuario
)
from core.auth_manager import check_persistent_login, login_user, logout_user
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from datetime import datetime
import pytz
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

# Inicialização do estado da sessão
if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = False
if 'usuario_info' not in st.session_state:
    st.session_state.usuario_info = None

# Verificar login persistente usando cookies
if not st.session_state.usuario_logado:
    check_persistent_login()

# Função para logout
def logout():
    logout_user()
    st.rerun()

# Cabeçalho principal
st.title('📊 Painel de Vendas')

# Mostrar informações do usuário se logado
if st.session_state.usuario_logado:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.success(f"✅ Logado como: **{st.session_state.usuario_info['nome']}** ({st.session_state.usuario_info['email']})")
    with col2:
        if st.button('🚪 Logout'):
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
    - `cliente`: Nome do cliente
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

# Função para obter datetime brasileiro
def get_br_datetime():
    """Retorna datetime atual no fuso horário do Brasil"""
    br_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(br_tz)

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
        
        # Gerar PDF somente (não salva uploads no banco)
        if 'produto' in df_standardized.columns:
            st.subheader('Gerar PDF')
            colp2, _ = st.columns([2,3])

            with colp2:
                if 'cliente' in df_standardized.columns:
                    customers = df_standardized['cliente'].dropna().unique().tolist()
                    sel_customer = st.selectbox('Cliente para emitir PDF', options=customers)
                    if st.button('🧾 Gerar PDF desta planilha (upload)'):
                        items = df_standardized[df_standardized['cliente']==sel_customer].to_dict(orient='records')
                        items_for_pdf = []
                        for r in items:
                            items_for_pdf.append({
                                'description': r.get('produto', 'Produto'),
                                'quantity': r.get('quantidade', 1),
                                'unit_price': r.get('valor_unitario', r.get('preco_unitario', 0))
                            })
                        outdir = 'uploads'
                        os.makedirs(outdir, exist_ok=True)
                        invoice_no = get_br_datetime().strftime('%Y%m%d%H%M%S')
                        outpath = os.path.join(outdir, f'nota_{invoice_no}.pdf')
                        generate_invoice_pdf(invoice_no, sel_customer, items_for_pdf, outpath)
                        with open(outpath,'rb') as f:
                            pdf_data = f.read()
                        st.download_button('Baixar PDF', data=pdf_data, file_name=f'nota_{sel_customer}_{invoice_no}.pdf', mime='application/pdf')
                        st.success('✅ PDF gerado com sucesso!')
                else:
                    st.info("Coluna 'cliente' não encontrada para gerar PDF")
                
    except Exception as e:
        st.error(f'❌ Erro ao processar arquivo: {e}')

# SEÇÃO 2: LOGIN (somente se não logado)
if not st.session_state.usuario_logado:
    st.header("🔐 Login")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Entrar")
        with st.form("form_login"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            
            if submitted:
                if email and senha:
                    sucesso, mensagem = login_user(email, senha)
                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.rerun()
                    else:
                        st.error(f"❌ {mensagem}")
                else:
                    st.error("❌ Preencha todos os campos")
    
    with col2:
        st.subheader("Cadastrar")
        with st.form("form_cadastro"):
            nome_cad = st.text_input("Nome completo")
            email_cad = st.text_input("Email")
            senha_cad = st.text_input("Senha", type="password")
            submitted_cad = st.form_submit_button("Cadastrar")
            
            if submitted_cad:
                if nome_cad and email_cad and senha_cad:
                    sucesso, mensagem = criar_usuario(nome_cad, email_cad, senha_cad)
                    if sucesso:
                        st.success(f"✅ {mensagem}")
                        st.info("Agora você pode fazer login!")
                    else:
                        st.error(f"❌ {mensagem}")
                else:
                    st.error("❌ Preencha todos os campos")

# SEÇÃO 3: ÁREA DE PLANILHAS (somente se logado)
if st.session_state.usuario_logado:
    st.header('🗂️ Planilhas')

    tab_draft, tab_saved = st.tabs(["Rascunho", "Salvas"])

    # ---------------- RASCUNHO ----------------
    with tab_draft:
        # Estado do builder
        if 'planilha_builder' not in st.session_state:
            st.session_state.planilha_builder = {
                'planilha_id': None,
                'nome': '',
                'itens': []
            }

        colpb2 = st.columns(1)[0]
        novo_nome = colpb2.text_input('Criar nova planilha (rascunho): nome', value=st.session_state.planilha_builder.get('nome') or '')
        if colpb2.button('➕ Iniciar novo rascunho'):
            st.session_state.planilha_builder = {'planilha_id': None, 'nome': novo_nome, 'itens': []}
            st.success('Rascunho iniciado. Adicione itens abaixo.')
            st.rerun()

        # Formulário para adicionar item ao rascunho
        st.subheader('Adicionar item à planilha (rascunho)')
        cpi1, cpi2, cpi3 = st.columns(3)
        with cpi1:
            p_prod = st.text_input('Produto', key='pb_prod')
        with cpi2:
            p_qtd_text = st.text_input('Quantidade', value='', placeholder='ex: 2,5', key='pb_qtd')
        with cpi3:
            p_preco_text = st.text_input('Preço Unitário (R$)', value='', placeholder='ex: 19,90', key='pb_preco')
        cpi4, cpi5 = st.columns(2)
        with cpi4:
            p_cliente = st.text_input('Cliente (opcional)', key='pb_cli')
        with cpi5:
            p_data = st.date_input('Data', value=get_br_datetime().date(), format='DD/MM/YYYY', key='pb_data')

        if st.button('Adicionar ao rascunho'):
            # parse entradas texto
            def _to_float(txt):
                if txt is None:
                    return None
                s = str(txt).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                try:
                    return float(s)
                except Exception:
                    return None
            qtd_val = _to_float(p_qtd_text)
            preco_val = _to_float(p_preco_text)

            if p_prod and qtd_val and preco_val:
                st.session_state.planilha_builder['itens'].append({
                    'produto': p_prod,
                    'quantidade': float(qtd_val),
                    'preco_unitario': float(preco_val),
                    'valor_total': float(qtd_val) * float(preco_val),
                    'cliente': p_cliente or None,
                    'data': p_data.strftime('%Y-%m-%d')
                })
                st.success('Item adicionado ao rascunho')
                st.rerun()
            else:
                st.error('Preencha produto, quantidade e preço')

        # Interface simplificada para editar rascunho
        draft_items = st.session_state.planilha_builder['itens']
        items_to_remove = []  # Inicializar sempre, fora do if
        
        if draft_items:
            st.subheader('Editar itens do rascunho')
            
            # Lista de items para editar
            for i, item in enumerate(draft_items):
                with st.expander(f"Item {i+1}: {item.get('produto', 'Produto')} - R$ {item.get('valor_total', 0):.2f}"):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_produto = st.text_input('Produto:', value=item.get('produto', ''), key=f'edit_prod_{i}')
                        with c2:
                            new_qtd = st.text_input('Quantidade:', value=str(item.get('quantidade', '')), key=f'edit_qtd_{i}')
                        with c3:
                            new_preco = st.text_input('Preço:', value=str(item.get('preco_unitario', '')), key=f'edit_preco_{i}')
                    
                    with col2:
                        st.markdown("**Ações:**")
                        if st.button(f'🗑️ Excluir', key=f'del_{i}', type="secondary"):
                            items_to_remove.append(i)
                        
                        if st.button(f'💾 Salvar', key=f'save_{i}', type="primary"):
                            # Parse dos valores
                            def _parse_float(txt):
                                try:
                                    return float(str(txt).replace(',', '.').replace('R$', '').strip())
                                except:
                                    return 0.0
                            
                            qtd_parsed = _parse_float(new_qtd)
                            preco_parsed = _parse_float(new_preco)
                            
                            # Atualizar item
                            st.session_state.planilha_builder['itens'][i] = {
                                'produto': new_produto,
                                'quantidade': qtd_parsed,
                                'preco_unitario': preco_parsed,
                                'valor_total': float(qtd_parsed) * float(preco_parsed),
                                'cliente': item.get('cliente'),  # Manter cliente original
                                'data': item.get('data')  # Manter data original
                            }
                            st.success(f'Item {i+1} atualizado!')
                            st.rerun()
        
        # Processar exclusões
        if items_to_remove:
            for i in reversed(sorted(items_to_remove)):
                st.session_state.planilha_builder['itens'].pop(i)
            st.success(f'Removido(s) {len(items_to_remove)} item(ns)')
            st.rerun()
        
        # Resumo
        if draft_items:
            total_items = len(draft_items)
            total_valor = sum(item.get('valor_total', 0) for item in draft_items)
            st.info(f"**Resumo:** {total_items} itens - Valor total: R$ {total_valor:.2f}")

        sel2 = []  # Não usa mais AgGrid
        cba, cbb, cbc = st.columns(3)
        with cba:
            if st.button('Remover selecionados do rascunho'):
                if sel2:
                    idxs_to_remove = sorted([int(r.get('idx', -1)) for r in sel2 if r.get('idx') is not None], reverse=True)
                    for idx in idxs_to_remove:
                        if 0 <= idx < len(st.session_state.planilha_builder['itens']):
                            st.session_state.planilha_builder['itens'].pop(idx)
                    st.success(f"Removido(s) {len(idxs_to_remove)} item(ns) da lista")
                    st.rerun()
                else:
                    st.info('Selecione uma ou mais linhas para remover')
        with cbb:
            if st.button('Limpar rascunho'):
                st.session_state.planilha_builder['itens'] = []
                st.rerun()
        with cbc:
            clientes_draft = [c for c in pd.Series([r.get('cliente') for r in draft_items]).dropna().unique().tolist() if c]
            cliente_opts = ['Todos'] + clientes_draft if clientes_draft else ['Todos']
            selc = st.selectbox('Cliente para PDF (rascunho)', options=cliente_opts, key='pb_pdf_cli')
            if st.button('🧾 Gerar PDF do rascunho'):
                items_for_pdf = []
                for r in draft_items:
                    if selc == 'Todos' or r.get('cliente') == selc:
                        items_for_pdf.append({
                            'description': r.get('produto', 'Produto'),
                            'quantity': r.get('quantidade', 1),
                            'unit_price': r.get('preco_unitario', 0)
                        })
                outdir = 'uploads'
                os.makedirs(outdir, exist_ok=True)
                invoice_no = get_br_datetime().strftime('%Y%m%d%H%M%S')
                outpath = os.path.join(outdir, f'nota_{invoice_no}.pdf')
                title = st.session_state.planilha_builder.get('nome') or 'Todos'
                generate_invoice_pdf(invoice_no, title if selc=='Todos' else selc, items_for_pdf, outpath)
                with open(outpath,'rb') as f:
                    pdf_data = f.read()
                st.download_button('Baixar PDF', data=pdf_data, file_name=f'nota_{selc}_{invoice_no}.pdf', mime='application/pdf')
                st.success('✅ PDF gerado com sucesso!')

        st.markdown('---')
        csa, csb = st.columns(2)
        with csa:
            nome_save = st.text_input('Nome da planilha para salvar', value=st.session_state.planilha_builder.get('nome') or '')
            if st.button('💾 Salvar como NOVA planilha'):
                if not nome_save.strip():
                    st.error('Informe um nome')
                else:
                    uid = st.session_state.usuario_info['id']
                    ok, pid, msg = criar_planilha(uid, nome_save)
                    if ok and pid:
                        ok2, count, msg2 = adicionar_itens_planilha(uid, pid, st.session_state.planilha_builder['itens'])
                        if ok2:
                            st.success(f"Planilha criada, itens: {count}")
                            st.session_state.planilha_builder['planilha_id'] = pid
                            st.session_state.planilha_builder['nome'] = nome_save
                        else:
                            st.error(f"Planilha criada mas erro ao inserir itens: {msg2}")
                    else:
                        st.error(msg)
        with csb:
            plans_for_append = listar_planilhas(st.session_state.usuario_info['id'])
            options = ['(selecionar)'] + [p['nome'] for p in plans_for_append] if plans_for_append else ['(selecionar)']
            target = st.selectbox('Anexar rascunho à planilha', options=options)
            if st.button('➕ Anexar itens ao selecionado') and target != '(selecionar)':
                pid_append = next((p['id'] for p in plans_for_append if p['nome'] == target), None)
                if pid_append:
                    uid = st.session_state.usuario_info['id']
                    ok2, count, msg2 = adicionar_itens_planilha(uid, pid_append, st.session_state.planilha_builder['itens'])
                    if ok2:
                        st.success(f"Itens anexados: {count}")
                    else:
                        st.error(msg2)

    # ---------------- SALVAS ----------------
    with tab_saved:
        plans = listar_planilhas(st.session_state.usuario_info['id'])
        if not plans:
            st.info('Você ainda não tem planilhas salvas')
        else:
            sel = st.selectbox('Planilha', options=[p['nome'] for p in plans], index=0 if plans else None)
            if plans:
                pid = next((p['id'] for p in plans if p['nome'] == sel), None)
            else:
                pid = None
            nome_atual = next((p['nome'] for p in plans if p['id']==pid), '')
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                novo_nome = st.text_input('Renomear planilha', value=nome_atual)
                if st.button('✏️ Renomear') and novo_nome.strip():
                    ok, msg = renomear_planilha(st.session_state.usuario_info['id'], pid, novo_nome.strip())
                    st.success(msg) if ok else st.error(msg)
            with c2:
                if st.button('🗑️ Excluir planilha'):
                    ok, msg = excluir_planilha(st.session_state.usuario_info['id'], pid)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c3:
                # Adicionar item único
                st.markdown('Adicionar item rápido')
                ap_prod = st.text_input('Produto', key='ap_prod')
                ap_qtd_txt = st.text_input('Qtd', value='', placeholder='ex: 2,5', key='ap_qtd')
                ap_preco_txt = st.text_input('Preço', value='', placeholder='ex: 19,90', key='ap_preco')
                ap_cli = st.text_input('Cliente', key='ap_cli')
                ap_data = st.date_input('Data', value=get_br_datetime().date(), format='DD/MM/YYYY', key='ap_data')
                if st.button('Adicionar') and ap_prod:
                    def _to_float_saved(txt):
                        if txt is None:
                            return None
                        s = str(txt).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
                        try:
                            return float(s)
                        except Exception:
                            return None
                    qv = _to_float_saved(ap_qtd_txt)
                    pv = _to_float_saved(ap_preco_txt)
                    if qv and pv:
                        ok, item_id, msg = add_item_planilha(
                            st.session_state.usuario_info['id'], pid, ap_prod, float(qv), float(pv), ap_cli or None, ap_data.strftime('%Y-%m-%d')
                        )
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()
                    else:
                        st.error('Informe quantidade e preço válidos')

            # Itens da planilha - Interface simplificada
            itens = obter_itens_planilha(st.session_state.usuario_info['id'], pid)
            if not itens:
                st.info('Sem itens nesta planilha')
            else:
                st.subheader('Editar itens da planilha')
                
                # Mostrar items em expanders editáveis
                items_para_excluir = []
                for i, item in enumerate(itens):
                    item_id = item.get('id')
                    
                    # Calcular valor total dinamicamente baseado nos campos atuais
                    def _calc_total_display(qtd_val, preco_val):
                        def _parse_display_num(v):
                            if v is None or v == '':
                                return 0.0
                            s = str(v).replace('R$', '').strip()
                            
                            # Se contém vírgula, assume formato (vírgula = decimal)
                            if ',' in s:
                                # Remove pontos (milhares) e troca vírgula por ponto
                                s = s.replace('.', '').replace(',', '.')
                            # Se só tem ponto, verifica se é decimal ou milhares
                            elif '.' in s:
                                parts = s.split('.')
                                if len(parts) == 2 and len(parts[1]) <= 2:
                                    # Formato: 40.50 (decimal)
                                    pass  # já está correto
                                else:
                                    # Formato milhares: 1.000 
                                    s = s.replace('.', '')
                            
                            try:
                                return float(s)
                            except Exception:
                                return 0.0
                        
                        # Calcular o total multiplicando quantidade por preço
                        qtd_num = _parse_display_num(qtd_val)
                        preco_num = _parse_display_num(preco_val)
                        return qtd_num * preco_num
                    
                    # Usar valores dos campos de entrada se existirem, senão usar valores do banco
                    qtd_current = st.session_state.get(f'saved_qtd_{item_id}', str(item.get('quantidade', '')))
                    preco_current = st.session_state.get(f'saved_preco_{item_id}', str(item.get('preco_unitario', '')))
                    valor_total_atual = _calc_total_display(qtd_current, preco_current)
                    
                    # Garantir que valor_total_atual nunca seja None
                    if valor_total_atual is None:
                        valor_total_atual = 0.0
                    
                    with st.expander(f"Item {i+1}: {item.get('produto', 'Produto')} - R$ {valor_total_atual:.2f}"):
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                new_produto = st.text_input('Produto:', value=item.get('produto', ''), key=f'saved_prod_{item_id}')
                            with c2:
                                new_qtd = st.text_input('Quantidade:', value=str(item.get('quantidade', '')), key=f'saved_qtd_{item_id}')
                            with c3:
                                new_preco = st.text_input('Preço:', value=str(item.get('preco_unitario', '')), key=f'saved_preco_{item_id}')
                        
                        c4, c5 = st.columns(2)
                        with c4:
                            new_cliente = st.text_input('Cliente:', value=item.get('cliente', '') or '', key=f'saved_cli_{item_id}')
                        with c5:
                            try:
                                data_val = pd.to_datetime(item.get('data_venda')).date() if item.get('data_venda') else get_br_datetime().date()
                            except:
                                data_val = get_br_datetime().date()
                            new_data = st.date_input('Data:', value=data_val, key=f'saved_data_{item_id}')
                        
                        # Mostrar cálculo em tempo real
                        valor_calc = _calc_total_display(new_qtd, new_preco)
                        st.info(f"**Valor Total:** R$ {valor_calc:.2f}")
                    
                        with col2:
                            st.markdown("**Ações:**")
                            if st.button(f'💾 Salvar', key=f'save_saved_{item_id}', type="primary"):
                                # Parse e atualização
                                def _parse_num(v):
                                    if v is None or v == '':
                                        return 0.0
                                    s = str(v).replace('R$', '').strip()
                                    
                                    # Se contém vírgula, assume formato brasileiro (vírgula = decimal)
                                    if ',' in s:
                                        # Remove pontos (milhares) e troca vírgula por ponto
                                        s = s.replace('.', '').replace(',', '.')
                                    # Se só tem ponto, verifica se é decimal ou milhares
                                    elif '.' in s:
                                        parts = s.split('.')
                                        if len(parts) == 2 and len(parts[1]) <= 2:
                                            # Formato americano: 40.50 (decimal)
                                            pass  # já está correto
                                        else:
                                            # Formato milhares: 1.000 
                                            s = s.replace('.', '')
                                    
                                    try:
                                        return float(s)
                                    except Exception:
                                        return 0.0
                                
                                qtd = _parse_num(new_qtd)
                                preco = _parse_num(new_preco)
                                
                                try:
                                    data_val = new_data.strftime('%Y-%m-%d') if new_data else None
                                except:
                                    data_val = None
                                
                                ok, msg = atualizar_item_planilha(
                                    st.session_state.usuario_info['id'], pid, item_id,
                                    new_produto, qtd, preco, new_cliente, data_val
                                )
                                if ok:
                                    st.success('Item atualizado!')
                                    st.rerun()
                                else:
                                    st.error(msg)
                            
                            if st.button(f'🗑️ Excluir', key=f'del_saved_{item_id}', type="secondary"):
                                items_para_excluir.append(item_id)
                
                # Processar exclusões
                if items_para_excluir:
                    ok, count, msg = excluir_itens_planilha(st.session_state.usuario_info['id'], pid, items_para_excluir)
                    if ok:
                        st.success(f'{count} item(ns) removido(s)')
                        st.rerun()
                    else:
                        st.error(msg)
                
                # Ações em lote
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button('🗑️ Limpar todos os itens'):
                        ok, msg = limpar_itens_planilha(st.session_state.usuario_info['id'], pid)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                
                with col2:
                    # Resumo
                    total_items = len(itens)
                    total_valor = sum(item.get('valor_total', 0) for item in itens)
                    st.info(f"**Total:** {total_items} itens - R$ {total_valor:.2f}")
                
                with col3:
                    # PDF
                    clientes = [c for c in pd.DataFrame(itens)['cliente'].dropna().unique().tolist() if c]
                    opts = ['Todos'] + clientes if clientes else ['Todos']
                    selc2 = st.selectbox('Cliente p/ PDF', options=opts, key='saved_pdf_cli')
                    if st.button('🧾 Gerar PDF'):
                        items_for_pdf = []
                        for row in itens:
                            if selc2 == 'Todos' or row.get('cliente') == selc2:
                                items_for_pdf.append({
                                    'description': row.get('produto', 'Produto'),
                                    'quantity': row.get('quantidade', 1),
                                    'unit_price': row.get('preco_unitario', 0)
                                })
                        outdir = 'uploads'
                        os.makedirs(outdir, exist_ok=True)
                        invoice_no = get_br_datetime().strftime('%Y%m%d%H%M%S')
                        outpath = os.path.join(outdir, f'nota_{invoice_no}.pdf')
                        generate_invoice_pdf(invoice_no, nome_atual if selc2=='Todos' else selc2, items_for_pdf, outpath)
                        with open(outpath,'rb') as f:
                            pdf_data = f.read()
                        st.download_button('Baixar PDF', data=pdf_data, file_name=f'nota_{selc2}_{invoice_no}.pdf', mime='application/pdf')
                        st.success('✅ PDF gerado!')

st.markdown('---')
st.markdown('Projeto desenvolvido com Python, Streamlit e Supabase.')