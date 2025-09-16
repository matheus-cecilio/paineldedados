-- ARQUIVO ÚNICO E SIMPLES PARA CRIAR TUDO
-- Execute no SQL Editor do Supabase
-- 1. Criar tabela de usuários
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Criar tabela de vendas
CREATE TABLE vendas (
    id SERIAL PRIMARY KEY,
    produto VARCHAR(255) NOT NULL,
    quantidade DECIMAL(10,2) NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    valor_total DECIMAL(10,2) GENERATED ALWAYS AS (quantidade * preco_unitario) STORED,
    cliente VARCHAR(255),
    numero_nota VARCHAR(100),
    data_venda DATE,
    usuario_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Habilitar RLS
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendas ENABLE ROW LEVEL SECURITY;

-- 4. Política SIMPLES: usuários só veem próprios dados
CREATE POLICY "usuarios_own_data" ON usuarios FOR ALL
USING (id = current_setting('app.user_id')::integer)
WITH CHECK (id = current_setting('app.user_id')::integer);

CREATE POLICY "vendas_own_data" ON vendas FOR ALL  
USING (usuario_id = current_setting('app.user_id')::integer)
WITH CHECK (usuario_id = current_setting('app.user_id')::integer);

-- 5. Políticas para permitir cadastro e login
CREATE POLICY "allow_signup" ON usuarios FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_login_check" ON usuarios FOR SELECT
USING (true);

-- 6. VIEW SEM SENHAS (para usar no app)
CREATE VIEW usuarios_safe AS
SELECT id, nome, email, created_at 
FROM usuarios;

-- 7. Função para login seguro
CREATE OR REPLACE FUNCTION login_user(input_email TEXT, input_password TEXT)
RETURNS TABLE(success BOOLEAN, user_id INTEGER, user_name TEXT, user_email TEXT)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
    user_record RECORD;
BEGIN
    SELECT * INTO user_record FROM usuarios WHERE email = input_email AND senha = input_password;
    
    IF FOUND THEN
        RETURN QUERY SELECT true, user_record.id, user_record.nome, user_record.email;
    ELSE
        RETURN QUERY SELECT false, NULL::INTEGER, NULL::TEXT, NULL::TEXT;
    END IF;
END;
$$;
