import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from utils import set_page_config, render_custom_css, render_sidebar_docs, get_db_connection

set_page_config(page_title="Início - Portal de Compras Públicas PB")
render_custom_css()
render_sidebar_docs()

# --- Cabeçalho com Logos e Título ---
col1, col2, col3 = st.columns([1, 2.5, 1])

with col1:
    if os.path.exists("fig/logo_nib.png"):
        st.image("fig/logo_nib.png", width=180)

with col2:
    st.markdown("<h3 style='text-align: center; margin-top: 10px; color: #0f172a; font-weight: 700;'>Portal de Inteligência: Compras Públicas e Desenvolvimento Regional</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #475569; font-size: 0.95rem; margin-top: -5px;'>Observatório de Microdados Governamentais, Estrutura Produtiva e Base Regulatória (PB &times; SE)</p>", unsafe_allow_html=True)

with col3:
    if os.path.exists("fig/logo_sudene.png"):
        st.image("fig/logo_sudene.png", width=180)

st.markdown("<hr style='border-top: 3px solid #0f52ba; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- Métricas Executivas da Base ---
try:
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 
            COUNT(DISTINCT registroCge) as total_cge,
            SUM(valorTotal) as total_valor,
            MIN(ano_referencia) as min_ano,
            MAX(ano_referencia) as max_ano
        FROM contratos
        WHERE valorTotal IS NOT NULL
    """).fetchone()
    total_cge, total_valor, min_ano, max_ano = row
except Exception:
    total_cge, total_valor, min_ano, max_ano = 15357, 26033745832.98, 2024, 2026

with st.container(border=True):
    st.markdown("#### 📌 Panorama Geral do Acervo Mapeado")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Volume Analisado", f"R$ {total_valor:,.2f}", border=True)
    m2.metric("Contratos Mapeados", f"{total_cge:,}".replace(",", "."), border=True)
    m3.metric("Exercícios Cobertos", f"{min_ano} — {max_ano}", border=True)
    m4.metric("Escopo Territorial", "Paraíba (PB)", "SE & Federal", border=True)

st.markdown("""
Este portal é uma iniciativa de pesquisa aplicada financiada pela **SUDENE** e executada em parceria institucional. O objetivo da plataforma é acompanhar, avaliar e instrumentalizar o poder de compra das contratações públicas sob a ótica do **desenvolvimento regional**, da **integração das cadeias produtivas locais** e do **fortalecimento de Micro e Pequenas Empresas (MPEs)**.
""")

st.subheader("🧭 Módulos Analíticos do Portal")
st.write("Selecione um dos painéis interativos para explorar os microdados:")

# --- Grid de Módulos Analíticos com Cards ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    with st.container(border=True):
        st.markdown("### 🛍️ 1. Compras Públicas: Painel Exploratório")
        st.write("Análise temporal e orçamentária dos contratos firmados e licitações adjudicadas pelo Governo da Paraíba. Rankings por órgão, fornecedor, modalidade de contratação e amparo normativo.")
        st.page_link("pages/1_🛍️_Compras_Publicas.py", label="Acessar Compras Públicas", icon="🛍️")

with row1_col2:
    with st.container(border=True):
        st.markdown("### 🏭 2. Perfil Produtivo, CNAE & IBGE")
        st.write("Mapeamento das empresas contratadas por domicílio fiscal (Capital vs. Interior vs. Vazamento), intensidade tecnológica (OCDE/IBGE) e as duas abordagens por Grandes Categorias Econômicas (PIM-PF / CGCE).")
        st.page_link("pages/5_🏭_Perfil_Produtivo_CNAE.py", label="Acessar Perfil Produtivo & CNAE", icon="🏭")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    with st.container(border=True):
        st.markdown("### 📈 3. Dados Socioeconômicos & CAGED")
        st.write("Cruzamento do gasto público estadual com a geração de postos de trabalho formais (Novo CAGED) por setor econômico, taxas de retenção territorial de renda e vazamento inter-regional.")
        st.page_link("pages/3_📈_Dados_Socioeconomicos.py", label="Acessar Dados Socioeconômicos", icon="📈")

with row2_col2:
    with st.container(border=True):
        st.markdown("### ⚖️ 4. Base Legal & Regulatória")
        st.write("Índice de Aderência e Adaptação Normativa (IAAN), matriz comparativa Paraíba x Sergipe x Legislação Federal e avaliação de aderência às matrizes de Keynes, Furtado e Schumpeter.")
        st.page_link("pages/2_⚖️_Base_Legal.py", label="Acessar Base Legal & Regulatória", icon="⚖️")

with st.container(border=True):
    c_cur_info, c_cur_btn = st.columns([3, 1])
    with c_cur_info:
        st.markdown("### 📝 5. Módulo de Curadoria Manual e Triagem Normativa")
        st.write("Ambiente restrito aos pesquisadores e membros do GT para inserção, validação temática e classificação qualitativa de novas normas e decretos estaduais.")
    with c_cur_btn:
        st.write("")
        st.page_link("pages/4_📝_Curadoria_Manual.py", label="Acessar Curadoria", icon="📝")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #475569; font-size: 0.85rem;">
    <p><b>Portal de Inteligência: Compras Públicas e Desenvolvimento Regional na Paraíba</b></p>
    <p><b>Coordenação:</b> Prof. Dr. Paulo Fernando Cavalcanti | <b>Colaboração:</b> Evandro Farias Rocha (UFPB / SUDENE)</p>
    <p>Licença Aberta (MIT) &bull; <i>Desenvolvido com apoio de Agentes de Inteligência Artificial (Google Gemini)</i></p>
</div>
""", unsafe_allow_html=True)
