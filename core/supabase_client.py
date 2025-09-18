import os
import socket
from urllib.parse import urlparse
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def _normalize_url(url: str) -> str:
    if not url:
        return url
    # remove trailing slash
    return url.rstrip('/')

def _validate_env(url: str, key: str):
    if not url or not key:
        raise Exception("Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env (veja .env.example)")
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise Exception("SUPABASE_URL inválida: deve começar com https://<projeto>.supabase.co")
    if not parsed.netloc:
        raise Exception("SUPABASE_URL inválida: hostname ausente")
    host = parsed.netloc
    try:
        # Verifica resolução DNS para evitar erro genérico [Errno -2]
        socket.gethostbyname(host)
    except Exception:
        raise Exception(f"Não foi possível resolver o host '{host}'. Verifique SUPABASE_URL em Project Settings → API (Project URL)")

def get_supabase() -> Client:
    _validate_env(SUPABASE_URL, SUPABASE_KEY)
    url = _normalize_url(SUPABASE_URL)
    # Criar cliente simples sem options problemáticas
    return create_client(url, SUPABASE_KEY)
