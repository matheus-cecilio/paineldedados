from core.supabase_client import get_supabase

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
        response = supabase.rpc('criar_usuario', {
            'input_nome': nome,
            'input_email': email,
            'input_senha': senha
        }).execute()
        
        if response.data and len(response.data) > 0 and response.data[0]['success']:
            return True, response.data[0]['message']
        else:
            message = response.data[0]['message'] if response.data and len(response.data) > 0 else "Erro desconhecido"
            return False, message
    except Exception as e:
        return False, f"Erro: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica usuário usando função segura do banco"""
    try:
        supabase = get_supabase()
        
        # Usar a função login_user do banco
        response = supabase.rpc('login_user', {
            'input_email': email,
            'input_password': senha
        }).execute()
        
        if response.data and len(response.data) > 0 and response.data[0]['success']:
            user = {
                'id': response.data[0]['user_id'],
                'nome': response.data[0]['user_name'],
                'email': response.data[0]['user_email']
            }
            return True, user, response.data[0]['message']
        else:
            message = response.data[0]['message'] if response.data and len(response.data) > 0 else "E-mail ou senha incorretos"
            return False, None, message
    except Exception as e:
        return False, None, f"Erro: {str(e)}"

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
