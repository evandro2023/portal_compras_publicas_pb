import duckdb
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "compras_pb.duckdb")

def setup_usuarios_db():
    conn = duckdb.connect(DB_PATH)
    
    # Criar tabela de usuários
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_curadores (
            nome VARCHAR,
            id_nome VARCHAR PRIMARY KEY,
            senha VARCHAR,
            unidade VARCHAR
        )
    """)
    
    # Lista de usuários cadastrados
    usuarios = [
        ("Curador", "curador", "teste123", "Sistema"),
        ("Evandro Farias", "evandro", "farias123", "UFPB"),
        ("Paulo Fernando", "paulof", "paulof123", "SUDENE"),
        ("Danilo Arruda", "danilo", "danilo123", "UFPB")
    ]
    
    # Inserir ou atualizar usuários (UPSERT)
    for nome, id_nome, senha, unidade in usuarios:
        conn.execute("""
            INSERT INTO usuarios_curadores (nome, id_nome, senha, unidade)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (id_nome) DO UPDATE SET
                nome = EXCLUDED.nome,
                senha = EXCLUDED.senha,
                unidade = EXCLUDED.unidade
        """, [nome, id_nome, senha, unidade])
        
    print(f"✅ Tabela 'usuarios_curadores' criada e populada com {len(usuarios)} usuários no DuckDB: {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    setup_usuarios_db()
