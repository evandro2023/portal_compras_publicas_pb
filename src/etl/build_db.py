import duckdb
import pandas as pd
import os
from enriquecimento_socioeconomico import aplicar_enriquecimento

DB_PATH = "data/compras_pb.duckdb"
RAW_DIR = "data/raw/compras_pb"
CATALOGO_LEIS = "data/catalogo_curado_leis.csv"

def get_csv_files(directory):
    """Retorna a lista de arquivos CSV no diretório."""
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

def build_database():
    print(f"--- Iniciando ETL para {DB_PATH} ---")
    
    # Conecta ou cria o banco de dados
    conn = duckdb.connect(DB_PATH)
    
    # 1. Carregar o Catálogo de Leis
    if os.path.exists(CATALOGO_LEIS):
        print(f"Carregando catálogo de leis: {CATALOGO_LEIS}")
        try:
            df_leis = pd.read_csv(CATALOGO_LEIS)
            conn.execute("CREATE OR REPLACE TABLE leis_catalogo AS SELECT * FROM df_leis")
            print(f"  Tabela 'leis_catalogo' criada com {len(df_leis)} registros.")
        except Exception as e:
            print(f"  Erro ao processar o catálogo de leis: {e}")
    else:
        print(f"Aviso: Catálogo de leis não encontrado em {CATALOGO_LEIS}")

    # 2. Carregar os dados brutos de compras
    csv_files = get_csv_files(RAW_DIR)
    
    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado em {RAW_DIR}")
    else:
        for file in csv_files:
            table_name = file.replace('.csv', '')
            file_path = os.path.join(RAW_DIR, file)
            print(f"Carregando {file_path} na tabela '{table_name}'...")
            
            try:
                # O pandas lidará com tipos mistos de forma segura para a carga inicial
                df_temp = pd.read_csv(file_path, low_memory=False)
                
                # Para evitar conflitos com palavras reservadas ou espaços
                df_temp.columns = [str(col).strip().replace(' ', '_') for col in df_temp.columns]
                
                # Injeta a variável df_temp na query do duckdb usando a feature nativa
                conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_temp")
                print(f"  Tabela '{table_name}' recriada com {len(df_temp)} registros.")
            except Exception as e:
                print(f"  Erro ao processar {file}: {e}")

    # Lista as tabelas no banco de dados no final
    print("\n--- Tabelas criadas no banco ---")
    tables = conn.execute("SHOW TABLES").fetchall()
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"- {t[0]}: {count} linhas")

    conn.close()
    
    # Roda o enriquecimento por último
    aplicar_enriquecimento(DB_PATH)
    
    print("ETL concluído com sucesso!")

if __name__ == "__main__":
    build_database()
