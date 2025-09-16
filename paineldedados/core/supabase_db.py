from core.supabase_client import get_supabase
import hashlib

def hash_senha(senha):
    """Cria hash SHA256 da senha"""
    return hashlib.sha256(senha.encode()).hexdigest()

def inserir_venda(produto, quantidade, preco_unitario, cliente=None, numero_nota=None, data=None, usuario_id=None):
    """Insere uma venda no Supabase"""
    try:
        supabase = get_supabase()
        valor_total = quantidade * preco_unitario
        
        data_venda = {
            'produto': produto,
            'quantidade': quantidade,
            'preco_unitario': preco_unitario,
            'valor_total': valor_total,
            'cliente': cliente,
            'numero_nota': numero_nota,
            'data_venda': data,
            'usuario_id': usuario_id
        }
        
        response = supabase.table('vendas').insert(data_venda).execute()
        return True, "Venda inserida com sucesso"
    except Exception as e:
        return False, f"Erro ao inserir venda: {str(e)}"

def listar_vendas(usuario_id=None):
    """Lista vendas do usuário"""
    try:
        supabase = get_supabase()
        if usuario_id:
            response = supabase.table('vendas').select('*').eq('usuario_id', usuario_id).execute()
        else:
            response = supabase.table('vendas').select('*').execute()
        return response.data
    except Exception as e:
        return []

def criar_usuario(nome, email, senha):
    """Cria usuário com senha hasheada"""
    try:
        supabase = get_supabase()
        
        # Verifica se já existe
        response = supabase.table('usuarios_safe').select('email').eq('email', email).execute()
        if response.data:
            return False, "E-mail já cadastrado"
        
        # Cria com senha hasheada
        novo_usuario = {
            'nome': nome,
            'email': email,
            'senha': hash_senha(senha)
        }
        
        response = supabase.table('usuarios').insert(novo_usuario).execute()
        return True, "Usuário criado com sucesso"
    except Exception as e:
        return False, f"Erro: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica usuário"""
    try:
        supabase = get_supabase()
        senha_hash = hash_senha(senha)
        
        # Usa função do banco para login seguro
        response = supabase.rpc('login_user', {
            'input_email': email,
            'input_password': senha_hash
        }).execute()
        
        if response.data and response.data[0]['success']:
            user = {
                'id': response.data[0]['user_id'],
                'nome': response.data[0]['user_name'],
                'email': response.data[0]['user_email']
            }
            return True, user, "Login realizado com sucesso"
        else:
            return False, None, "E-mail ou senha incorretos"
    except Exception as e:
        return False, None, f"Erro: {str(e)}"
