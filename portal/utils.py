import streamlit as st
import duckdb

import os
import re

UFS_NORDESTE = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}


def categorizar_localizacao(uf: str | None, municipio: str | None) -> str:
    """Classifica a localização do fornecedor contratado em 4 categorias."""
    if not uf or str(uf).strip() == "" or str(uf).upper() == "NONE":
        return "Não Identificado"
    uf_clean = str(uf).strip().upper()
    mun_clean = str(municipio).strip().upper() if municipio else ""
    mun_norm = re.sub(r"[ÁÀÂÃ]", "A", mun_clean)
    if uf_clean == "PB":
        if "JOAO PESSOA" in mun_norm:
            return "Capital (PB)"
        return "Interior (PB)"
    elif uf_clean in UFS_NORDESTE:
        return "Nordeste (Demais UFs)"
    else:
        return "Fora do Nordeste"


def normalizar_cnae(cnae_code: str | int | float | None) -> str | None:
    """Normaliza o código CNAE para uma string de 7 dígitos com zeros à esquerda.
    
    Trata floats (ex: 163600.0 -> '0163600'), inteiros, strings formatadas ('01.63-6/00')
    e strings numéricas sem zero à esquerda.
    """
    if cnae_code is None or str(cnae_code).strip() in ("", "None", "nan"):
        return None
    try:
        val = int(float(cnae_code))
        if val <= 0:
            return None
        return f"{val:07d}"
    except (ValueError, TypeError):
        s = re.sub(r"\D", "", str(cnae_code))
        return s.zfill(7) if s else None


def categorizar_setor_cnae(cnae_code: str | int | float | None) -> str:
    """Mapeia o código CNAE para os 7 Setores Econômicos principais."""
    cnae_str = normalizar_cnae(cnae_code)
    if not cnae_str or len(cnae_str) < 2:
        return "Não Classificado"
    try:
        divisao = int(cnae_str[:2])
    except ValueError:
        return "Não Classificado"

    if 1 <= divisao <= 3:
        return "Agricultura e Pecuária"
    elif 5 <= divisao <= 9:
        return "Indústria Extrativa"
    elif 10 <= divisao <= 33:
        return "Indústria de Transformação"
    elif 35 <= divisao <= 39:
        return "Serviços Industriais de Utilidade Pública (SIUP)"
    elif 41 <= divisao <= 43:
        return "Construção Civil"
    elif 45 <= divisao <= 47:
        return "Comércio"
    elif 49 <= divisao <= 96:
        return "Serviços"
    else:
        return "Outros / Não Classificado"


def categorizar_intensidade_tecnologica(cnae_code: str | int | float | None) -> str:
    """Mapeia a intensidade tecnológica de acordo com a taxonomia OCDE/IBGE."""
    cnae_str = normalizar_cnae(cnae_code)
    if not cnae_str or len(cnae_str) < 2:
        return "Não Classificado"
    try:
        divisao = int(cnae_str[:2])
    except ValueError:
        return "Não Classificado"

    if divisao in {21, 26, 72} or cnae_str.startswith(("303", "304")):
        return "Alta Intensidade Tecnológica"
    if divisao in {20, 27, 28, 29, 30} or cnae_str.startswith("325"):
        return "Média-Alta Intensidade Tecnológica"
    if divisao in {19, 22, 23, 24, 25, 33} or cnae_str.startswith("301"):
        return "Média-Baixa Intensidade Tecnológica"
    if divisao in {10, 11, 12, 13, 14, 15, 16, 17, 18, 31, 32}:
        return "Baixa Intensidade Tecnológica"
    if divisao in {61, 62, 63}:
        return "Alta Intensidade Tecnológica (Serviços KIS)"
    return "Serviços e Outros (Não-Industrial)"


def categorizar_ibge_pim_estrito(cnae_code: str | int | float | None) -> str | None:
    """Classificação da Abordagem 1 (Indústria Fabricante Estrita PIM-PF / Divisões 05 a 33 da CNAE).
    
    Retorna a categoria IBGE se pertencer à indústria fabril, ou None caso contrário.
    """
    cnae_str = normalizar_cnae(cnae_code)
    if not cnae_str or len(cnae_str) < 2:
        return None
    try:
        cnae_int = int(cnae_str)
        divisao = int(cnae_str[:2])
        grupo = int(cnae_str[:3]) if len(cnae_str) >= 3 else 0
        subclasse_5 = int(cnae_str[:5]) if len(cnae_str) >= 5 else 0
    except ValueError:
        return None

    # Restrito às seções B e C (Divisões 05 a 33)
    if not (5 <= divisao <= 33):
        return None

    # Bens de Capital
    if (
        divisao == 28
        or (divisao == 26 and grupo in (261, 262, 265))
        or (divisao == 27 and grupo in (271, 273, 279))
        or (divisao == 29 and grupo in (292, 293))
        or (divisao == 30 and grupo in (301, 303, 304, 305))
        or (divisao == 32 and subclasse_5 == 32501)
        or divisao == 33
    ):
        return "Bens de Capital"

    # Bens Intermediários
    if (
        5 <= divisao <= 9
        or divisao in (16, 17, 22, 23, 24, 25)
        or (divisao == 20 and grupo not in (206, 207))
        or (divisao == 29 and grupo == 294)
        or (divisao == 13 and grupo in (131, 132, 133))
    ):
        return "Bens Intermediários"

    # Bens de Consumo Duráveis
    if (
        (divisao == 26 and grupo in (263, 264))
        or (divisao == 27 and grupo == 275)
        or (divisao == 29 and grupo == 291)
        or (divisao == 30 and grupo == 309)
        or divisao == 31
        or (divisao == 32 and grupo in (321, 322, 323, 324))
    ):
        return "Bens de Consumo Duráveis"

    # Bens de Consumo Semiduráveis e Não Duráveis
    if (
        divisao in (10, 11, 12, 14, 15, 18, 21)
        or (divisao == 13 and grupo in (134, 135))
        or (divisao == 20 and grupo in (206, 207))
        or (divisao == 32 and grupo == 329)
    ):
        return "Bens de Consumo Semiduráveis e Não Duráveis"

    return None


def categorizar_ibge_cadeia_ampla(cnae_code: str | int | float | None) -> str:
    """Classificação da Abordagem 2 (Cadeia Ampla de Aquisição de Bens / Indústria + Comércio Distribuidor).
    
    Classifica todas as compras públicas sob as 4 Grandes Categorias de Bens ou macrosetores estruturais.
    """
    cnae_str = normalizar_cnae(cnae_code)
    if not cnae_str or len(cnae_str) < 2:
        return "Não Classificado"
    try:
        cnae_int = int(cnae_str)
        divisao = int(cnae_str[:2])
        grupo = int(cnae_str[:3]) if len(cnae_str) >= 3 else 0
        subclasse_5 = int(cnae_str[:5]) if len(cnae_str) >= 5 else 0
    except ValueError:
        return "Não Classificado"

    # Bens de Capital (Indústria + Comércio de Máquinas e Equipamentos)
    if (
        divisao == 28
        or (divisao == 26 and grupo in (261, 262, 265))
        or (divisao == 27 and grupo in (271, 273, 279))
        or (divisao == 29 and grupo in (292, 293))
        or (divisao == 30 and grupo in (301, 303, 304, 305))
        or (divisao == 32 and subclasse_5 == 32501)
        or divisao == 33
        or grupo in (466, 465)
        or subclasse_5 == 47512
        or cnae_int in (4511102, 4511104, 4511106)
    ):
        return "Bens de Capital"

    # Bens Intermediários (Indústria + Comércio de Autopeças e Insumos)
    if (
        5 <= divisao <= 9
        or divisao in (16, 17, 22, 23, 24, 25)
        or (divisao == 20 and grupo not in (206, 207))
        or (divisao == 29 and grupo == 294)
        or (divisao == 13 and grupo in (131, 132, 133))
        or grupo in (453, 467, 468)
        or grupo == 474
    ):
        return "Bens Intermediários"

    # Bens de Consumo Duráveis (Indústria + Comércio Moveleiro e Eletro)
    if (
        (divisao == 26 and grupo in (263, 264))
        or (divisao == 27 and grupo == 275)
        or (divisao == 29 and grupo == 291)
        or (divisao == 30 and grupo == 309)
        or divisao == 31
        or (divisao == 32 and grupo in (321, 322, 323, 324))
        or grupo == 454
        or subclasse_5 in (47539, 47547, 46494)
        or cnae_int in (4511101, 4511103, 4511105)
    ):
        return "Bens de Consumo Duráveis"

    # Bens de Consumo Semiduráveis e Não Duráveis (Indústria Farmacêutica/Alimentos + Distribuidoras)
    if (
        divisao in (10, 11, 12, 14, 15, 18, 21)
        or (divisao == 13 and grupo in (134, 135))
        or (divisao == 20 and grupo in (206, 207))
        or (divisao == 32 and grupo == 329)
        or grupo in (462, 463, 464, 471, 472, 473, 476, 477, 478)
    ):
        return "Bens de Consumo Semiduráveis e Não Duráveis"

    # Macrocategorias Estruturais
    if 41 <= divisao <= 43:
        return "Construção Civil (Infraestrutura/FBCF)"
    elif 35 <= divisao <= 39:
        return "Serviços Industriais de Utilidade Pública (SIUP)"
    elif 49 <= divisao <= 96:
        return "Serviços Gerais"
    elif 1 <= divisao <= 3:
        return "Agropecuária"
    else:
        return "Demais Setores"


def categorizar_grande_setor(cnae_code: str | int | None) -> str:
    """Classifica o código CNAE nas Grandes Categorias Econômicas do IBGE (CGCE / PIM-PF)."""
    return categorizar_ibge_cadeia_ampla(cnae_code)

def get_db_connection():
    """
    Retorna uma conexão com o banco DuckDB analítico do projeto.
    Abre em modo somente leitura (read_only=True). Se o banco estiver travado
    por processo externo (ex: DBeaver), utiliza automaticamente um snapshot
    temporário em /tmp para não interromper a navegação no portal.
    """
    import shutil
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "compras_pb.duckdb")
    try:
        return duckdb.connect(db_path, read_only=True)
    except duckdb.IOException:
        tmp_db = "/tmp/compras_pb_ro_cache.duckdb"
        shutil.copy2(db_path, tmp_db)
        return duckdb.connect(tmp_db, read_only=True)

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
    
def aplicar_estilo_grafico(fig, altura=None):
    """Aplica formatação padronizada de alta visibilidade e contraste nos gráficos Plotly.
    
    - Eixos X e Y escuros, nítidos e com fonte em negrito.
    - Valores das barras em negrito com fonte escura e legível.
    - Gridlines suaves e background transparente.
    """
    if fig is None:
        return fig

    estilo_eixo = dict(
        tickfont=dict(color="#0f172a", size=12, family="sans-serif"),
        title_font=dict(color="#0f172a", size=13, family="sans-serif"),
        showline=True,
        linecolor="#334155",
        linewidth=1.5,
        gridcolor="#e2e8f0",
        zerolinecolor="#cbd5e1",
    )

    fig.update_layout(
        font=dict(family="sans-serif", size=13, color="#0f172a"),
        title=dict(font=dict(size=15, color="#0f172a", family="sans-serif")),
        xaxis=estilo_eixo,
        yaxis=estilo_eixo,
        plot_bgcolor="rgba(248, 250, 252, 0.4)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=40, t=45, b=25)
    )

    if altura:
        fig.update_layout(height=altura)

    try:
        fig.update_traces(
            textfont=dict(color="#0f172a", size=12, family="sans-serif"),
            cliponaxis=False
        )
    except Exception:
        pass

    return fig


def render_sidebar_docs():
    """
    Renderiza um painel na barra lateral com atalhos de navegação rápida e links para a documentação técnica.
    """
    st.sidebar.markdown("### 🧭 Navegação Rápida")
    st.sidebar.page_link("app.py", label="Início / Visão Geral", icon="🏠")
    st.sidebar.page_link("pages/1_🛍️_Compras_Publicas.py", label="1. Compras Públicas", icon="🛍️")
    st.sidebar.page_link("pages/5_🏭_Perfil_Produtivo_CNAE.py", label="2. Perfil Produtivo & CNAE", icon="🏭")
    st.sidebar.page_link("pages/3_📈_Dados_Socioeconomicos.py", label="3. Dados Socioeconômicos", icon="📈")
    st.sidebar.page_link("pages/2_⚖️_Base_Legal.py", label="4. Base Legal & Regulatória", icon="⚖️")
    st.sidebar.page_link("pages/4_📝_Curadoria_Manual.py", label="5. Curadoria Normativa", icon="📝")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Documentação do Projeto")
    st.sidebar.markdown("Acompanhe os referenciais e metodologias da pesquisa:")
    
    # Link direto para o PDF no repositório GitHub
    pdf_url = "https://github.com/evandro2023/portal_compras_publicas_pb/blob/main/documentacao/relatorio_compras_pb_gov.pdf"
    st.sidebar.markdown(f"📄 [Relatório Metodológico (PDF)]({pdf_url})")
    
    # Link para o README
    readme_url = "https://github.com/evandro2023/portal_compras_publicas_pb/blob/main/README.md"
    st.sidebar.markdown(f"📖 [Visão Geral e Arquitetura]({readme_url})")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 Portal Compras Públicas PB.")
    st.sidebar.caption("🤖 *SUDENE / Governo da Paraíba.*")

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
