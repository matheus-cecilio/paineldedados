-- =====================================================
-- PAINEL DE VENDAS - VERSÃO COMPATÍVEL COM SUPABASE
-- =====================================================

-- Extensão para hash de senhas (em Supabase fica no schema "extensions")
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

-- Garantir acesso básico ao schema para roles de API do Supabase
DO $$
BEGIN
  -- Em ambientes Supabase, as roles são "anon" e "authenticated".
  -- Estes GRANTs evitam erros de "permission denied for schema public" ao invocar RPCs.
  BEGIN
    EXECUTE 'GRANT USAGE ON SCHEMA public TO anon';
  EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN
    EXECUTE 'GRANT USAGE ON SCHEMA public TO authenticated';
  EXCEPTION WHEN undefined_object THEN NULL; END;
END $$;

-- =====================================================
-- Tabelas principais
-- =====================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    email_canonico VARCHAR(255) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendas (
    id SERIAL PRIMARY KEY,
    produto VARCHAR(255) NOT NULL,
    quantidade DECIMAL(10,2) NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    valor_total DECIMAL(10,2) GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,
    cliente VARCHAR(255),
  numero_nota VARCHAR(255),
    data_venda DATE DEFAULT CURRENT_DATE,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Garante coluna numero_nota caso a tabela já exista sem ela
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS numero_nota VARCHAR(255);

-- Audit logins
CREATE TABLE IF NOT EXISTS audit_logins (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER,
  email_attempt VARCHAR(255),
  success BOOLEAN,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- Constraints e Índices
-- =====================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE c.conname = 'chk_vendas_qtde_positive'
      AND n.nspname = 'public'
      AND t.relname = 'vendas'
  ) THEN
    EXECUTE 'ALTER TABLE public.vendas ADD CONSTRAINT chk_vendas_qtde_positive CHECK (quantidade > 0)';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE c.conname = 'chk_vendas_preco_positive'
      AND n.nspname = 'public'
      AND t.relname = 'vendas'
  ) THEN
    EXECUTE 'ALTER TABLE public.vendas ADD CONSTRAINT chk_vendas_preco_positive CHECK (preco_unitario > 0)';
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email_canonico ON usuarios (email_canonico);
CREATE INDEX IF NOT EXISTS idx_vendas_usuario ON vendas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data_venda);

-- =====================================================
-- Trigger para manter email_canonico atualizado
-- =====================================================

CREATE OR REPLACE FUNCTION usuarios_email_canonico_trigger()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.email_canonico := LOWER(NEW.email);
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_usuarios_email_canonico ON usuarios;
CREATE TRIGGER trg_usuarios_email_canonico
BEFORE INSERT OR UPDATE ON usuarios
FOR EACH ROW EXECUTE FUNCTION usuarios_email_canonico_trigger();

-- Atualiza registros existentes
UPDATE usuarios
SET email_canonico = LOWER(email)
WHERE email IS NOT NULL
  AND (email_canonico IS NULL OR email_canonico <> LOWER(email));

-- =====================================================
-- Row Level Security (RLS) + Policies
-- =====================================================

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendas ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS usuarios_policy ON usuarios;
DROP POLICY IF EXISTS usuarios_signup ON usuarios;  
DROP POLICY IF EXISTS usuarios_login ON usuarios;
DROP POLICY IF EXISTS vendas_policy ON vendas;

CREATE POLICY usuarios_policy ON usuarios
  FOR ALL
  USING ( id = current_setting('app.user_id', true)::integer );

CREATE POLICY usuarios_signup ON usuarios
  FOR INSERT
  WITH CHECK ( true );

CREATE POLICY usuarios_login ON usuarios
  FOR SELECT
  USING ( id = current_setting('app.user_id', true)::integer );

CREATE POLICY vendas_policy ON vendas
  FOR ALL
  USING ( usuario_id = current_setting('app.user_id', true)::integer );

-- =====================================================
-- Funções (com checagem de app.user_id)
-- =====================================================

DROP FUNCTION IF EXISTS criar_usuario(text,text,text);
DROP FUNCTION IF EXISTS login_user(text,text);
DROP FUNCTION IF EXISTS login_user(text,text,inet,text);
DROP FUNCTION IF EXISTS get_usuarios_safe();
DROP FUNCTION IF EXISTS get_vendas_resumo(integer);
DROP FUNCTION IF EXISTS criar_venda(integer,text,numeric,numeric,text,text,date);
DROP FUNCTION IF EXISTS listar_vendas_user(integer);

-- Criar usuário
CREATE OR REPLACE FUNCTION criar_usuario(input_nome TEXT, input_email TEXT, input_senha TEXT)
RETURNS TABLE(success BOOLEAN, user_id INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
    new_user_id INTEGER;
BEGIN
    IF input_nome IS NULL OR btrim(input_nome) = '' THEN
      RETURN QUERY SELECT false, NULL::INTEGER, 'Nome inválido'::TEXT;
      RETURN;
    END IF;

    IF input_email IS NULL OR btrim(input_email) = '' THEN
      RETURN QUERY SELECT false, NULL::INTEGER, 'E-mail inválido'::TEXT;
      RETURN;
    END IF;

    IF input_senha IS NULL OR length(input_senha) < 6 THEN
      RETURN QUERY SELECT false, NULL::INTEGER, 'Senha muito curta (mín 6 caracteres)'::TEXT;
      RETURN;
    END IF;

    -- checar duplicado
    IF EXISTS (SELECT 1 FROM public.usuarios WHERE email_canonico = LOWER(input_email)) THEN
        RETURN QUERY SELECT false, NULL::INTEGER, 'E-mail já cadastrado'::TEXT;
        RETURN;
    END IF;

    INSERT INTO public.usuarios (nome, email, email_canonico, senha_hash)
    VALUES (
      input_nome,
      input_email,
      LOWER(input_email),
      extensions.crypt(input_senha, extensions.gen_salt('bf'))
    )
    RETURNING id INTO new_user_id;

    RETURN QUERY SELECT true, new_user_id, 'Usuário criado com sucesso'::TEXT;
END;
$$;

-- Login
CREATE OR REPLACE FUNCTION login_user(input_email TEXT, input_password TEXT, ip INET DEFAULT NULL, ua TEXT DEFAULT NULL)
RETURNS TABLE(success BOOLEAN, user_id INTEGER, user_name TEXT, user_email TEXT, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
    user_record RECORD;
    ok BOOLEAN := FALSE;
BEGIN
  SELECT * INTO user_record
  FROM public.usuarios
    WHERE email_canonico = LOWER(input_email);

  IF FOUND AND user_record.senha_hash = extensions.crypt(input_password, user_record.senha_hash) THEN
        ok := TRUE;
    END IF;

  INSERT INTO public.audit_logins (usuario_id, email_attempt, success, ip_address, user_agent)
    VALUES (CASE WHEN ok THEN user_record.id ELSE NULL END, input_email, ok, ip, ua);

  IF ok THEN
    RETURN QUERY SELECT true, user_record.id, user_record.nome::TEXT, user_record.email::TEXT, 'Login realizado com sucesso'::TEXT;
  ELSE
    RETURN QUERY SELECT false, NULL::INTEGER, NULL::TEXT, NULL::TEXT, 'E-mail ou senha incorretos'::TEXT;
  END IF;
END;
$$;

-- Usuário atual
CREATE OR REPLACE FUNCTION get_usuarios_safe()
RETURNS TABLE(id INTEGER, nome VARCHAR, email VARCHAR, created_at TIMESTAMP)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  sess_user TEXT := current_setting('app.user_id', true);
BEGIN
  IF sess_user IS NULL THEN
    RAISE EXCEPTION 'app.user_id não definido na sessão';
  END IF;

  RETURN QUERY
  SELECT u.id, u.nome, u.email, u.created_at
  FROM public.usuarios u
  WHERE u.id = sess_user::integer;
END;
$$;

-- Vendas por usuário
CREATE OR REPLACE FUNCTION get_vendas_resumo(user_id_param INTEGER)
RETURNS TABLE(
    id INTEGER, produto VARCHAR, quantidade DECIMAL, preco_unitario DECIMAL, 
    valor_total DECIMAL, cliente VARCHAR, data_venda DATE, 
    usuario_id INTEGER, usuario_nome VARCHAR
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  sess_user TEXT := current_setting('app.user_id', true);
BEGIN
  IF sess_user IS NULL THEN
    RAISE EXCEPTION 'app.user_id não definido na sessão';
  END IF;

  IF user_id_param IS DISTINCT FROM sess_user::integer THEN
    RAISE EXCEPTION 'user_id_param incompatível com app.user_id';
  END IF;

  RETURN QUERY
  SELECT v.id, v.produto, v.quantidade, v.preco_unitario, v.valor_total,
         v.cliente, v.data_venda, v.usuario_id, u.nome
  FROM public.vendas v
  JOIN public.usuarios u ON v.usuario_id = u.id
  WHERE v.usuario_id = sess_user::integer;
END;
$$;

-- =====================================================
-- RPCs seguras para criar e listar vendas sem depender de app.user_id
-- =====================================================

-- Criação de venda
CREATE OR REPLACE FUNCTION criar_venda(
  input_user_id INTEGER,
  input_produto TEXT,
  input_quantidade NUMERIC,
  input_preco NUMERIC,
  input_cliente TEXT DEFAULT NULL,
  input_numero_nota TEXT DEFAULT NULL,
  input_data DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(success BOOLEAN, id INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  new_id INTEGER;
BEGIN
  IF input_produto IS NULL OR btrim(input_produto) = '' THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Produto inválido'::TEXT; RETURN; END IF;
  IF input_quantidade IS NULL OR input_quantidade <= 0 THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Quantidade deve ser positiva'::TEXT; RETURN; END IF;
  IF input_preco IS NULL OR input_preco <= 0 THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Preço deve ser positivo'::TEXT; RETURN; END IF;

  INSERT INTO public.vendas (
    produto, quantidade, preco_unitario, cliente, numero_nota, data_venda, usuario_id
  ) VALUES (
    input_produto, input_quantidade, input_preco,
    NULLIF(input_cliente, ''), NULLIF(input_numero_nota, ''), COALESCE(input_data, CURRENT_DATE), input_user_id
  ) RETURNING public.vendas.id INTO new_id;

  RETURN QUERY SELECT true, new_id, 'Venda inserida com sucesso'::TEXT;
END;
$$;

-- Listagem de vendas por usuário
CREATE OR REPLACE FUNCTION listar_vendas_user(input_user_id INTEGER)
RETURNS TABLE(
  id INTEGER,
  produto VARCHAR,
  quantidade DECIMAL,
  preco_unitario DECIMAL,
  valor_total DECIMAL,
  cliente VARCHAR,
  numero_nota VARCHAR,
  data_venda DATE,
  usuario_id INTEGER,
  created_at TIMESTAMP
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
BEGIN
  RETURN QUERY
  SELECT v.id, v.produto, v.quantidade, v.preco_unitario, v.valor_total,
         v.cliente, v.numero_nota, v.data_venda, v.usuario_id, v.created_at
  FROM public.vendas v
  WHERE v.usuario_id = input_user_id
  ORDER BY v.data_venda DESC, v.id DESC;
END;
$$;

-- Conceder EXECUTE nas funções para roles de API
DO $$
BEGIN
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION criar_usuario(text,text,text) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION login_user(text,text,inet,text) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION get_usuarios_safe() TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION get_vendas_resumo(integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION criar_venda(integer,text,numeric,numeric,text,text,date) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION listar_vendas_user(integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
END $$;
-- ===================================================== 

-- =====================================================
-- Planilhas: metadados e itens
-- =====================================================

-- Tabela de planilhas do usuário
CREATE TABLE IF NOT EXISTS planilhas (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  arquivo_original TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de itens de cada planilha
CREATE TABLE IF NOT EXISTS planilha_itens (
  id SERIAL PRIMARY KEY,
  planilha_id INTEGER NOT NULL REFERENCES planilhas(id) ON DELETE CASCADE,
  produto TEXT NOT NULL,
  quantidade DECIMAL(10,2) NOT NULL,
  preco_unitario DECIMAL(10,2) NOT NULL,
  valor_total DECIMAL(10,2) GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,
  cliente TEXT,
  data_venda DATE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_planilhas_usuario ON planilhas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_planilha_itens_planilha ON planilha_itens(planilha_id);

-- RLS (opcional); funções usam SECURITY DEFINER
ALTER TABLE planilhas ENABLE ROW LEVEL SECURITY;
ALTER TABLE planilha_itens ENABLE ROW LEVEL SECURITY;

-- Funções RPC para planilhas
DROP FUNCTION IF EXISTS criar_planilha(integer,text,text);
DROP FUNCTION IF EXISTS adicionar_itens_planilha(integer,integer,jsonb);
DROP FUNCTION IF EXISTS listar_planilhas_user(integer);
DROP FUNCTION IF EXISTS obter_itens_planilha(integer,integer);
DROP FUNCTION IF EXISTS excluir_planilha(integer,integer);
DROP FUNCTION IF EXISTS excluir_itens_planilha(integer,integer,integer[]);
DROP FUNCTION IF EXISTS limpar_itens_planilha(integer,integer);
DROP FUNCTION IF EXISTS add_item_planilha(integer,integer,text,numeric,numeric,text,date);
DROP FUNCTION IF EXISTS renomear_planilha(integer,integer,text);
DROP FUNCTION IF EXISTS atualizar_item_planilha(integer,integer,integer,text,numeric,numeric,text,date);

-- Criar planilha
CREATE OR REPLACE FUNCTION criar_planilha(
  input_user_id INTEGER,
  input_nome TEXT,
  input_arquivo TEXT DEFAULT NULL
) RETURNS TABLE(success BOOLEAN, planilha_id INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  new_id INTEGER;
BEGIN
  IF input_user_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Usuário inválido'::TEXT; RETURN; END IF;
  IF input_nome IS NULL OR btrim(input_nome) = '' THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Nome da planilha inválido'::TEXT; RETURN; END IF;

  INSERT INTO public.planilhas (usuario_id, nome, arquivo_original)
  VALUES (input_user_id, input_nome, NULLIF(input_arquivo,''))
  RETURNING public.planilhas.id INTO new_id;

  RETURN QUERY SELECT true, new_id, 'Planilha criada com sucesso'::TEXT;
END;
$$;

-- Adicionar itens em massa (items é um array JSON de objetos)
CREATE OR REPLACE FUNCTION adicionar_itens_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER,
  items JSONB
) RETURNS TABLE(success BOOLEAN, inserted_count INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  cnt INTEGER := 0;
  owner_ok BOOLEAN;
BEGIN
  IF input_user_id IS NULL OR input_planilha_id IS NULL THEN
    RETURN QUERY SELECT false, 0, 'Parâmetros inválidos'::TEXT; RETURN; END IF;

  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;

  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 0, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  IF items IS NULL OR jsonb_typeof(items) <> 'array' THEN
    RETURN QUERY SELECT false, 0, 'Itens inválidos'::TEXT; RETURN; END IF;

  INSERT INTO public.planilha_itens (planilha_id, produto, quantidade, preco_unitario, cliente, data_venda)
  SELECT input_planilha_id,
         t.produto,
         COALESCE(t.quantidade, 0)::DECIMAL(10,2),
         COALESCE(COALESCE(t.preco_unitario, t.valor_unitario), 0)::DECIMAL(10,2),
         NULLIF(t.cliente, ''),
         COALESCE(t.data_venda, t.data)
  FROM jsonb_to_recordset(items) AS t(
    produto TEXT,
    quantidade NUMERIC,
    preco_unitario NUMERIC,
    valor_unitario NUMERIC,
    cliente TEXT,
    data_venda DATE,
    data DATE
  );

  GET DIAGNOSTICS cnt = ROW_COUNT;
  RETURN QUERY SELECT true, COALESCE(cnt,0), 'Itens adicionados'::TEXT;
END;
$$;

-- Listar planilhas do usuário
CREATE OR REPLACE FUNCTION listar_planilhas_user(
  input_user_id INTEGER
) RETURNS TABLE(id INTEGER, nome TEXT, arquivo_original TEXT, created_at TIMESTAMP)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
BEGIN
  RETURN QUERY
  SELECT p.id, p.nome, p.arquivo_original, p.created_at
  FROM public.planilhas p
  WHERE p.usuario_id = input_user_id
  ORDER BY p.created_at DESC, p.id DESC;
END;
$$;

-- Obter itens da planilha (somente do dono)
CREATE OR REPLACE FUNCTION obter_itens_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER
) RETURNS TABLE(
  id INTEGER,
  produto TEXT,
  quantidade DECIMAL,
  preco_unitario DECIMAL,
  valor_total DECIMAL,
  cliente TEXT,
  data_venda DATE
)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RAISE EXCEPTION 'Planilha não pertence ao usuário';
  END IF;

  RETURN QUERY
  SELECT i.id, i.produto, i.quantidade, i.preco_unitario, i.valor_total, i.cliente, i.data_venda
  FROM public.planilha_itens i
  WHERE i.planilha_id = input_planilha_id
  ORDER BY i.data_venda NULLS LAST, i.id;
END;
$$;

-- Excluir planilha (cascade apaga itens)
CREATE OR REPLACE FUNCTION excluir_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER
) RETURNS TABLE(success BOOLEAN, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;

  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  DELETE FROM public.planilhas WHERE id = input_planilha_id;
  RETURN QUERY SELECT true, 'Planilha excluída com sucesso'::TEXT;
END;
$$;

-- Excluir itens selecionados da planilha
CREATE OR REPLACE FUNCTION excluir_itens_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER,
  input_item_ids INTEGER[]
) RETURNS TABLE(success BOOLEAN, deleted_count INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
  del_cnt INTEGER := 0;
BEGIN
  IF input_item_ids IS NULL OR array_length(input_item_ids,1) IS NULL THEN
    RETURN QUERY SELECT false, 0, 'Nenhum item selecionado'::TEXT; RETURN; END IF;

  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 0, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  DELETE FROM public.planilha_itens i
  WHERE i.planilha_id = input_planilha_id
    AND i.id = ANY(input_item_ids);

  GET DIAGNOSTICS del_cnt = ROW_COUNT;
  RETURN QUERY SELECT true, COALESCE(del_cnt,0), 'Itens excluídos'::TEXT;
END;
$$;

-- Limpar todos os itens da planilha
CREATE OR REPLACE FUNCTION limpar_itens_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER
) RETURNS TABLE(success BOOLEAN, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  DELETE FROM public.planilha_itens WHERE planilha_id = input_planilha_id;
  RETURN QUERY SELECT true, 'Todos os itens foram removidos'::TEXT;
END;
$$;

-- Adicionar item único a uma planilha
CREATE OR REPLACE FUNCTION add_item_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER,
  input_produto TEXT,
  input_quantidade NUMERIC,
  input_preco NUMERIC,
  input_cliente TEXT DEFAULT NULL,
  input_data DATE DEFAULT NULL
) RETURNS TABLE(success BOOLEAN, item_id INTEGER, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
  new_id INTEGER;
BEGIN
  IF input_user_id IS NULL OR input_planilha_id IS NULL THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Parâmetros inválidos'::TEXT; RETURN; END IF;
  IF input_produto IS NULL OR btrim(input_produto) = '' THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Produto inválido'::TEXT; RETURN; END IF;
  IF input_quantidade IS NULL OR input_quantidade <= 0 THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Quantidade deve ser positiva'::TEXT; RETURN; END IF;
  IF input_preco IS NULL OR input_preco <= 0 THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Preço deve ser positivo'::TEXT; RETURN; END IF;

  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, NULL::INTEGER, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  INSERT INTO public.planilha_itens (planilha_id, produto, quantidade, preco_unitario, cliente, data_venda)
  VALUES (input_planilha_id, input_produto, input_quantidade, input_preco, NULLIF(input_cliente,''), input_data)
  RETURNING id INTO new_id;

  RETURN QUERY SELECT true, new_id, 'Item adicionado'::TEXT;
END;
$$;

-- Renomear planilha
CREATE OR REPLACE FUNCTION renomear_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER,
  input_novo_nome TEXT
) RETURNS TABLE(success BOOLEAN, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
BEGIN
  IF input_novo_nome IS NULL OR btrim(input_novo_nome) = '' THEN
    RETURN QUERY SELECT false, 'Nome inválido'::TEXT; RETURN; END IF;
  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  UPDATE public.planilhas SET nome = input_novo_nome WHERE id = input_planilha_id;
  RETURN QUERY SELECT true, 'Planilha renomeada'::TEXT;
END;
$$;

-- Atualizar um item de uma planilha salva
CREATE OR REPLACE FUNCTION atualizar_item_planilha(
  input_user_id INTEGER,
  input_planilha_id INTEGER,
  input_item_id INTEGER,
  input_produto TEXT,
  input_quantidade NUMERIC,
  input_preco NUMERIC,
  input_cliente TEXT DEFAULT NULL,
  input_data DATE DEFAULT NULL
) RETURNS TABLE(success BOOLEAN, message TEXT)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
  owner_ok BOOLEAN;
  belongs_ok BOOLEAN;
BEGIN
  SELECT EXISTS(
    SELECT 1 FROM public.planilhas p WHERE p.id = input_planilha_id AND p.usuario_id = input_user_id
  ) INTO owner_ok;
  IF NOT owner_ok THEN
    RETURN QUERY SELECT false, 'Planilha não pertence ao usuário'::TEXT; RETURN; END IF;

  SELECT EXISTS(
    SELECT 1 FROM public.planilha_itens i WHERE i.id = input_item_id AND i.planilha_id = input_planilha_id
  ) INTO belongs_ok;
  IF NOT belongs_ok THEN
    RETURN QUERY SELECT false, 'Item não pertence à planilha'::TEXT; RETURN; END IF;

  IF input_produto IS NULL OR btrim(input_produto) = '' THEN
    RETURN QUERY SELECT false, 'Produto inválido'::TEXT; RETURN; END IF;
  IF input_quantidade IS NULL OR input_quantidade <= 0 THEN
    RETURN QUERY SELECT false, 'Quantidade deve ser positiva'::TEXT; RETURN; END IF;
  IF input_preco IS NULL OR input_preco <= 0 THEN
    RETURN QUERY SELECT false, 'Preço deve ser positivo'::TEXT; RETURN; END IF;

  UPDATE public.planilha_itens
  SET produto = input_produto,
      quantidade = input_quantidade,
      preco_unitario = input_preco,
      cliente = NULLIF(input_cliente, ''),
      data_venda = input_data
  WHERE id = input_item_id;

  RETURN QUERY SELECT true, 'Item atualizado'::TEXT;
END;
$$;

-- Grants
DO $$
BEGIN
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION criar_planilha(integer,text,text) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION adicionar_itens_planilha(integer,integer,jsonb) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION listar_planilhas_user(integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION obter_itens_planilha(integer,integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION excluir_planilha(integer,integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION excluir_itens_planilha(integer,integer,integer[]) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION limpar_itens_planilha(integer,integer) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION add_item_planilha(integer,integer,text,numeric,numeric,text,date) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION renomear_planilha(integer,integer,text) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
  BEGIN EXECUTE 'GRANT EXECUTE ON FUNCTION atualizar_item_planilha(integer,integer,integer,text,numeric,numeric,text,date) TO anon, authenticated'; EXCEPTION WHEN undefined_object THEN NULL; END;
END $$;
