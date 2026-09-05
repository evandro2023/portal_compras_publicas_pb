---
name: monitoramento-leis
description: Usada para raspar e monitorar novos decretos, leis e normativas de compras públicas no Diário Oficial e portais da Paraíba e Sergipe, comparando com o catálogo local.
---

# Skill: Monitoramento de Leis e Decretos (Curadoria Normativa)

## Objetivo
Esta skill instrui o agente a monitorar ativamente novas regulamentações estaduais (Decretos, INs, Portarias, Leis) publicadas nos portais governamentais, extrair seus dados e comparar com a base de dados interna do projeto (`data/catalogo_curado_leis.csv`) para propor atualizações metodologicamente consistentes.

## Gatilhos (Quando usar)
Use quando o usuário solicitar: "verifique se há novas leis", "atualize o catálogo", "monitore o site de compras", ou durante rotinas de manutenção periódica.

## Instruções de Execução

### Passo 1: Busca de Dados (Scraping)
1. Acesse o portal da Central de Compras da PB, como a URL de transparência da Lei 14.133 (`https://centraldecompras.pb.gov.br/appls/sgc/transparencia.nsf/Web?OpenAgent&pageClassName=DocumentosLei14133Dialog`) ou o Diário Oficial do Estado (DOE-PB).
2. Extraia o conteúdo usando a ferramenta `read_url_content` ou o `browser_subagent`. 
3. Caso a página utilize muita renderização client-side e falhe via curl/URL reader, priorize o subagente de navegação para interagir com o DOM e extrair tabelas.

### Passo 2: Extração e Padronização
Identifique atos normativos na resposta (buscando pelas palavras Decreto, Lei, Portaria Conjunta, Instrução Normativa).
Extraia:
- **Esfera** (ex: PB, SE, Federal)
- **Identificador** (ex: Decreto 46.187)
- **Ano** (ex: 2025)
- **Tipo** (ex: Decreto, IN, Lei)
- **Tema Principal** (resuma o assunto, ex: Fase Preparatória)
- **URL** (verifique se a URL precisa do prefixo oficial do estado, evite links quebrados)

### Passo 3: Comparação (Diffing)
1. Leia o arquivo local `data/catalogo_curado_leis.csv`.
2. Compare os identificadores encontrados no site com os existentes no CSV local.
3. Filtre apenas os documentos **novos** (não cadastrados no CSV).

### Passo 4: Curadoria e Apresentação
Como este projeto adota uma abordagem de "catálogo curado", **NUNCA modifique o arquivo CSV automaticamente sem permissão**.
1. Salve as novas leis candidatas no arquivo: `outputs/tables/candidatas_normas.csv` (formato: esfera,identificador,ano,título,tema detectado,URL,fonte,status_revisao).
2. Apresente os resultados ao usuário em uma tabela formatada no chat (ou em um Artifact `relatorio_monitoramento.md`).
3. Destaque quais normas impactam diretamente a Teoria Econômica ou as Custos de Transação (ex: leis sobre dispensa de licitação).
4. Peça o "De Acordo" do usuário para incluí-las definitivamente no `catalogo_curado_leis.csv` e recalcular o IAAN.
