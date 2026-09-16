# Portal Compras Públicas PB 📊

Este projeto visa criar uma ferramenta analítica avançada para acompanhar e analisar as compras públicas realizadas pelo governo do Estado da Paraíba. O projeto é dividido em módulos integrados (ETL / Teoria Econômica / CAGED / Visualização Streamlit):

1. **Coleta de Legislação (Catálogo Ouro)**: `scripts/coleta_leis.py` faz o parse e download automático das normas essenciais (Federal e Estadual) para cruzamento posterior.
2. **Coleta de Dados de Compras**: `scripts/explora_api_compras_pb.py` varre as APIs governamentais (em modo exploratório ou incremental) e constrói as bases em CSV bruto.
3. **Modelagem Econômica e Risco**: O script `src/etl/enriquecimento_socioeconomico.py` limpa textos e constrói um Star Schema com matrizes clássicas (Keynes, Furtado, Schumpeter) e análises de Risco Metodológico.
4. **Ingestão de Dados Econômicos (CAGED PB)**: `src/caged/ingest_caged.py` baixa e consolida os microdados formais de emprego da Paraíba (2025/2026) nos níveis CNAE de Seção, **Classe (4 dígitos)** e Subclasse, armazenando em Parquet e DuckDB.
5. **Enriquecimento de Localização dos Fornecedores (UF/Município)**: `src/etl/enriquece_fornecedores_uf.py` consulta as APIs de Dados Abertos da Receita Federal (MinhaReceita) para identificar a UF de origem dos fornecedores e calcular a taxa de retenção territorial de renda da Paraíba.
6. **ETL e DuckDB (Analytics)**: `src/etl/build_db.py` transforma toda a massa de CSVs, Parquets e cruzamentos de Teoria vs Gastos em uma base de dados local de alta velocidade (`compras_pb.duckdb`).
7. **Portal Web Streamlit (Multipage)**: Dashboard interativo com Módulo de Compras Públicas, Módulo de Base Legal, Módulo Socioeconômico e Módulo de Curadoria Manual.
8. **Módulo de Curadoria Manual (Autenticado)**: Interface para curadores revisarem, alterarem status (A ser revisado, revisando, revisada) e integrarem novas normas candidatas ao catálogo curado oficial.

---

## 🚀 Como Executar o Projeto

O projeto utiliza a ferramenta moderna `uv` para gestão ultrarrápida de dependências e ambientes virtuais.

### 1. Pré-requisitos
- Tenha o [uv](https://docs.astral.sh/uv/) instalado na sua máquina.

### 2. Instalação
Na raiz do projeto, instale todas as bibliotecas executando:
```bash
uv sync
```
Isso criará a pasta `.venv` automaticamente lendo o `pyproject.toml`.

### 3. Executando as Coletas e Ingestão de Dados

**Passo A: Coletar a Legislação**
```bash
uv run scripts/coleta_leis.py --baixar
```

**Passo B: Extrair Dados da API da Paraíba**
```bash
uv run scripts/explora_api_compras_pb.py --limite-paginas 0
```

**Passo C: Ingerir Microdados do CAGED (Paraíba)**
```bash
PYTHONPATH=. uv run python src/caged/ingest_caged.py --incremental
```

**Passo D: Enriquecer Localização dos Fornecedores (UF/Município)**
```bash
PYTHONPATH=. uv run python src/etl/enriquece_fornecedores_uf.py
```

**Passo E: Rodar a Aplicação Web no Streamlit**
```bash
PYTHONPATH=. uv run streamlit run portal/app.py
```

---

## 🗂️ Estrutura de Diretórios

- `/data/`: Base de dados, catálogo curado, DuckDB e CSVs/Parquets brutos e processados (`raw` e `processed`).
- `/scripts/`: Scripts utilitários de web scraping e consumo de APIs (`coleta_leis.py`, `explora_api_compras_pb.py`).
- `/src/caged/`: Ingestão, tratamento e consolidação do Novo CAGED (`data.py`, `ingest_caged.py`, `secao_classe.csv`).
- `/src/etl/`: Lógica de transformação, enriquecimento socioeconômico e carga (`build_db.py`, `enriquecimento_socioeconomico.py`, `enriquece_fornecedores_uf.py`).
- `/portal/`: Aplicação interativa web Streamlit (Painel Multipage).
  - `app.py`: Página inicial (Home) com apresentação do projeto e equipe.
  - `pages/1_🛍️_Compras_Publicas.py`: Módulo 1 (Dashboard de Contratações, Contratos e Fornecedores).
  - `pages/2_⚖️_Base_Legal.py`: Módulo 2 (Matrizes de IAAN, Comparação PBxSE e Aderência Teórica).
  - `pages/3_📈_Dados_Socioeconomicos.py`: Módulo 3 (Matriz de Associação Compras x Emprego, Retenção Territorial de Renda por UF, Evolução Mensal do CAGED e Rankings por Classe CNAE).
  - `pages/4_📝_Curadoria_Manual.py`: Módulo 4 (Interface de Login e Curadoria para Triagem, Revisão e Validação da Base Oficial).
- `/documentacao/`: Referenciais teóricos, relatórios em PDF e guia de ingestão do CAGED (`estrategia_ingestao_caged.md`).

---

## 📈 Status de Desenvolvimento

- **[✓] Banco Analítico (DuckDB):** Estruturado com tabelas de compras, matrizes teóricas, séries do CAGED e dimensões geográficas de fornecedores.
- **[✓] Módulo 1 (Compras Públicas):** Implementado com consultas SQL rápidas e painéis interativos.
- **[✓] Módulo 2 (Base Legal):** Matrizes visuais de IAAN e comparativo PB x SE.
- **[✓] Módulo 3 (Dados Econômicos - CAGED & Retenção Territorial):** Mapeamento por Classe CNAE, Matriz de Associação Compras x Emprego e **Taxa de Retenção Territorial de Renda por UF (PB x Outros Estados)**.
- **[✓] Módulo 4 (Curadoria Manual):** Módulo restrito com autenticação para revisão e homologação de normas para a base oficial.
- **[ ] Próximos Módulos:** Incorporação do PIB municipal e VAB (Valor Adicionado Bruto).

---

## 📜 Licença e Direitos Autorais

Este projeto está sob a licença open-source **MIT License** (consulte o arquivo [LICENSE](LICENSE) para maiores detalhes).

- **Coordenação do Projeto**: Prof. Dr. Paulo Fernando Cavalcanti
- **Desenvolvimento e Colaboração**: Evandro Farias Rocha
- **Instituições parceiras**: UFPB / SUDENE / Governo do Estado da Paraíba

---

## 🤖 Nota de Transparência e Apoio Tecnológico em IA

Este projeto adota boas práticas de integridade e transparência no uso de inteligência artificial. 

> *O desenvolvimento da arquitetura computacional, pipelines de ETL, scripts de raspagem e componentes visuais Streamlit contaram com o auxílio autônomo da ferramenta de **Agentes de IA (Google Gemini Agentic Coding / Antigravity Agentic Framework)** como suporte à programação, refinamento de código e estruturação de bases analíticas.*


