import streamlit as st
from utils import set_page_config, render_custom_css, render_sidebar_docs

set_page_config(page_title="Início - Portal de Compras Públicas PB")
render_custom_css()
render_sidebar_docs()

# --- Cabeçalho com Logos e Título ---
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    # Logo NIB
    st.image("fig/logo_nib.png", width=180)

with col2:
    # Título centralizado e menor (h3 ao invés de h1)
    st.markdown("<h3 style='text-align: center; margin-top: 15px; color: #2c3e50;'>Portal de Inteligência: Compras Públicas e Desenvolvimento Regional na Paraíba</h3>", unsafe_allow_html=True)

with col3:
    # Logo SUDENE
    st.image("fig/logo_sudene.png", width=180)

# --- Apresentação ---
st.markdown("<hr style='border-top: 3px solid #ff7f0e; margin-top: 0; margin-bottom: 20px;'>", unsafe_allow_html=True)

st.markdown("""
<br><br>

Bem-vindo ao observatório analítico do Estado da Paraíba.

Este portal é uma iniciativa de pesquisa aplicada financiada pela SUDENE e executada em parceria com o Governo da Paraíba. O objetivo desta ferramenta é acompanhar, analisar e avaliar o sistema de compras públicas estaduais sob a ótica do **desenvolvimento regional**, da **inovação tecnológica** e da **transformação produtiva**.

Através de uma interface interativa baseada em microdados governamentais, permitimos que gestores, pesquisadores e a sociedade civil compreendam como o poder de compra do Estado pode atuar como vetor para dinamizar a economia local, integrar arranjos produtivos e fortalecer micro e pequenas empresas (MPEs).

---
**Equipe do Projeto:**
- **Prof. Dr. Paulo Fernando Cavalcanti** – *Coordenador do Projeto*
- **Evandro Farias Rocha** – *Colaborador*
---
""", unsafe_allow_html=True)

st.subheader("Nossos Módulos Analíticos")
st.write("Selecione um dos painéis abaixo para explorar os dados:")

# --- Layout de Cards (Hub) ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
        <div class="nav-card">
            <div class="nav-card-title">🛍️ Compras Públicas PB</div>
            <div class="nav-card-text">
                Análise aprofundada dos contratos, contratações e itens adquiridos pelo Estado da Paraíba.
            </div>
            <a href="/Compras_Publicas" target="_self" class="nav-card-button">Explorar</a>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="nav-card">
            <div class="nav-card-title">🏭 Perfil Produtivo & CNAE</div>
            <div class="nav-card-text">
                Análise por CNAE, CNPJ, localização, setor e intensidade tecnológica dos fornecedores.
            </div>
            <a href="/Perfil_Produtivo_CNAE" target="_self" class="nav-card-button">Explorar</a>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="nav-card">
            <div class="nav-card-title">⚖️ Base Legal</div>
            <div class="nav-card-text">
                Comparação e mapeamento da legislação (Paraíba, Sergipe e Federal).
            </div>
            <a href="/Base_Legal" target="_self" class="nav-card-button">Explorar</a>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="nav-card">
            <div class="nav-card-title">📈 Socioeconômico</div>
            <div class="nav-card-text">
                Módulos integrados com CAGED, RAIS, PIB e Comex Stat para cruzamento local.
            </div>
            <a href="/Dados_Socioeconomicos" target="_self" class="nav-card-button">Explorar</a>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
        <div class="nav-card">
            <div class="nav-card-title">📝 Curadoria</div>
            <div class="nav-card-text">
                Módulo restrito para revisão e triagem de leis e decretos.
            </div>
            <a href="/Curadoria_Manual" target="_self" class="nav-card-button">Acessar</a>
        </div>
    """, unsafe_allow_html=True)


st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.85rem;">
    <p><b>Portal de Inteligência: Compras Públicas e Desenvolvimento Regional na Paraíba</b></p>
    <p>© 2026 Prof. Dr. Paulo Fernando Cavalcanti & Evandro Farias Rocha (UFPB / SUDENE). Licença Open Source (MIT).</p>
    <p>🤖 <i>Desenvolvimento computacional e engenharia de dados auxiliados por Agentes de Inteligência Artificial (Google Gemini Agentic Coding).</i></p>
</div>
""", unsafe_allow_html=True)
