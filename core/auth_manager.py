import streamlit as st
import extra_streamlit_components as stx
import json
import hashlib
from datetime import datetime, timedelta
from core.supabase_db import autenticar_usuario

# Configurar o cookie manager
cookie_manager = stx.CookieManager()

def get_cookie_name():
    """Nome do cookie para autenticação"""
    return "painel_vendas_auth"

def create_auth_token(user_info):
    """Cria um token de autenticação seguro"""
    # Criar um hash simples com informações do usuário + timestamp
    data = {
        'user_id': user_info['id'],
        'email': user_info['email'],
        'nome': user_info['nome'],
        'timestamp': datetime.now().isoformat()
    }
    return json.dumps(data)

def save_auth_cookie(user_info, days=2):
    """Salva as informações de login no cookie"""
    try:
        token = create_auth_token(user_info)
        cookie_manager.set(
            cookie=get_cookie_name(),
            val=token,
            expires_at=datetime.now() + timedelta(days=days)
        )
        return True
    except Exception as e:
        print(f"Erro ao salvar cookie: {e}")
        return False

def load_auth_cookie():
    """Carrega as informações de login do cookie"""
    try:
        token = cookie_manager.get(cookie=get_cookie_name())
        if token:
            data = json.loads(token)
            # Verificar se o token não está muito antigo (2 dias)
            token_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - token_time < timedelta(days=2):
                return data
        return None
    except Exception as e:
        print(f"Erro ao carregar cookie: {e}")
        return None

def clear_auth_cookie():
    """Remove o cookie de autenticação"""
    try:
        cookie_manager.delete(cookie=get_cookie_name())
        return True
    except Exception as e:
        print(f"Erro ao limpar cookie: {e}")
        return False

def check_persistent_login():
    """Verifica se há login persistente e restaura se necessário"""
    # Primeiro verificar session_state
    if st.session_state.get('usuario_logado', False):
        return True
    
    # Se não há login no session_state, verificar cookie
    auth_data = load_auth_cookie()
    if auth_data:
        # Restaurar login no session_state
        st.session_state.usuario_logado = True
        st.session_state.usuario_info = {
            'id': auth_data['user_id'],
            'email': auth_data['email'],
            'nome': auth_data['nome']
        }
        
        # Também salvar nas chaves antigas para compatibilidade
        st.session_state.user_authenticated = True
        st.session_state.user_id = auth_data['user_id']
        st.session_state.user_email = auth_data['email']
        st.session_state.user_nome = auth_data['nome']
        
        return True
    
    return False

def login_user(email, senha):
    """Faz login e salva nos cookies para persistência"""
    sucesso, usuario, mensagem = autenticar_usuario(email, senha)
    
    if sucesso:
        # Salvar no session_state
        st.session_state.usuario_logado = True
        st.session_state.usuario_info = usuario
        
        # Salvar no cookie para persistência
        save_auth_cookie(usuario)
        
        return True, mensagem
    else:
        return False, mensagem

def logout_user():
    """Faz logout e limpa session_state + cookies"""
    # Limpar session_state
    keys_to_clear = [
        'usuario_logado', 'usuario_info', 'user_authenticated', 
        'user_id', 'user_email', 'user_nome', 'lista_vendas'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Limpar cookie
    clear_auth_cookie()
    
    return True