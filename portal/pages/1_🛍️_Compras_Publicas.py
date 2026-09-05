import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Ajusta o path para importar utils da raiz do portal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import set_page_config, get_db_connection, render_sidebar_docs

# Configuração da página
set_page_config("Módulo de Compras Públicas")
render_sidebar_docs()
st.title("🛍️ Compras Públicas: Painel Exploratório")
st.markdown("Análise interativa das contratações e contratos firmados pelo Governo do Estado.")

# Conecta ao banco de dados e carrega dados base
@st.cache_data
def load_data():
    # Invalida o cache antigo
    conn = get_db_connection()
    # Carrega um sample das contratações agregadas para evitar lentidão extrema no protótipo, 
    # ou carrega tudo dependendo do tamanho. Usaremos um limit 100000 para segurança inicial.
    query = """
        SELECT ano_referencia, nomeOrgao, modalidade, valorAdjudicado, situacao, amparoLegal
        FROM contratacoes
        WHERE valorAdjudicado IS NOT NULL
    """
    df = conn.execute(query).df()
    
    # Carrega contratos para ranking de fornecedores
    query_contratos = """
        SELECT ano_referencia, nomeOrgao, contratado, cnpjCpf, valorTotal, municipio
        FROM contratos
        WHERE valorTotal IS NOT NULL
    """
    df_contratos = conn.execute(query_contratos).df()
    
    conn.close()
    return df, df_contratos

try:
    df_contratacoes, df_contratos = load_data()
except Exception as e:
    st.error(f"Erro ao carregar dados do banco: {e}")
    st.stop()

# --- FILTROS LATERAIS ---
st.sidebar.header("Filtros Analíticos")

# Filtro de Ano
anos_disponiveis = sorted(df_contratacoes['ano_referencia'].dropna().unique().tolist())
if not anos_disponiveis:
    anos_disponiveis = [2024, 2025, 2026] # fallback
ano_selecionado = st.sidebar.selectbox("Ano de Referência", ["Todos"] + anos_disponiveis)

# Filtro de Órgão
orgaos_disponiveis = sorted(df_contratacoes['nomeOrgao'].dropna().unique().tolist())
orgao_selecionado = st.sidebar.selectbox("Órgão", ["Todos"] + orgaos_disponiveis)

# Aplica os filtros
df_filtrado_contratacoes = df_contratacoes.copy()
df_filtrado_contratos = df_contratos.copy()

if ano_selecionado != "Todos":
    df_filtrado_contratacoes = df_filtrado_contratacoes[df_filtrado_contratacoes['ano_referencia'] == ano_selecionado]
    df_filtrado_contratos = df_filtrado_contratos[df_filtrado_contratos['ano_referencia'] == ano_selecionado]

if orgao_selecionado != "Todos":
    df_filtrado_contratacoes = df_filtrado_contratacoes[df_filtrado_contratacoes['nomeOrgao'] == orgao_selecionado]
    df_filtrado_contratos = df_filtrado_contratos[df_filtrado_contratos['nomeOrgao'] == orgao_selecionado]

# --- ABAS (TABS) ---
tab1, tab2, tab3 = st.tabs(["📊 Visão: Contratações (Licitações)", "📜 Detalhamento: Contratos Firmados", "🏛️ Regulação e Teoria Econômica"])

with tab1:
    st.markdown("### Panorama dos Processos de Contratação")
    # --- KPIs ---
    col1, col2 = st.columns(2)

    valor_total = df_filtrado_contratacoes['valorAdjudicado'].sum()
    num_contratacoes = len(df_filtrado_contratacoes)
    valor_total_formatado = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    with col1:
        st.metric(label="Valor Total Adjudicado", value=valor_total_formatado)
    with col2:
        st.metric(label="Total de Processos", value=f"{num_contratacoes:,}".replace(",", "."))

    st.markdown("---")

    # --- GRÁFICOS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Órgãos por Volume")
        df_orgao = df_filtrado_contratacoes.groupby('nomeOrgao')['valorAdjudicado'].sum().reset_index()
        df_orgao = df_orgao.sort_values('valorAdjudicado', ascending=False).head(10)
        
        fig_orgao = px.bar(
            df_orgao, 
            x='valorAdjudicado', 
            y='nomeOrgao',
            orientation='h',
            labels={'valorAdjudicado': 'Valor (R$)', 'nomeOrgao': 'Órgão'},
            color_discrete_sequence=['#0056b3']
        )
        fig_orgao.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_orgao, use_container_width=True)

    with col2:
        st.subheader("Compras por Modalidade")
        df_modalidade = df_filtrado_contratacoes.groupby('modalidade')['valorAdjudicado'].sum().reset_index()
        
        fig_mod = px.pie(
            df_modalidade, 
            values='valorAdjudicado', 
            names='modalidade',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_mod, use_container_width=True)

    st.markdown("---")
    st.subheader("Amparo Legal (Base Normativa)")
    
    # Limpa valores vazios
    df_filtrado_contratacoes['amparoLegal'] = df_filtrado_contratacoes['amparoLegal'].fillna('Não Informado')
    df_filtrado_contratacoes.loc[df_filtrado_contratacoes['amparoLegal'] == '', 'amparoLegal'] = 'Não Informado'
    
    df_amparo = df_filtrado_contratacoes.groupby('amparoLegal')['valorAdjudicado'].sum().reset_index()
    df_amparo = df_amparo.sort_values('valorAdjudicado', ascending=False).head(10)
    
    fig_amparo = px.bar(
        df_amparo, 
        x='valorAdjudicado', 
        y='amparoLegal',
        orientation='h',
        labels={'valorAdjudicado': 'Valor Adjudicado (R$)', 'amparoLegal': 'Base Legal'},
        color_discrete_sequence=['#8c564b']
    )
    fig_amparo.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_amparo, use_container_width=True)

with tab2:
    st.markdown("### Análise de Fornecedores e Contratos Finalizados")
    
    # KPI Contratos
    num_fornecedores = df_filtrado_contratos['cnpjCpf'].nunique()
    valor_contratos = df_filtrado_contratos['valorTotal'].sum()
    valor_contratos_fmt = f"R$ {valor_contratos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    c1, c2 = st.columns(2)
    c1.metric(label="Volume Financeiro dos Contratos", value=valor_contratos_fmt)
    c2.metric(label="Fornecedores Distintos", value=f"{num_fornecedores:,}".replace(",", "."))
    
    st.markdown("---")

    # --- RANKING DE FORNECEDORES ---
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        st.subheader("Top 10 Maiores Fornecedores")
        df_forn = df_filtrado_contratos.groupby('contratado')['valorTotal'].sum().reset_index()
        df_forn = df_forn.sort_values('valorTotal', ascending=False).head(10)
    
        fig_forn = px.bar(
            df_forn, 
            x='valorTotal', 
            y='contratado',
            orientation='h',
            labels={'valorTotal': 'Valor Contratado (R$)', 'contratado': 'Fornecedor'},
            color_discrete_sequence=['#28a745']
        )
        fig_forn.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_forn, use_container_width=True)

    with col2_2:
        st.subheader("Top 10 Municípios (Sede ou Execução)")
        df_filtrado_contratos['municipio'] = df_filtrado_contratos['municipio'].fillna('Não Informado')
        df_filtrado_contratos.loc[df_filtrado_contratos['municipio'] == '', 'municipio'] = 'Não Informado'
        
        df_mun = df_filtrado_contratos.groupby('municipio')['valorTotal'].sum().reset_index()
        df_mun = df_mun.sort_values('valorTotal', ascending=False).head(10)
    
        fig_mun = px.bar(
            df_mun, 
            x='valorTotal', 
            y='municipio',
            orientation='h',
            labels={'valorTotal': 'Valor (R$)', 'municipio': 'Município'},
            color_discrete_sequence=['#17a2b8']
        )
        fig_mun.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_mun, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("Amostra dos Dados Brutos (Contratos)")
    st.dataframe(
        df_filtrado_contratos.head(100).style.format({
            'valorTotal': 'R$ {:,.2f}'
        }), 
        use_container_width=True
    )

with tab3:
    st.markdown("### 🏛️ Impacto Regulatório e Teoria Econômica")
    st.markdown("Análise da aderência das compras à regulamentação estadual e federal, além das implicações econômicas.")
    
    st.markdown("---")
    st.subheader("1. Aderência Federal x Estadual (PB)")
    st.info("A Lei Federal 14.133/2021 estabelece normas gerais, mas delega aos Estados a regulamentação de procedimentos específicos. Abaixo, o mapeamento da regulamentação no Estado da Paraíba.")
    
    aderencia_data = {
        "Tema (Lei Federal 14.133)": ["Fase Preparatória (Art. 18)", "Contratação Direta (Art. 72)", "Critério de Menor Preço (Art. 34)", "Execução Indireta (Art. 45)"],
        "Regulamentação Estadual (PB)": ["Decreto 46.187/2025", "Decreto 41.200/2021 / ON 0001/2025", "IN SEAD 005/2023", "IN SEAD 007/2023"],
        "Status de Aderência": ["Regulamentado", "Regulamentado", "Regulamentado", "Regulamentado"]
    }
    st.table(pd.DataFrame(aderencia_data))
    
    st.markdown("---")
    st.subheader("2. Comparativo Regulatório: PB x SE")
    st.info("Comparação de como diferentes estados regulamentam as mesmas diretrizes federais, impactando a eficiência das compras.")
    
    comp_data = {
        "Critério Analisado": ["Regulamentação ME/EPP", "Pesquisa de Preços", "Sustentabilidade/Selo", "Fase Preparatória"],
        "Paraíba (PB)": ["Lei 8.292/2007 / Decreto 32.056", "Decreto 42.967/2022", "Decreto 43.346 (Logística Reversa)", "Decreto 46.187/2025"],
        "Sergipe (SE)": ["Lei 8.747/2020 / Lei 9.493/2024", "Pendente/Outro", "Decreto 622/623 (Selo Socioambiental)", "Decreto 567/2024 (Plano Anual)"]
    }
    st.table(pd.DataFrame(comp_data))
    
    st.markdown("---")
    st.subheader("3. Teoria Econômica Aplicada")
    st.info("Conexão entre as normativas implementadas e os conceitos de economia institucional e microeconomia.")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("**📉 Custos de Transação**")
        st.caption("A clareza na *Fase Preparatória (Dec. 46.187/2025)* reduz incertezas, diminuindo os custos de elaboração de propostas pelos fornecedores e os custos de fiscalização pelo Estado.")
    with col_t2:
        st.markdown("**⚖️ Problema Agente-Principal**")
        st.caption("Normativas como a *IN SEAD 004/2023* (regras de licitação) e a exigência de transparência mitigam a assimetria de informação entre o servidor público (agente) e a sociedade (principal).")
    with col_t3:
        st.markdown("**🔨 Teoria dos Leilões**")
        st.caption("A *IN SEAD 005/2023* (Menor Preço) estrutura os leilões reversos. Regras claras evitam a 'Maldição do Vencedor' e atraem maior competitividade.")
