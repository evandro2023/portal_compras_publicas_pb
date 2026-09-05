import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import set_page_config, get_db_connection, render_sidebar_docs

set_page_config("Base Legal e Regulatória")
render_sidebar_docs()

st.title("⚖️ Módulo: Base Legal e Regulatória")
st.markdown("Análise qualitativa e comparativa do arcabouço normativo de compras públicas sob a ótica do desenvolvimento regional.")

# --- DADOS ESTÁTICOS DO RELATÓRIO (Aba 1 e Aba 2) ---
data_iaan = [
    {"Tema": "Âmbito de aplicação da Lei 14.133", "Tipologia": "Reprodução Literal", "IAAN": 1.00},
    {"Tema": "Pesquisa de preços", "Tipologia": "Adaptação Contextual", "IAAN": 0.75},
    {"Tema": "Gestão e fiscalização contratual", "Tipologia": "Adaptação Contextual", "IAAN": 0.50},
    {"Tema": "Credenciamento", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.25},
    {"Tema": "Fase preparatória, ETP e TR", "Tipologia": "Adaptação Contextual", "IAAN": 0.50},
    {"Tema": "Tratamento favorecido a ME/EPP", "Tipologia": "Adaptação Contextual", "IAAN": 0.50},
    {"Tema": "Preferência regional", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.25},
    {"Tema": "Startups e CPSI", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.00},
    {"Tema": "Margem de preferência e compras sustentáveis", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.00},
    {"Tema": "Alimentação escolar e PCT", "Tipologia": "Adaptação Contextual", "IAAN": 0.50},
    {"Tema": "Diálogo competitivo", "Tipologia": "Reprodução Literal", "IAAN": 1.00},
    {"Tema": "Estratégia nacional de compras sustentáveis", "Tipologia": "Adaptação Contextual", "IAAN": 0.50},
    {"Tema": "Taxonomia sustentável aplicada", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.25},
    {"Tema": "Adensamento produtivo no PAC", "Tipologia": "Complementação/Inovação Substantiva", "IAAN": 0.25}
]
df_iaan = pd.DataFrame(data_iaan)

data_se = [
    {"Tema": "Regulamentação geral da Lei nº 14.133", "Vantagem": "Sergipe", "Comparação": "Sergipe apresenta consolidação normativa mais concentrada por grandes objetos; Paraíba aparece com regulamentação mais modular por etapa/instrumento."},
    {"Tema": "Pesquisa de preços e planejamento", "Vantagem": "Equilíbrio", "Comparação": "Paraíba tem maior detalhe temático em fase preparatória; Sergipe evidencia planejamento anual como instrumento de previsibilidade de demanda."},
    {"Tema": "Tratamento favorecido a pequenos fornecedores", "Vantagem": "Sergipe", "Comparação": "Sergipe adota rol de beneficiários mais amplo e atualizado; Paraíba possui conexão explícita com desenvolvimento municipal/regional no decreto regulamentador."},
    {"Tema": "Compras sustentáveis e critérios socioambientais", "Vantagem": "Equilíbrio", "Comparação": "Sergipe possui instrumentos explícitos e nomeados de compras sustentáveis; Paraíba tem maior conexão com logística reversa e cadeia de resíduos."},
    {"Tema": "Inovação, TIC e soluções tecnológicas", "Vantagem": "Paraíba", "Comparação": "Paraíba tem marco estadual de CT&I mais substantivo; Sergipe vincula inovação à estrutura administrativa e ao planejamento das contratações."},
    {"Tema": "Obras públicas, engenharia e BIM", "Vantagem": "Sergipe", "Comparação": "Sergipe apresenta avanço específico em engenharia, arquitetura e BIM, importante para custos, aditivos, produtividade e qualidade do investimento público."},
    {"Tema": "Integridade e qualificação", "Vantagem": "Sergipe", "Comparação": "Sergipe possui camada específica de integridade empresarial; Paraíba enfatiza gestão e fiscalização contratual."}
]
df_se = pd.DataFrame(data_se)

# --- DADOS DINÂMICOS DO DUCKDB (Abas 3 e 4) ---
@st.cache_data
def load_duckdb_data():
    conn = get_db_connection()
    # Dados Teóricos
    query_teoria = """
        SELECT norma_base, score_keynes, score_furtado, score_schumpeter 
        FROM dim_matriz_teorica
        WHERE score_keynes IS NOT NULL
    """
    df_teor = conn.execute(query_teoria).df()
    
    # Dados de Impacto Regional
    query_impacto = """
        SELECT norma_base, mecanismo, reflexos_socioeconomicos, risco_metodologico
        FROM dim_impacto_regional
    """
    df_imp = conn.execute(query_impacto).df()
    
    conn.close()
    return df_teor, df_imp

try:
    df_teoria, df_impacto = load_duckdb_data()
except Exception as e:
    df_teoria = pd.DataFrame()
    df_impacto = pd.DataFrame()
    st.error(f"Atenção: Erro ao carregar dados do DuckDB: {e}")

# --- ABAS (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 IAAN (Federal x PB)", "⚖️ Comparação (PB x SE)", "📚 Aderência Teórica", "🌍 Impactos Regionais"])

# === ABA 1: IAAN ===
with tab1:
    st.markdown("### Indicador de Integração e Autonomia Normativa (IAAN)")
    
    st.info("""
    **Entendendo o Indicador:**
    - **Integração à norma federal (IAAN Global):** Representa o percentual em que a legislação estadual apenas reproduz ou internaliza diretamente as regras da União. Quanto *menor* esse valor, mais o Estado está agindo por conta própria.
    - **Autonomia Normativa Complementar (Espaço de Adaptação):** Representa a margem em que o Estado inovou, complementou ou adaptou fortemente a lei às suas realidades locais. Quanto *maior*, mais autonomia substantiva o Estado exerceu no seu poder de compra.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("IAAN Global (Integração Federal)", "44.6%", delta="- Menos Autonomia", delta_color="inverse")
    with col2:
        st.metric("Autonomia Normativa Complementar", "55.4%", delta="+ Espaço de Inovação Estadual")
        
    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Tipologia das Normas Mapeadas")
        df_tipologia = df_iaan['Tipologia'].value_counts().reset_index()
        df_tipologia.columns = ['Tipologia', 'Quantidade']
        
        fig_tipo = px.bar(
            df_tipologia, 
            x='Quantidade', 
            y='Tipologia',
            orientation='h',
            color='Tipologia',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_tipo.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_tipo, use_container_width=True)

    with col_g2:
        st.subheader("Integração Normativa por Eixo Temático")
        df_sorted_iaan = df_iaan.sort_values(by="IAAN", ascending=True)
        # Transforma para percentual
        df_sorted_iaan['IAAN (%)'] = df_sorted_iaan['IAAN'] * 100
        
        fig_iaan = px.bar(
            df_sorted_iaan, 
            x='IAAN (%)', 
            y='Tema',
            orientation='h',
            color_discrete_sequence=['#CC7952']
        )
        fig_iaan.update_xaxes(range=[0, 100])
        st.plotly_chart(fig_iaan, use_container_width=True)

# === ABA 2: PB x SE ===
with tab2:
    st.markdown("### Matriz Comparativa Interestadual: Paraíba e Sergipe")
    st.markdown("Comparação qualitativa dos temas mais aderentes ao desenvolvimento regional para identificar diferenças institucionais e oportunidades de aprendizado.")
    
    # Renderiza a tabela de forma amigável
    st.dataframe(
        df_se, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Tema": st.column_config.TextColumn("Eixo Temático", width="medium"),
            "Vantagem": st.column_config.TextColumn("Vantagem Comparativa", width="small"),
            "Comparação": st.column_config.TextColumn("Leitura Interpretativa", width="large"),
        }
    )

# === ABA 3: TEORIA ===
with tab3:
    st.markdown("### Aderência Teórica por Autores (Keynes, Furtado, Schumpeter)")
    st.markdown("Intensidade com que cada norma reflete os princípios de demanda efetiva (Keynes), desenvolvimento estrutural e agregação de valor (Furtado) e inovação tecnológica (Schumpeter).")
    
    if not df_teoria.empty:
        # Prepara os dados para o Heatmap (necessário transformar a norma em índice e as colunas como matriz)
        df_heat = df_teoria.set_index('norma_base')[['score_keynes', 'score_furtado', 'score_schumpeter']]
        # Renomeia colunas para visualização
        df_heat.columns = ['Keynes', 'Furtado', 'Schumpeter']
        
        fig_heat = px.imshow(
            df_heat,
            labels=dict(x="Referencial Teórico", y="Norma Base", color="Score de Aderência"),
            x=['Keynes', 'Furtado', 'Schumpeter'],
            y=df_heat.index,
            color_continuous_scale='YlGnBu', # Escala de cor que vai do amarelo claro (0) ao azul escuro (1)
            aspect="auto"
        )
        fig_heat.update_xaxes(side="bottom")
        
        # Define o tamanho do gráfico baseado na quantidade de linhas
        altura_grafico = max(500, len(df_heat) * 30)
        fig_heat.update_layout(height=altura_grafico)
        
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("Não há dados teóricos disponíveis no momento para gerar o Heatmap.")

# === ABA 4: IMPACTOS REGIONAIS ===
with tab4:
    st.markdown("### Dimensão Econômica e Impactos Regionais")
    st.markdown("""
    Esta visão detalha os mecanismos de indução econômica embutidos nas normas estaduais.
    Como os textos lidam com descrições muito qualitativas (reflexos e riscos), a **melhor forma de visualização é uma tabela de dados estruturada**, permitindo a leitura clara dos contrapontos.
    """)
    
    if not df_impacto.empty:
        st.dataframe(
            df_impacto, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "norma_base": st.column_config.TextColumn("Norma/Regra", width="medium"),
                "mecanismo": st.column_config.TextColumn("Mecanismo (Aplicação)", width="medium"),
                "reflexos_socioeconomicos": st.column_config.TextColumn("Reflexos Socioeconômicos Esperados", width="large"),
                "risco_metodologico": st.column_config.TextColumn("Contraponto/Risco", width="large"),
            }
        )
    else:
        st.warning("Dados de impacto regional ainda não disponíveis no banco.")
