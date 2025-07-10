-- database/init.sql

-- Cria a tabela de produtos
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL
);

-- Opcional: Apaga os dados existentes e reinicia a sequência para um teste limpo e repetível
-- CUIDADO: Não use isso em produção se tiver dados importantes!
DELETE FROM products;
ALTER SEQUENCE products_id_seq RESTART WITH 1;

-- Insere 100.000 produtos fictícios
INSERT INTO products (name, description, price)
SELECT
    'Produto ' || LPAD(s::text, 6, '0'), -- Ex: 'Produto 000001'
    'Descrição detalhada para o produto ' || LPAD(s::text, 6, '0') || '. Um item fascinante e de alta qualidade.',
    (RANDOM() * 1000)::NUMERIC(10,2) -- Preço aleatório entre 0 e 1000
FROM generate_series(1, 100000) s; -- Altere para um número maior (ex: 1000000) se quiser mais dados

-- Importante: Atualiza as estatísticas do otimizador do PostgreSQL após a inserção em massa
ANALYZE products;

-- Mensagem opcional para verificar se a tabela e os dados foram criados
SELECT 'Tabela products criada e populada com sucesso!' AS status;