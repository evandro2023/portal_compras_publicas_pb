import duckdb
import pandas as pd

def gerar_dim_matriz_teorica():
    """Gera a tabela dim_matriz_teorica baseada na Tabela 6 do Relatório."""
    data = [
        {"norma_base": "Lei 14.133/2021", "score_keynes": 0.91, "score_furtado": 0.80, "score_schumpeter": 0.60, "predominancia": "Keynes"},
        {"norma_base": "Lei Complementar 123/2006", "score_keynes": 0.84, "score_furtado": 0.69, "score_schumpeter": 0.32, "predominancia": "Keynes"},
        {"norma_base": "Lei Complementar 182/2021", "score_keynes": 0.58, "score_furtado": 0.34, "score_schumpeter": 0.76, "predominancia": "Schumpeter"},
        {"norma_base": "Resolução CD/FNDE 11/2026", "score_keynes": 0.84, "score_furtado": 0.81, "score_schumpeter": 0.43, "predominancia": "Keynes"},
        {"norma_base": "Decreto 11.630/2023", "score_keynes": 0.75, "score_furtado": 0.70, "score_schumpeter": 0.87, "predominancia": "Schumpeter"},
        {"norma_base": "Decreto 12.705/2025", "score_keynes": 0.59, "score_furtado": 0.77, "score_schumpeter": 0.81, "predominancia": "Schumpeter"},
        {"norma_base": "Decreto 12.771/2025", "score_keynes": 0.95, "score_furtado": 0.99, "score_schumpeter": 0.83, "predominancia": "Furtado"},
        {"norma_base": "Decreto Estadual 43.975/2023", "score_keynes": 0.74, "score_furtado": 0.42, "score_schumpeter": 0.30, "predominancia": "Keynes"},
        {"norma_base": "Decreto Estadual 46.187/2025", "score_keynes": 0.82, "score_furtado": 0.69, "score_schumpeter": 0.61, "predominancia": "Keynes"},
        {"norma_base": "Lei 13.303/2016", "score_keynes": 0.80, "score_furtado": 0.60, "score_schumpeter": 0.50, "predominancia": "Keynes"}, # Estimativa adicionada
    ]
    return pd.DataFrame(data)

def gerar_dim_impacto_regional():
    """Gera a tabela dim_impacto_regional baseada na Tabela 11 do Relatório."""
    data = [
        {
            "norma_base": "Lei 14.133/2021",
            "mecanismo": "Planejamento, margem de preferência, modalidades para demandas complexas.",
            "reflexos_socioeconomicos": "Potencial de geração de mercado institucional, formalização, qualificação de fornecedores.",
            "risco_metodologico": "A norma cria instrumentos de indução, mas sua aplicação pode permanecer centrada em conformidade formal e menor preço, sem produzir mudança setorial se os editais não incorporarem critérios territoriais e tecnológicos."
        },
        {
            "norma_base": "Lei Complementar 123/2006",
            "mecanismo": "Tratamento diferenciado para ME/EPP, licitações exclusivas, cotas.",
            "reflexos_socioeconomicos": "Pode fortalecer emprego local, renda empresarial e circulação regional.",
            "risco_metodologico": "Pode reforçar uma base produtiva de baixa complexidade se a política apenas comprar localmente aquilo que a região já produz, sem estimular diversificação, inovação e subida de qualidade."
        },
        {
            "norma_base": "Lei 13.303/2016",
            "mecanismo": "Regras das empresas estatais, parcerias e contratações.",
            "reflexos_socioeconomicos": "Agilidade nas contratações e parcerias com setor privado local.",
            "risco_metodologico": "Pode privilegiar grandes players estabelecidos em detrimento de fornecedores locais se não houver política de encadeamento."
        },
        {
            "norma_base": "Lei Complementar 182/2021",
            "mecanismo": "CPSI e contratação experimental de soluções inovadoras.",
            "reflexos_socioeconomicos": "Pode criar empregos qualificados, reter talentos e aproximar universidades.",
            "risco_metodologico": "A contratação de inovação pode concentrar oportunidades em poucos atores com maior capacidade técnica, deixando startups periféricas fora do processo."
        }
    ]
    return pd.DataFrame(data)

def gerar_map_amparo_legal(conn):
    """Lê as strings sujas da coluna amparoLegal e mapeia para a norma_base."""
    
    try:
        # Extrai os amparos únicos da base de contratações (ignora nulos)
        df_amparos = conn.execute("SELECT DISTINCT amparoLegal FROM contratacoes WHERE amparoLegal IS NOT NULL AND amparoLegal != ''").df()
    except Exception as e:
        print(f"Erro ao buscar amparos legais (a tabela contratacoes existe?): {e}")
        return pd.DataFrame(columns=['amparo_sujo', 'norma_base'])

    mapeamento = []
    
    for amparo in df_amparos['amparoLegal']:
        amparo_str = str(amparo).lower()
        norma_base = "Não Classificado"
        
        # Lógica de Classificação / Expressões Regulares Simples
        if "14.133" in amparo_str or "14133" in amparo_str:
            norma_base = "Lei 14.133/2021"
        elif "123/2006" in amparo_str or "123/06" in amparo_str:
            norma_base = "Lei Complementar 123/2006"
        elif "182/2021" in amparo_str or "182/21" in amparo_str:
            norma_base = "Lei Complementar 182/2021"
        elif "13.303" in amparo_str or "13303" in amparo_str:
            norma_base = "Lei 13.303/2016"
        elif "43.975" in amparo_str:
            norma_base = "Decreto Estadual 43.975/2023"
        elif "46.187" in amparo_str:
            norma_base = "Decreto Estadual 46.187/2025"
        
        mapeamento.append({
            "amparo_sujo": amparo,
            "norma_base": norma_base
        })
        
    return pd.DataFrame(mapeamento)

def aplicar_enriquecimento(db_path="data/compras_pb.duckdb"):
    print("\n--- Iniciando Enriquecimento Socioeconômico ---")
    conn = duckdb.connect(db_path)
    
    try:
        df_matriz = gerar_dim_matriz_teorica()
        conn.execute("CREATE OR REPLACE TABLE dim_matriz_teorica AS SELECT * FROM df_matriz")
        print("✓ Tabela dim_matriz_teorica criada.")
        
        df_impacto = gerar_dim_impacto_regional()
        conn.execute("CREATE OR REPLACE TABLE dim_impacto_regional AS SELECT * FROM df_impacto")
        print("✓ Tabela dim_impacto_regional criada.")
        
        df_map = gerar_map_amparo_legal(conn)
        conn.execute("CREATE OR REPLACE TABLE map_amparo_legal AS SELECT * FROM df_map")
        print("✓ Tabela map_amparo_legal criada (Ponte Concluída).")
        
        # Gera uma view materializada unindo os dados da API com as Matrizes Teóricas
        # Essa View será consumida pelo Streamlit para facilitar as análises.
        view_query = """
        CREATE OR REPLACE VIEW vw_analise_socioeconomica AS
        SELECT 
            c.*,
            m.norma_base,
            t.score_keynes,
            t.score_furtado,
            t.score_schumpeter,
            t.predominancia,
            i.mecanismo,
            i.reflexos_socioeconomicos,
            i.risco_metodologico
        FROM contratacoes c
        LEFT JOIN map_amparo_legal m ON c.amparoLegal = m.amparo_sujo
        LEFT JOIN dim_matriz_teorica t ON m.norma_base = t.norma_base
        LEFT JOIN dim_impacto_regional i ON m.norma_base = i.norma_base;
        """
        conn.execute(view_query)
        print("✓ View analítica 'vw_analise_socioeconomica' criada com sucesso.")
        
    except Exception as e:
        print(f"Erro no enriquecimento: {e}")
    finally:
        conn.close()
        print("--- Fim do Enriquecimento ---\n")

if __name__ == "__main__":
    aplicar_enriquecimento()
