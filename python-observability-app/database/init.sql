-- database/init.sql

-- Cria a tabela de produtos
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL
);

-- Insere alguns dados de exemplo
INSERT INTO products (name, description, price) VALUES
    ('Monitor UltraWide', 'Monitor de 34 polegadas, resolução 2560x1080.', 799.99),
    ('Teclado Mecânico', 'Teclado com switches Cherry MX Blue e RGB.', 129.50),
    ('Mouse Gamer', 'Mouse com sensor óptico de alta precisão e 12 botões programáveis.', 59.90),
    ('Webcam Full HD', 'Webcam com resolução 1080p a 60fps.', 85.00),
    ('Headset Surround 7.1', 'Fone de ouvido com áudio surround virtual 7.1 e microfone retrátil.', 150.00);

-- Mensagem opcional para verificar se a tabela e os dados foram criados
SELECT 'Tabela products criada e dados inseridos com sucesso!' AS status;
