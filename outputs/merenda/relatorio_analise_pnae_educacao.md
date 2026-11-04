# 🥗 Relatório Técnico: Análise das Compras do Programa Nacional de Alimentação Escolar (PNAE) e Merenda na Secretaria de Estado da Educação da Paraíba

**Destinatário:** Grupo de Trabalho (GT) de Compras Públicas, Desenvolvimento Regional e Inovação  
**Elaboração:** Núcleo de Engenharia de Dados e Inteligência Analítica do Projeto  
**Base Analítica:** DuckDB (`data/compras_pb.duckdb`), APIs de Dados Abertos de Compras da Paraíba e Dados da Receita Federal  
**Data:** 03 de Novembro de 2026  

---

## 1. Sumário Executivo

Atendendo à diretriz formulada pelo Grupo de Trabalho (GT), este estudo avalia a viabilidade metodológica e empírica de **isolar, monitorar e analisar os processos de compras públicas da alimentação e merenda escolar (PNAE)** no âmbito da **Secretaria de Estado da Educação (SEE-PB)**.

A conclusão é **plenamente afirmativa**: o ecossistema de APIs de compras do Estado da Paraíba (composto por quatro endpoints integrados: `/plano_anual_contratacao`, `/contratacoes`, `/contratos` e `/itens_contratacoes`) possui granularidade suficiente para individualizar o fluxo da merenda escolar desde o planejamento orçamentário até o domicílio fiscal e CNAE dos fornecedores contratados.

### Principais Evidências Encontradas nos Microdados:
1. **Salto de Planejamento Orçamentário (PCA):** Em 2024 e 2025, o planejamento anual de gêneros alimentícios e alimentação registrava **R$ 4,51 milhões/ano**. Em 2026, houve um salto estrutural na dotação planejada da Educação para **R$ 746,47 milhões** (40 milhões de unidades registradas na conta `33.90.30.07 - Gêneros de Alimentação`).
2. **Instrumento Específico de Chamamento Público (Agricultura Familiar):** Localizou-se o processo formal **`22.000.045106.2026`** da SEE-PB, modalidade **Chamamento Público**, fundamentado na **Lei Federal nº 14.628/2023, Art. 4º** (marco legal do PAA e PNAE) destinado à aquisição de alimentos diretamente de produtores e cooperativas da agricultura familiar.
3. **Retenção Territorial de Renda (54,1% Local vs. 45,9% Vazamento Interestadual):**
   - **Retenção na Paraíba (54,07%):** R$ 7,20 milhões na Capital (João Pessoa) e R$ 486 mil no Interior (Catolé do Rocha).
   - **Vazamento de Recursos para Outros Estados (45,93%):** R$ 3,48 milhões para São Paulo (24,45%), R$ 2,48 milhões para o Rio Grande do Norte (17,43%), além de fornecedores em Minas Gerais (2,63%), Rondônia (1,08%), Pernambuco (0,31%) e Santa Catarina (0,02%).

---

## 2. Metodologia de Rastreamento nas APIs Oficiais

A segregação dos dados foi viabilizada pela combinação das seguintes chaves de negócio:

```
[1. PCA: Contas 33903007 / 33903941] 
         │ (Previsão de Demanda)
         ▼
[2. Contratações: Chamamento Público / Pregão (Órgão SEE)]
         │ (Processos Licitatórios: ex. 22.000.045106.2026)
         ▼
[3. Contratos: Órgão 220001 (SEE) e Objeto Alimentar]
         │ (Execução Financeira e CNPJ Contratado)
         ▼
[4. Enriquecimento: CNAE + Município/UF (Receita Federal)]
         │ (Avaliação de Retenção Territorial e Agricultura Familiar)
```

### Detalhamento dos Atributos Técnicos por Endpoint:

| Camada | Endpoint API | Filtro Aplicado | Informação Gerada |
| :--- | :--- | :--- | :--- |
| **Planejamento** | `/plano_anual_contratacao` | `nomeOrgao ILIKE '%EDUCA%'` e `classeGrupo` com códigos `33903007` e `33903941` | Valores totais planejados, quantitativos previstos e custos unitários de referência. |
| **Seleção Pública** | `/contratacoes` | `nomeOrgao ILIKE '%EDUCA%'` e `modalidade = 'CHAMAMENTO PÚBLICO'` ou amparo na `Lei 14.628/2023` | Procedimentos simplificados de credenciamento e chamadas públicas de cooperativas e produtores rurais. |
| **Contratos** | `/contratos` | `nomeOrgao ILIKE '%EDUCA%'` (`codigoOrgao: 220001`) e palavras-chave de alimentação/merenda | Valores empenhados/assinados, prazos de vigência e empresas adjudicadas. |
| **Fornecedores** | `dim_fornecedores_cnae` | Cruzamento pelo CNPJ raiz (14 dígitos) | Classificação Nacional de Atividades Econômicas (CNAE), município sede e classificação territorial (Capital PB, Interior PB, Nordeste, Fora do Nordeste). |

---

## 3. Análise Detalhada dos Resultados

### 3.1. Planejamento no PCA da Secretaria de Educação (2024–2026)

| Exercício | Código Conta | Descrição da Conta Orçamentária | Quantidade Prevista | Preço Médio Ref. | Valor Total Planejado |
| :---: | :---: | :--- | :---: | :---: | :---: |
| **2024** | 33903007 | Gêneros de Alimentação (Consumo) | 13.150 | R$ 135,42 | R$ 1.780.766,00 |
| **2024** | 33903941 | Fornecimento de Alimentação (Serviço PJ) | 133.460 | R$ 20,48 | R$ 2.733.048,64 |
| **2025** | 33903007 | Gêneros de Alimentação (Consumo) | 13.150 | R$ 135,42 | R$ 1.780.766,00 |
| **2025** | 33903941 | Fornecimento de Alimentação (Serviço PJ) | 133.460 | R$ 20,48 | R$ 2.733.048,64 |
| **2026** | 33903007 | Gêneros de Alimentação (Consumo) | 40.016.300 | R$ 9,33 | **R$ 373.239.091,89** |
| **2026** | 33903007 | Gêneros de Alimentação (Consumo - Item 2) | 40.016.300 | R$ 9,33 | **R$ 373.239.091,89** |

> **Nota:** Em 2026, a Secretaria da Educação alocou duas linhas idênticas de R$ 373,2 milhões no PCA, indicando a previsão orçamentária global de **R$ 746,47 milhões** para suporte alimentar contínuo da rede escolar estadual.

---

### 3.2. Contratos Celebrados e Retenção Territorial de Renda

A análise dos contratos ativos identificou **14 contratos formais de alimentação e kits de merenda** na Educação somando **R$ 14,22 milhões**:

| Categoria Territorial | UF | Cidade Sede | Contratos | Fornecedores | Valor Contratado (R$) | Participação (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Capital (PB)** | PB | João Pessoa | 6 | 6 | R$ 7.204.754,37 | **50,65%** |
| **Fora do Nordeste** | SP | Iracemápolis | 1 | 1 | R$ 3.478.267,96 | **24,45%** |
| **Nordeste (Demais UFs)** | RN | Mossoró | 1 | 1 | R$ 2.478.724,62 | **17,43%** |
| **Interior (PB)** | PB | Catolé do Rocha | 1 | 1 | R$ 486.305,32 | **3,42%** |
| **Fora do Nordeste** | MG | Belo Horizonte | 1 | 1 | R$ 374.489,84 | **2,63%** |
| **Fora do Nordeste** | RO | Porto Velho | 1 | 1 | R$ 153.636,00 | **1,08%** |
| **Nordeste (Demais UFs)** | PE | Camaragibe / Paulista | 2 | 2 | R$ 44.475,03 | **0,31%** |
| **Fora do Nordeste** | SC | São José | 1 | 1 | R$ 3.456,50 | **0,02%** |
| **TOTAL GERAL** | - | - | **14** | **14** | **R$ 14.224.109,64** | **100,00%** |

---

### 3.3. Perfil Econômico dos Contratados (Setor e CNAE)

A desagregação das empresas contratadas revela dois padrões distintos de fornecimento:
1. **Serviços de Refeições e Alimentação Coletiva:**
   - *Drop's Buffet e Eventos* (João Pessoa - PB): R$ 6.706.763,70 (CNAE 5620-1 - Serviços de alimentação para recepções/bufê).
   - *Leve Refeições Coletivas* (Mossoró - RN): R$ 2.478.724,62 (CNAE 5611-2 - Restaurantes e similares).
2. **Kits de Merenda, Utensílios de Cozinha e Apoio Logístico:**
   - *Domínios Participações Ltda* (Iracemápolis - SP): R$ 3.478.267,96 (Comércio atacadista).
   - *G Leite dos Santos Vieira* (Catolé do Rocha - PB): R$ 486.305,32 (Comércio varejista).
   - *Santana Werneck Comercial* (Belo Horizonte - MG): R$ 374.489,84.

---

## 4. Recomendações Estratégicas para o Grupo de Trabalho (GT)

Com base nos dados empíricos observados, sugerimos ao GT as seguintes diretrizes para o aprofundamento das políticas públicas:

1. **Monitoramento do Piso Legal de 30% da Agricultura Familiar (Art. 14 da Lei 11.947/2009):**
   - Implementar no painel um medidor em tempo real do percentual das contratações da SEE-PB alocadas via **Chamamento Público** para pequenos produtores e cooperativas locais.
2. **Estratégia de Descentralização e Adensamento Regional (Furtado):**
   - O diagnóstico apontou que **apenas 3,42%** do valor contratado da amostra está sediado no **Interior da Paraíba**, concentrando-se na Capital ou em empresas atacadistas de São Paulo e Rio Grande do Norte. Recomenda-se estimular editais regionalizados por Gerência Regional de Educação (GRE).
3. **Padrão de Centralização vs. Descentralização:**
   - Há uma divisão operacional relevante: parte dos certames de merenda e utensílios é licitada centralizadamente pela Secretaria de Administração (SEAD - processo prefixo `19.000...`) e executada pela Educação (`22.000...`). É fundamental manter os filtros agregados por objeto e órgão beneficiário final.

---

## 5. Artefatos Produzidos e Disponíveis

Todos os artefatos de dados foram gerados e armazenados no repositório do projeto:
- 📂 **Pasta do Módulo:** [`outputs/merenda/`](file:///home/sti-gii/Projetos/PythonProject/portal_compras_publica_pb/outputs/merenda/)
- 📄 **Base Tabular Unificada (CSV):** [`outputs/merenda/dados_pnae_educacao.csv`](file:///home/sti-gii/Projetos/PythonProject/portal_compras_publica_pb/outputs/merenda/dados_pnae_educacao.csv) (delimitador `;` e vírgula decimal, pronto para Excel/PowerBI).
- 💾 **Script de Consultas SQL (DuckDB / DBeaver):** [`outputs/merenda/consultas_pnae_educacao.sql`](file:///home/sti-gii/Projetos/PythonProject/portal_compras_publica_pb/outputs/merenda/consultas_pnae_educacao.sql) (5 blocos analíticos prontos para reuso).
