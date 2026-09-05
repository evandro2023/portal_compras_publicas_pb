import streamlit as st
import duckdb

import os

def get_db_connection():
    """
    Retorna uma conexão com o banco DuckDB analítico do projeto.
    Abre em modo somente leitura (read_only=True) para permitir acesso
    simultâneo, mesmo se o DBeaver ou outro processo estiver com o banco aberto.
    """
    # Obtém o diretório base do projeto (um nível acima da pasta portal onde este utils.py está)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "compras_pb.duckdb")
    return duckdb.connect(db_path, read_only=True)

def set_page_config(page_title="Portal Compras PB"):
    """
    Configurações padrão para todas as páginas do Streamlit.
    """
    st.set_page_config(
        page_title=page_title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
def render_sidebar_docs():
    """
    Renderiza um painel na barra lateral com links para a documentação técnica do projeto.
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Documentação do Projeto")
    st.sidebar.markdown("Acompanhe os referenciais e metodologias da pesquisa:")
    
    # Link direto para o PDF no repositório GitHub (ideal para a nuvem do Streamlit)
    pdf_url = "https://github.com/EvandroFarias/portal_compras_publicas_pb/blob/main/documentacao/relatorio_compras_pb_gov.pdf"
    st.sidebar.markdown(f"📄 [Relatório Analítico Metodológico (PDF)]({pdf_url})")
    
    # Link para o README
    readme_url = "https://github.com/EvandroFarias/portal_compras_publicas_pb/blob/main/README.md"
    st.sidebar.markdown(f"📖 [Visão Geral e Arquitetura (README)]({readme_url})")

def render_custom_css():
    """
    Injeta CSS customizado para estilizar os cards e melhorar o layout geral.
    """
    st.markdown("""
    <style>
    /* Estilo para os cards de navegação */
    .nav-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .nav-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        border-color: #0056b3;
    }
    .nav-card-title {
        color: #0056b3;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .nav-card-text {
        color: #495057;
        font-size: 0.95rem;
        margin-bottom: 15px;
        flex-grow: 1;
    }
    .nav-card-button {
        background-color: #0056b3;
        color: white !important;
        padding: 8px 15px;
        border-radius: 4px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-top: auto;
    }
    .nav-card-button:hover {
        background-color: #004494;
    }
    
    /* Logos Header */
    .logos-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)
