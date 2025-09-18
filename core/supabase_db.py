from core.supabase_client import get_supabase
import streamlit as st

def inserir_venda(produto, quantidade, preco_unitario, cliente=None, numero_nota=None, data=None, usuario_id=None):
    """Insere uma venda via RPC segura (SECURITY DEFINER)."""
    try:
        supabase = get_supabase()

        payload = {
            'input_user_id': usuario_id,
            'input_produto': produto,
            'input_quantidade': quantidade,
            'input_preco': preco_unitario,
            'input_cliente': cliente,
            'input_numero_nota': numero_nota,
            'input_data': data
        }

        response = supabase.rpc('criar_venda', payload).execute()
        if response.data and len(response.data) > 0 and response.data[0].get('success'):
            return True, response.data[0].get('message', 'Venda inserida com sucesso')
        else:
            msg = None
            if response.data and len(response.data) > 0:
                msg = response.data[0].get('message')
            return False, msg or 'Falha ao inserir venda'
    except Exception as e:
        return False, f"Erro ao inserir venda: {str(e)}"

def listar_vendas(usuario_id=None):
    """Lista vendas do usuário via RPC segura (SECURITY DEFINER)."""
    try:
        supabase = get_supabase()

        if not usuario_id:
            return []

        response = supabase.rpc('listar_vendas_user', {
            'input_user_id': usuario_id
        }).execute()
        return response.data or []
    except Exception as e:
        print(f"Erro ao listar vendas: {e}")
        return []

def criar_usuario(nome, email, senha):
    """Cria usuário usando função segura do banco"""
    try:
        supabase = get_supabase()
        
        # Usar a função criar_usuario do banco
        try:
            response = supabase.rpc('criar_usuario', {
                'input_nome': nome,
                'input_email': email,
                'input_senha': senha
            }).execute()
        except Exception as rpc_error:
            print(f"Erro na chamada RPC criar_usuario: {str(rpc_error)}")
            return False, f"Erro de conexão com banco: {str(rpc_error)}"
        
        # Tratar diferentes tipos de resposta
        data = None
        if hasattr(response, 'data'):
            data = response.data
        elif isinstance(response, dict) and 'data' in response:
            data = response['data']
        elif isinstance(response, list):
            data = response
        else:
            print(f"Tipo de resposta inesperado no criar_usuario: {type(response)}")
            print(f"Conteúdo da resposta: {response}")
            return False, "Formato de resposta inesperado"
        
        # Verificar se temos dados válidos
        if data and len(data) > 0:
            primeiro_item = data[0]
            if isinstance(primeiro_item, dict) and primeiro_item.get('success'):
                return True, primeiro_item.get('message', 'Usuário criado com sucesso!')
            else:
                message = primeiro_item.get('message', 'Erro ao criar usuário') if isinstance(primeiro_item, dict) else 'Erro desconhecido'
                return False, message
        else:
            return False, "Resposta vazia do servidor"
            
    except Exception as e:
        print(f"Erro geral ao criar usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Erro inesperado: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica usuário usando função segura do banco"""
    try:
        supabase = get_supabase()
        
        # Usar a função login_user do banco
        try:
            response = supabase.rpc('login_user', {
                'input_email': email,
                'input_password': senha
            }).execute()
        except Exception as rpc_error:
            print(f"Erro na chamada RPC: {str(rpc_error)}")
            return False, None, f"Erro de conexão com banco: {str(rpc_error)}"
        
        # Tratar diferentes tipos de resposta
        data = None
        if hasattr(response, 'data'):
            data = response.data
        elif isinstance(response, dict) and 'data' in response:
            data = response['data']
        elif isinstance(response, list):
            data = response
        else:
            print(f"Tipo de resposta inesperado: {type(response)}")
            print(f"Conteúdo da resposta: {response}")
            return False, None, "Formato de resposta inesperado"
        
        # Verificar se temos dados válidos
        if data and len(data) > 0:
            primeiro_item = data[0]
            if isinstance(primeiro_item, dict) and primeiro_item.get('success'):
                user = {
                    'id': primeiro_item.get('user_id'),
                    'nome': primeiro_item.get('user_name', 'Usuário'),
                    'email': primeiro_item.get('user_email', email)
                }
                # Salva no session state para manter login após reload
                st.session_state.user_authenticated = True
                st.session_state.user_id = user['id']
                st.session_state.user_email = user['email']
                st.session_state.user_nome = user['nome']
                
                return True, user, primeiro_item.get('message', 'Login realizado com sucesso!')
            else:
                message = primeiro_item.get('message', 'E-mail ou senha incorretos') if isinstance(primeiro_item, dict) else 'Credenciais inválidas'
                return False, None, message
        else:
            return False, None, "Resposta vazia do servidor"
            
    except Exception as e:
        print(f"Erro geral na autenticação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, f"Erro inesperado: {str(e)}"

def logout_usuario():
    """Faz logout e limpa a sessão"""
    # Limpa o session state
    if 'user_authenticated' in st.session_state:
        del st.session_state.user_authenticated
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'user_email' in st.session_state:
        del st.session_state.user_email
    if 'user_nome' in st.session_state:
        del st.session_state.user_nome

# -------------------------------
# Planilhas (metadados e itens)
# -------------------------------

def criar_planilha(usuario_id, nome, arquivo_original=None):
    """Cria uma planilha vinculada ao usuário."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('criar_planilha', {
            'input_user_id': usuario_id,
            'input_nome': nome,
            'input_arquivo': arquivo_original
        }).execute()

        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('planilha_id'), resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao criar planilha'
        return False, None, msg
    except Exception as e:
        return False, None, f"Erro: {str(e)}"

def adicionar_itens_planilha(usuario_id, planilha_id, itens):
    """Adiciona itens em massa (lista de dicts) a uma planilha."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('adicionar_itens_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id,
            'items': itens
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('inserted_count', 0), resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao adicionar itens'
        return False, 0, msg
    except Exception as e:
        return False, 0, f"Erro: {str(e)}"

def listar_planilhas(usuario_id):
    """Lista planilhas do usuário."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('listar_planilhas_user', {
            'input_user_id': usuario_id
        }).execute()
        return resp.data or []
    except Exception as e:
        print(f"Erro ao listar planilhas: {e}")
        return []

def obter_itens_planilha(usuario_id, planilha_id):
    """Obtém itens de uma planilha do usuário."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('obter_itens_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id
        }).execute()
        return resp.data or []
    except Exception as e:
        print(f"Erro ao obter itens da planilha: {e}")
        return []

def excluir_planilha(usuario_id, planilha_id):
    """Exclui uma planilha do usuário."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('excluir_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao excluir planilha'
        return False, msg
    except Exception as e:
        return False, f"Erro: {str(e)}"

def add_item_planilha(usuario_id, planilha_id, produto, quantidade, preco, cliente=None, data=None):
    """Adiciona um único item a uma planilha existente."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('add_item_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id,
            'input_produto': produto,
            'input_quantidade': quantidade,
            'input_preco': preco,
            'input_cliente': cliente,
            'input_data': data
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('item_id'), resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao adicionar item'
        return False, None, msg
    except Exception as e:
        return False, None, f"Erro: {str(e)}"

def excluir_itens_planilha(usuario_id, planilha_id, item_ids):
    """Exclui itens selecionados de uma planilha."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('excluir_itens_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id,
            'input_item_ids': item_ids
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('deleted_count'), resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao excluir itens'
        return False, 0, msg
    except Exception as e:
        return False, 0, f"Erro: {str(e)}"

def limpar_itens_planilha(usuario_id, planilha_id):
    """Remove todos os itens de uma planilha."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('limpar_itens_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao limpar planilha'
        return False, msg
    except Exception as e:
        return False, f"Erro: {str(e)}"

def renomear_planilha(usuario_id, planilha_id, novo_nome):
    """Renomeia uma planilha do usuário."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('renomear_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id,
            'input_novo_nome': novo_nome
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao renomear planilha'
        return False, msg
    except Exception as e:
        return False, f"Erro: {str(e)}"

def atualizar_item_planilha(usuario_id, planilha_id, item_id, produto, quantidade, preco, cliente=None, data=None):
    """Atualiza um item já salvo em uma planilha."""
    try:
        supabase = get_supabase()
        resp = supabase.rpc('atualizar_item_planilha', {
            'input_user_id': usuario_id,
            'input_planilha_id': planilha_id,
            'input_item_id': item_id,
            'input_produto': produto,
            'input_quantidade': quantidade,
            'input_preco': preco,
            'input_cliente': cliente,
            'input_data': data
        }).execute()
        if resp.data and len(resp.data) > 0 and resp.data[0].get('success'):
            return True, resp.data[0].get('message')
        msg = resp.data[0].get('message') if resp.data else 'Falha ao atualizar item'
        return False, msg
    except Exception as e:
        return False, f"Erro: {str(e)}"


