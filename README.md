# Portal Compras Públicas PB 📊

Este projeto visa criar uma ferramenta analítica avançada para acompanhar e analisar as compras públicas realizadas pelo governo do Estado da Paraíba. O diferencial doO projeto é dividido em três grandes módulos (ETL / IA / Visualização):

1. **Coleta de Legislação (Catálogo Ouro)**: `scripts/coleta_leis.py` faz o parse e download automático das normas essenciais (Federal e Estadual) para cruzamento posterior.
2. **Coleta de Dados de Compras**: `scripts/explora_api_compras_pb.py` varre as APIs governamentais (em modo exploratório ou incremental) e constrói as bases em CSV bruto.
3. **Modelagem Econômica e Risco**: O script `src/etl/enriquecimento_socioeconomico.py` limpa textos e constrói um Star Schema com matrizes clássicas (Keynes, Furtado, Schumpeter) e análises de Risco Metodológico.
4. **ETL e DuckDB (Analytics)**: `src/etl/build_db.py` transforma toda a massa de CSVs e cruzamentos de Teoria vs Gastos em uma base de dados local de alta velocidade (`compras_pb.duckdb`).
5. **Automação (CI/CD)**: Integrado ao GitHub Actions para carga automática incremental toda semana.
- Cálculo do **IAAN (Índice de Aderência e Alinhamento Normativo)**.
- Dashboard interativo desenvolvido em Streamlit, alimentado por um motor analítico DuckDB.

---

## 🚀 Como Executar o Projeto

O projeto utiliza a ferramenta moderna `uv` para gestão ultrarrápida de dependências e ambientes virtuais, abandonando o `conda` ou `pip` manual.

### 1. Pré-requisitos
- Tenha o [uv](https://docs.astral.sh/uv/) instalado na sua máquina.

### 2. Instalação
Na raiz do projeto, instale todas as bibliotecas executando:
```bash
uv sync
```
Isso criará a pasta `.venv` automaticamente lendo o `pyproject.toml` ou `requirements.txt`.

### 3. Executando as Coletas de Dados (Etapa 1)

O projeto foi dividido em camadas de dados (Pipeline ETL).

**Passo A: Coletar a Legislação**
Baixa os normativos listados no catálogo curado em `data/catalogo_curado_leis.csv`.
```bash
uv run scripts/coleta_leis.py --baixar
```

**Passo B: Extrair Dados da API da Paraíba**
Consome os endpoints oficiais da Paraíba buscando contratos dos anos (2024, 2025, 2026).
Para rodar em modo seguro (amostra de 2 páginas), use:
```bash
uv run scripts/explora_api_compras_pb.py --limite-paginas 2
```
Para rodar na base inteira, use:
```bash
uv run scripts/explora_api_compras_pb.py --limite-paginas 0
```
Os dados brutos serão salvos na pasta `data/raw/compras_pb/`.

**Passo C: Construir o Banco de Dados (DuckDB)**
Lê todos os CSVs brutos coletados e consolida na base de alta performance.
```bash
uv run src/etl/build_db.py
```
Isso gerará o arquivo principal `data/compras_pb.duckdb` que alimentará o portal.

---

## 🗂️ Estrutura de Diretórios

- `/data/`: Base de dados, catálogo curado, DuckDB e CSVs brutos (`raw`).
- `/scripts/`: Scripts utilitários de web scraping e consumo de APIs (`coleta_leis.py`, `explora_api_compras_pb.py`).
- `/src/etl/`: Lógica de transformação e carga (`build_db.py`).
- `/portal/`: Aplicação interativa web Streamlit (Painel Multipage).
  - `app.py`: Página inicial (Home) com apresentação e equipe.
  - `pages/1_🛍️_Compras_Publicas.py`: Módulo 1 (Dashboard interativo conectado ao DuckDB focado em Contratações, Contratos e Análise de Impacto Regulatório/Econômico).
  - `pages/2_⚖️_Base_Legal.py`: Módulo 2 (Matrizes qualitativas de IAAN, Comparação PBxSE e Mapa de Calor de Aderência Teórica de Keynes/Furtado/Schumpeter).
- `/documentacao/`: Referenciais teóricos e relatórios em PDF.
- `/outputs/`: Tabelas, gráficos gerados, e arquivos de rastreio de logs.

## 📈 Status de Desenvolvimento

- **[✓] Banco Analítico (DuckDB):** Estruturado com tabelas de compras e matrizes teóricas.
- **[✓] Módulo 1 (Compras Públicas):** Implementado com leitura local (`read_only=True`) e painéis interativos.
- **[✓] Módulo 2 (Base Legal):** Matrizes visuais complexas traduzidas em abas e gráficos de calor.
- **[ ] Integração CAGED e RAIS:** Próximo passo para aprofundar impacto socioeconômico.
