# CLAUDE.md

Guia para agentes de IA trabalhar neste projeto.

## Breve contextualização teórica do projeto

A forma de organização do sistema econômico nordestino foi produzida e permanece se reproduzindo, ao longo dos últimos dois séculos, através de diversos processos, mecanismos e instrumentos de natureza pública e privada. O papel que a Estratégia Nacional de Contratações Públicas (ENCP) pode desenvolver na região Nordeste está fortemente condicionado pelo processo histórico que estruturou a economia, a sociedade e política regional. O Estado brasileiro foi formado tendo como centro político e econômico a região sudeste e este contexto histórico e geográfico moldou a estrutura do Estado Nacional, seus instrumentos de ação e seus objetivos. Este estudo busca propor uma nova perspectiva para os formuladores da ENCP. Esta nova perspectiva busca revelar e destacar aspectos teóricos e empíricos considerados não apenas relevantes, mas críticos para que a ENCP possa efetivamente produzir os resultados e impactos que, de acordo com a análise do conteúdo da base documental analisada, motivaram sua elaboração e transformação em política pública do Estado brasileiro. 
É entendimento deste estudo que estes aspectos estão ausentes, minimizados ou distorcidos nos fundamentos teórico-metodológicos de natureza econômico-inovativa, político-institucional e socioambiental que dão suporte à atual ENCP. A intencionalidade de objetivos definida pelos formuladores e executores da ENCP se defronta com a realidade histórica construída no território nacional, em suas formas de integração, diversidade e heterogeneidade estrutural
Neste estudo, busca-se delimitar os aspectos histórico-estruturais do território nacional e regional e os contornos político-institucionais da ação do Estado Nacional no planejamento e execução das políticas públicas e do uso do instrumento das contratações públicas para a promoção do desenvolvimento sustentável. Dado este contexto histórico-estrutural nacional e regional, o estudo se concentra nos aspectos específicos do arcabouço legal e regulatório da ENCP e de suas contrapartes no estado da Paraíba. O estudo deve investigar como o desenho da ENCP reflete e condiciona como as contratações públicas poderão impactar as regiões do território nacional e sua heterogênea estrutura produtiva. Também se busca conexões entre este desenho institucional da ENCP e a forma como o estado da Paraíba legisla e regulamenta, com suas especificidades, as contratações públicas nos territórios da economia paraibana. Esta investigação permitirá identificar, inicialmente, como se organizam e manifestam concretamente os processos e instrumentos das contratações públicas para o desenvolvimento sustentável no estado da Paraíba. 
Para este intuito, recorreu-se à análise documental da legislação do estado e das bases de dados das compras públicas de forma global, destacando a magnitude das contratações, os tipos de bens e serviços contratados, o uso de instrumentos de preferências por porte empresarial, por critérios ambientais e para inovação tecnológica.


## Objetivo do projeto

O objetivo deste projeto é criar uma ferramenta que permita acompanhar, analisar as compras públicas realizadas pelo governo da Paraíba, compará-las com a legislação de compras públicas do governo da Paraíba com a legislação federal, com foco em desenvolvimento regional, inovação, sustentabilidade e transformação produtiva.

O projeto também incorpora uma comparação interestadual inicial entre Paraíba e Sergipe. Essa comparação deve permanecer separada do IAAN principal, que mede a relação Paraíba x Governo Federal.

O portal será composto por 2 módulos principais:

- Módulo de análise de compras públicas realizadas pelo governo do estado da Paraíba
- Módulo de comparação da legislação de compras públicas do governo da Paraíba com a legislação federal e de sergipe, com foco em desenvolvimento regional, inovação, sustentabilidade e transformação produtiva.   

## O projeto será dividido em 2 etapas principais:

### Etapa 1

#### Criar um portal com as informações sobre as compras públicas do governo do estado da Paraíba.

##### Ações sugeridas para o Agent de IA

* Acessar os dados do sistema de compras públicas do estado da Paraíba por meio de APIs: https://api.dados.pb.gov.br/swagger/#/compras. Baixar os dados de

- /compras/contratacoes
- /compras/contratos
- /compras/itens_contratacoes
- /compras/plano_anual_contratacao

Verificar documento no diretório do projeto:

- /documentacao/compras/contratacoes
- /documentacao/compras/contratos
- /documentacao/compras/itens_contratacoes
- /documentacao/compras/plano_anual_contratacao

* Estrutura os dados em um banco de dados de preferência DuckDB.

As tabelas do banco devem ser criadas com base nas APIs, seguindo a estrutura das tabelas e seus possíves relacionamentos. A API deve retornar dados para os anos de 2024, 2025 e 2026 O banco de ser capaz de responder as seguintes perguntas de forma rápida:

-- Contratações
- Quais foram os órgãos do da Paraíba que mais contrataram, por ano?
- Quais foram os objetos mais contratados, por ano?
- Quais foram as modalidades de compras públicas mais utilizadas no governo da Paraíba, por ano?
- Qual o amparo legal que fundamenta as compras públicas no estado da Paraíba? Essa informação vai se conectar a outras tabelas com informações específicas sobre leis e normas que fomentam o desenvolvimento regional e a transformação produtiva.
- Quais foram os valores gastos em compras públicas na Paraíba, por ano? 

-- Contratos
- Quais foram os contratos celebrados por órgão, por ano?
- Quais foram os contratos celebrados por fornecedor, por ano?
- Quais foram os contratos celebrados por modalidade de compra pública, por ano?
- Quais as empresas mais contratadas? Quanto cada uma recebeu, por ano?
- Quais foram os objetos mais contratados, por ano?
- Quais foram os valores gastos em contratos por modalidade de compra pública, por ano?
- Quais foram os valores gastos em contratos por fornecedor, por ano?

-- Itens de contratações
- Quais foram os itens de contratações por modalidade de compra pública, por ano?
- Quais foram os itens de contratações por fornecedor, por ano?
- Quais foram os itens de contratações por tipo de objeto, por ano?
- Quais foram os itens de contratações por órgão, por ano?
- Quais foram os itens de contratações por tipo de bem ou serviço, por ano?

-- Plano anual de contratação
- Quais foram os órgãos que realizaram plano anual de contratação por ano?
- Quais foram os objetos mais contratados por ano?
- Quais foram as modalidades de compras públicas mais utilizadas no governo da Paraíba por ano?
- Qual o amparo legal que fundamenta as compras públicas no estado da Paraíba? Essa informação vai se conectar a outras tabelas com informações específicas sobre leis e normas que fomentam o desenvolvimento regional e a transformação produtiva.
- Quais foram os valores gastos em compras públicas na Paraíba por ano? 

* Visualização dos dados

 O portal deve ser desenvolvido com streamlit e as consultas devem ser feitas de forma rápida. O portal deve ser capaz de responder as perguntas acima de forma interativa, permitindo filtros por ano, modalidade, órgão, fornecedor, tipo de objeto e tipo de bem ou serviço.

* O portal deve ter as seguintes funcionalidades (Status Atualizado):

- [x] Página inicial com um resumo do projeto e equipe;
- [x] Página de Compras Públicas integrando dados de Contratações e Contratos por Órgão, Fornecedor e Modalidade (Dashboard iterativo em `1_🛍️_Compras_Publicas.py`);
- [x] Página de Base Legal e Regulatória, contendo IAAN, Matriz Comparativa PBxSE, Mapa de Calor Teórico e Impactos Regionais (`2_⚖️_Base_Legal.py`);
- [ ] Página de itens de contratações e plano anual de contratação;
- [ ] Incorporação das bases CAGED e RAIS (Módulo 3 planejado).

* Bibliotecas a serem utilizadas:

- pandas
- streamlit
- sqlalchemy
- requests
- json
- plotly
- outras que se fizerem necessárias

* Estrutura do visual

Mantenha uma paleta de cores que possa se identificar com a página da SUDENE https://www.gov.br/sudene/pt-br e do governo Federal. Para a criação de gráficos e elementos visuais, utilize as seguintes diretrizes:

- os gráficos devem ser responsivos e interativos, permitindo filtros por ano, modalidade, órgão, fornecedor, tipo de objeto e tipo de bem ou serviço;
- Utilize o plotly para criação de gráficos;
- Mantenha uma organização visual clara e objetiva, com informações bem distribuídas e fáceis de encontrar;
- Crie um botão de download para os dados em csv ou excel;
- O portal deve ser responsivo e acessível em dispositivos móveis;
- O portal deve ter uma documentação completa e atualizada disponível para download.
- O portal deve seguir as diretrizes de acessibilidade do governo federal.

### Etapa 2

#### Mapear na legislação federal de compras públicas quais os objetivos, instrumentos e mecanismos que possibilitam promover transformação produtiva;

1) mapear na legislação federal de compras públicas quais os objetivos, instrumentos e mecanismos que possibilitam promover transformação produtiva;
2) identificado na legislação federal, vasculhar a legislação estadual para identificar se há algo igual, similar ou próximo.
3) Vasculhar na ENCP e na Lei nº 14.133/2021 quais instrumentos e mecanismos impactam a política nacional de desenvolvimento regional, com foco na diversificação produtiva e agregação de valor.


* O levantamento de informações das Leis e normas devem ser capaz de responder as seguintes perguntas:

- Onde a legislação da Paraíba copia a legislação federal?
- Onde existe mera adaptação da legislação federal às especificidades do estado (valor da compra pública por produtor na agricultura familiar, por exemplo)?
- Onde existe complementação estadual, incluindo critérios novos, restrições ou possibilidades não prevista na lei federal?
- Onde existe critérios diferentes (não-complementares) entre a legislação federal e a estadual (sem que houvesse violação da lei federal, obviamente)?
- Identificar se na legislação federal e estadual há alguma previsão legal, instrumentos e objetivos para "transformação da estrutura produtiva regional, estadual ou local". Exemplo:

Quando o arcabouço regulatório favorece as MPE e as compras locais de alimentos, ele está impulsionando o tecido econômico local, mas está  reforçando o perfil produtivo e tecnológico territorial. 
Comprar macaxeira dos APLs vizinhos às escolas da Paraíba é correto, pois comprar de um APL do estado vizinho seria estúpido e comprar miojo seria criminoso, mas o lado problemático é que esta compra pública, isoladamente, também reforça um perfil produtivo de baixa intensidade tecnológica e baixa remuneração.
O que o Nordeste precisa, e a Paraíba em particular, é transformar seu tecido produtivo em direção a uma maior complexidade econômica.

## Regra de Ouro

Use somente os dados de leis que estejam associadas às contas públicas (estadual e federal). 

## Fonte de Dados

- Site da Assembleia Legislativa da Paraíba: https://www.al.pb.leg.br/leis-estaduais
- Sites do Governo Federal
- Planalto: https://www.planalto.gov.br/
- FNDE: https://www.gov.br/fnde/
- Sistema Gestor de Compras da Paraíba: https://centraldecompras.pb.gov.br/
- SECLOG/SE: https://www.se.gov.br/seclog/legislacao
- Assembleia Legislativa de Sergipe: https://aleselegis.al.se.leg.br/

## Conteúdo Sugerido: 

### Leis do Governo Federal que estrutura a legisliação de compras do Governo Federal 

Consular na web Leis do governo Federal que tratam especificamente de compras governamentais e suas implicações no desenvolviemnto regional. Exemplo:

- Lei Federal nº 14.133/2021e o Marco Legal das Startups (Lei Complementar nº 182/2021).

- Marco Legal da Ciência, Tecnologia e Inovação da Paraíba (Lei Estadual nº 12.191/2022):Estabelece como princípio expresso a "utilização do poder de compra do Estado para fomento à inovação".

- Contrato Público de Soluções Inovadoras (CPSI): utiliza o rito do Marco Legal das Startups para contratar testes de soluções inovadoras desenvolvidas por startups ou empresas de tecnologia, permitindo a validação de protótipos antes de eventuais compras em escala.

- Procedimento Auxiliar de Credenciamento (Decreto Estadual nº 45.710/2024):credenciamento contínuo de soluções tecnológicas e prestadores de serviços em mercados dinâmicos e fluidos para atendimento das demandas da Administração Direta e Indireta.

- Diálogo Competitivo (Lei nº 14.133/2021):Modalidade aplicável no estado quando a administração possui uma necessidade complexa ou tecnológica, mas não domina a solução técnica ideal, permitindo conversações prévias com potenciais fornecedores antes da proposta final.

- Resolução CD/FNDE Nº 11, DE 22 DE JUNHO DE 2026 https://www.gov.br/fnde/pt-br/acesso-a-informacao/legislacao/resolucoes/2026/resolucao-cd-fnde-no-11-de-22-de-junho-de-2026

- Decreto Federal nº 11.630/2023: governança de inovações e aquisições do Novo PAC, com atenção a margens de preferência, adensamento produtivo e inovação tecnológica.

- Decreto Federal nº 12.705/2025: Taxonomia Sustentável Brasileira, especialmente pelo uso potencial em compras públicas, investimentos, atividades sustentáveis e redução de desigualdades regionais.

- Decreto Federal nº 12.771/2025: Estratégia Nacional de Contratações Públicas para o Desenvolvimento Sustentável, com eixos econômico, social, ambiental e de gestão.


### Leis do Governo do Estado da Paraíba que tratam das compras públicas

Consultar na web (https://www.al.pb.leg.br/leis-estaduais) e filtrar somente as leis que tratam das compras públicas, incluindo compras da administração direta e indireta. Exemplo:

- Estruturada pela Lei Federal nº 14.133/2021 (Nova Lei de Licitações e Contratos) e complementada pela Lei Complementar Federal nº 123/2006 (Estatuto da Micro e Pequena Empresa). No âmbito estadual.

- Decreto Estadual nº 42.967/2022: Regulamenta o procedimento administrativo para a pesquisa de preços para aquisição de bens e contratação de serviços em geral na Administração Pública Estadual direta, autárquica e fundacional.

- Decreto Estadual nº 43.975/2023: Dispõe sobre as regras para a gestão e fiscalização de contratos administrativos no âmbito do Estado da Paraíba, fixando atribuições dos gestores e fiscais técnicos.

- Decreto Estadual nº 45.710/2024: Regulamenta o procedimento auxiliar de credenciamento (art. 79 da Lei 14.133/2021) no âmbito do Estado da Paraíba, permitindo chamamentos públicos para contratações paralelas, mercados fluidos e seleção a critério de terceiros.

- Lei Estadual nº 8.292/2007: Dispõe sobre a adaptação da Lei Geral da Micro e Pequena Empresa no âmbito do estado da Paraíba

- Decreto Estadual nº 32.056/2011: Estabelece regras simplificadas e favorecidas para compras e licitações públicas do governo estadual voltadas a ME e EPP.

- Decreto Estadual referente à Fase Preparatória: Disciplina a elaboração do Estudo Técnico Preliminar (ETP), Termo de Referência (TR) e matrizes de risco nas contratações estaduai

## A análise deve ser feita sob a ótica do desenvolvimento regional e inovação.  Assim, os seguintes pontos devem ser observados:

 - O Estatuto Estadual da ME e EPP que garante o tratamento diferenciado, favorecido e simplificado às MPEs nas licitações do Estado, em alinhamento com a LC nº 123/2006.

- Tratamento Favorecido nas Licitações Públicas do Estado: Aplicação das prerrogativas estaduais e federais nas compras governamentais, tais como:

- Licitações Exclusivas: Destinadas preferencialmente a MPEs para itens com valor estimado de até R$ 80.000,00.

- Reservas de Cotas: Reserva de cota de até 25% do objeto em licitações para aquisição de bens divisíveis.

- Subcontratação Compulsória: Previsão em editais para exigência de subcontratação de MPEs locais.

- Margem de Preferência Regional: Priorização de contratação de MPEs sediadas local ou regionalmente até o limite de 10% do melhor preço válido em certames promovidos pelo Estado.

- Foco em Sustentabilidade Ambiental e Critérios ESG: Critérios de Sustentabilidade na Fase Preparatória (ETP e TR): Regulamentados para exigir a inclusão de critérios ambientais, como análise do ciclo de vida do produto, eficiência energética, utilização de matérias-primas de origem reciclada/sustentável e comprovação de baixa pegada de carbono.

- Decreto Estadual nº 43.346/2022: Estabelece diretrizes estaduais para a Logística Reversa e o sistema de certificação de reciclagem (Sisrev-Recicla+PB). O cumprimento das obrigações de logística reversa e licenciamento ambiental (comprovado via Sudema) serve como requisito ou qualificação técnica/ambiental em licitações do Estado.

- Política Estadual de Resíduos Sólidos e Compras Verdes: Diretrizes estaduais para a destinação adequada de resíduos e priorização de fornecedores que comprovem gestão sustentável de resíduos e redução do consumo de plástico de uso único em serviços contratados pelo governo.

### Leis e atos do Governo do Estado de Sergipe

Usar Sergipe como estado de comparação, principalmente por meio de fontes oficiais da SECLOG/SE e ALESE. Nesta etapa, considerar:

- Lei Estadual SE nº 8.747/2020: tratamento diferenciado e simplificado para ME/EPP, agricultores familiares, produtores rurais pessoa física, MEIs e cooperativas nas contratações públicas estaduais.
- Lei Estadual SE nº 9.493/2024: altera a Lei nº 8.747/2020.
- Lei Estadual SE nº 9.315/2023: define o agente de contratação para aplicação da Lei nº 14.133/2021.
- Decreto Estadual SE nº 342/2023: estabelece regras e diretrizes para aquisição de bens e contratação de serviços em geral sob a Lei nº 14.133/2021.
- Decreto Estadual SE nº 368/2023: estabelece regras para obras e serviços de engenharia e arquitetura, com atenção ao uso de BIM.
- Decreto Estadual SE nº 567/2024: Plano de Contratações Anual de bens, serviços, obras e soluções de TIC.
- Decreto Estadual SE nº 622/2024: Programa Estadual de Contratações Públicas Sustentáveis.
- Decreto Estadual SE nº 623/2024: Selo Socioambiental no Poder Executivo Estadual.
- Lei Estadual SE nº 8.866/2021: Programa de Integridade nas empresas que contratem com a Administração Pública do Estado de Sergipe.

## Perspectiva Socioeconômica e Dimensão Econômica

A análise deve incorporar um tópico específico sobre o contexto do desenvolvimento regional e os reflexos socioeconômicos potenciais das legislações analisadas. Além da comparação jurídica, o relatório deve examinar como as normas de compras públicas podem influenciar:

- transformações produtivas nos setores alcançados pelo gasto público;
- diversificação produtiva e ampliação da base local de fornecedores;
- agregação de valor em bens, serviços, tecnologia, alimentos regionais e soluções sustentáveis;
- formalização, profissionalização e qualificação de ME/EPP, agricultores familiares, startups, ICTs, cooperativas e prestadores locais;
- efeitos territoriais sobre emprego, renda, circulação local de recursos públicos, inclusão produtiva e fortalecimento de cadeias regionais.

### Associar as perspectivas Socioeconômicas e Dimensão Econômica à luz dos seguintes autores:

- Keynes: compras públicas como demanda efetiva e ativação de renda, emprego e produção.
- Furtado: desenvolvimento regional, estrutura produtiva, subdesenvolvimento, diversificação e agregação de valor.
- Schumpeter: inovação, mudança tecnológica, novas combinações produtivas e aprendizagem empresarial.

Todas as informações de Leis, normas e atos do Governo Federal, do Goveno da Paraíba e do Estado de Sergipe devem ser armazenadas no banco de dados do DuckDB em tabelas específicas. 

- As tabelas devem estar relacionadas entre si e devem conter as seguintes informações:
  - Identificação da norma:
  -- Nome completo da norma
  -- Sigla da norma
  -- Tipo da norma (Lei, Decreto, Portaria, Resolução, etc.)
  -- Data da norma
  -- Versão da norma
  -- URL da norma
- Perspectiva Socioeconômica e Dimensão Econômica
  -- transformações produtivas nos setores alcançados pelo gasto público;
  -- diversificação produtiva e ampliação da base local de fornecedores;
  -- agregação de valor em bens, serviços, tecnologia, alimentos regionais e soluções sustentáveis;
  -- formalização, profissionalização e qualificação de ME/EPP, agricultores familiares, startups, ICTs, cooperativas e prestadores locais;
  -- efeitos territoriais sobre emprego, renda, circulação local de recursos públicos, inclusão produtiva e fortalecimento de cadeias regionais.

- Aderência Teórica
  - Keynes
  - Furtado
  - Schumpeter

- Regra de ouro

-- Não invente informações que não estão nas Leis, normas etc.

O projeto deve gerar `outputs/tables/dimensao_economica_desenvolvimento_regional.csv` e `outputs/tables/aderencia_teorica_autores.csv`. A pontuação de aderência teórica é interpretativa e derivada da triagem temática e da intensidade socioeconômica; não trate os pesos como citação direta dos autores pelas normas.


## Estrutura dos scripts

Crie um estrutura de projeto com diretórios específicos de acordo com o projeto.

- `portal/`: diretório principal contendo a aplicação interativa desenvolvida em Streamlit.

- `scripts/coleta_leis.py`: script reprodutível que faz uma varredura na web e coleta as leis federais e estaduais necessárias para a análise. Baixa as leis em pdf ou html e armazena no diretorio data/leis/federais e data/leis/estaduais.  

- `scripts/explora_api_compras_pb.py`: script exploratório para testar a API pública de compras da Paraíba, inicialmente o endpoint:
-- `/compras/contratacoes`, salvando uma amostra controlada em `data/raw/compras_pb/contratacoes.csv`.
-- `/compras/contratos`, salvando uma amostra controlada em `data/raw/compras_pb/contratos.csv`
-- `/compras/itens_contratados`, salvando uma amostra controlada em `data/raw/compras_pb/itens_contratados.csv`
-- `/compras/plano_anual_contratacao`, salvando uma amostra controlada em `data/raw/compras_pb/plano_anual_contratacao.csv`

### Modelo conceitual e indicadores

- Para auxiliar na elaboração dos indicadores tome como base o documento /documentacao/relatorio_compras_pb_gov.pdf

- Crie um documento `analise_compras_pb_gov.ipynb` com a análise em Python para facilitar a compreenção das etapatas realizadas no projeto. 

- Crie um arquivo teste.py na pasta `/tests` para testar as APIS .

- Crie um relatório `relatorio_compras_pb_gov.qmd`: relatório fonte em Quarto saidas em html e pdf com os gráficos e tabelas para um ano específicoas tabelas em latex e análises das leis, em pt-br.
- `relatorio_style.css`: estilos do relatório HTML.
- `relatorio_compras_pb_gov.html`: relatório final em HTML.
- `relatorio_compras_pb_gov.pdf`: relatório final em PDF.
- `outputs/figures/`: gráficos exportados em PNG.
- `outputs/tables/`: tabelas exportadas em CSV.
- `outputs/tables/matriz_comparativa_pb_se.csv`: matriz comparativa interestadual entre Paraíba e Sergipe.
- `outputs/tables/dimensao_economica_desenvolvimento_regional.csv`: dimensão econômica baseada em teoria do desenvolvimento regional.
- `outputs/tables/aderencia_teorica_autores.csv`: aderência teórica por norma a Keynes, Furtado e Schumpeter.
- `outputs/cache/`, `outputs/mplconfig/` e `outputs/texmf-var/`: caches e arquivos auxiliares de renderização.
- `data/leis/estaduais/sergipe/`: textos normativos de Sergipe baixados a partir do catálogo curado.
- `data/raw/compras_pb/`: amostras brutas controladas dos endpoints reais de compras públicas do Estado da Paraíba.

- Tome como base os arquivos compras_federal_pb_exemplo.pdf e replique a base conceitual e o calculo de IAAN. Sugira outros indicadores ou métricas que podem ser usados para enriquecer a análise.  

- Matriz de Mapeamento, Tipologia Comparativa e Contribuição para o IAAN: Defina a tipologia (Reprodução Literal, Adaptação Contextual, Complementação/Inovação Substantiva, Divergência Não-Conflitante) para cada tema e justifique a valoração do peso IAAN (0 = não contribui para a integração; 0.25 = baixa contribuição; 0.50 = média contribuição; 0.75 = alta contribuição; 1 = reprodução literal exata). Inclua na coluna de descrição informações relevantes como a base legal federal, dispositivo estadual correspondente e observações sobre a interpretação e aplicação prática. 

## Próximos Passos a Implementar

### Catálogo curado

O projeto deve manter um catálogo curado de normas já verificadas, com fontes, URLs, caminhos locais, esfera federativa, tema e status de revisão. Esse catálogo é a base principal da matriz comparativa e do cálculo do IAAN, pois evita que normas irrelevantes ou ainda não validadas entrem automaticamente na análise.

### Triagem de aderência temática

Antes de consolidar uma norma na análise, o projeto deve registrar uma triagem de aderência temática. Essa triagem deve avaliar, em escala de 0 a 1, a relação de cada norma com as seguintes dimensões: compras públicas, desenvolvimento regional, inovação, sustentabilidade e contas públicas.

A triagem não deve funcionar como filtro automático de exclusão. Seu papel é diagnóstico e metodológico: explicitar se a norma possui aderência central, relevante, indireta, periférica ou inexistente em cada dimensão. Isso evita que normas descontextualizadas contaminem a leitura do IAAN, mas preserva a possibilidade de manter normas de baixa aderência em alguma categoria quando houver justificativa analítica.

O resultado deve ser salvo em `outputs/tables/triagem_aderencia_normas.csv`, contendo pelo menos: esfera, identificador, ano, título, scores por categoria, score total, classe de aderência, status de triagem, justificativa e observação metodológica.

### Busca exploratória

Como evolução importante do `scripts/coleta_leis.py`, implementar uma etapa de busca exploratória por novas leis, decretos, resoluções e atualizações normativas. A busca deve consultar fontes como Assembleia Legislativa da Paraíba, Sistema Gestor de Compras da Paraíba, Planalto, FNDE e demais sites oficiais federais, usando palavras-chave como: licitação, compras públicas, contratação pública, desenvolvimento regional, desenvolvimento local, inovação, startups, CPSI, credenciamento, microempresa, empresa de pequeno porte, agricultura familiar, alimentação escolar, sustentabilidade e logística reversa.

O resultado dessa busca deve ser salvo em `outputs/tables/candidatas_normas.csv`, contendo pelo menos: esfera, identificador, ano, título, tema detectado, URL, fonte, trecho/ementa e status de revisão. As normas candidatas devem passar por validação humana antes de entrar no catálogo curado, na matriz IAAN e no relatório final.

Para automatizar o processo, o projeto agora prevê o desenvolvimento e uso de uma **Skill de Monitoramento de Leis**. Esta habilidade (`.agents/skills/monitoramento-leis`) será encarregada de extrair ativamente dados do *Sistema Gestor de Compras da Paraíba* (e outros diários oficiais), compará-los com o `catalogo_curado_leis.csv` e sugerir a incorporação de novos decretos que afetem as dinâmicas de teoria dos leilões e custos de transação na plataforma.

Essa etapa é central para aumentar a qualidade do projeto, pois permite identificar atualizações recentes e normas relevantes não listadas inicialmente, sem comprometer a rastreabilidade e a consistência metodológica.

## Sugestões para implementação no projeto (Módulos Futuros)

A ideia do projeto é escalonar para os seguintes módulos:
- **Base Legal compras públicas** (ok)
- **Compras publicas da Paraíba** (ok)
- **Rais**: Vínculos formais, massa salarial, escolaridade e ocupação por estabelecimento por município da Paraíba;
- **Novo Caged**: Admissões e desligamentos formais por município da Paraíba;
- **PIB e contas regionais**: PIB e contas regionais dos municípios da Paraiba;
- **CEMPRE**: Empresas e unidades locais, pessoal ocupado por município da Paraíba;
- **Comex Stat (MDIC)**: Exportações e importações por produtos, por município da Paraíba.


## Dependências

Ambiente:

- O projeto é gerenciado pelo `uv`.
- As dependências e configurações estão no `pyproject.toml`.
- O ambiente virtual `.venv` é criado e mantido automaticamente pelo `uv`.
- Para adicionar novas dependências, utilize `uv add <pacote>`.
- Para executar scripts, utilize `uv run <script.py>` ou `uv run streamlit run <app.py>`.

Python:

- pandas
- matplotlib
- seaborn
- requests
- duckdb
- jupyter
- nbformat
- ipykernel
- pytest

Relatórios:

- Quarto
- ambiente LaTeX compatível para gerar PDF

## Cuidados ao Editar

- Preserve a rastreabilidade entre `scripts/coleta_leis.py`, `outputs/`, notebook e relatório.
- Se alterar cálculos, títulos, recorte temporal ou classificação de subsetores, atualize também `README.md` e este arquivo.
- Não edite manualmente gráficos ou tabelas gerados se a mudança puder ser feita no script.
- Mantenha textos do relatório objetivos e baseados nas análise comparativas.
- Preserve a distinção entre IAAN Paraíba x Governo Federal, matriz interestadual Paraíba x Sergipe e dimensão econômica qualitativa.
- Ao baixar normas, use `uv run scripts/coleta_leis.py --baixar`; sem `--baixar`, o script apenas gera tabelas, gráficos e cria diretórios.

## Histórico de Decisões Técnicas (Etapa 1)
- **Gerenciamento de Pacotes:** Optamos pelo uso de `uv` em vez de `conda` por ser mais rápido e eficiente, adotando o `pyproject.toml` como fonte da verdade.
- **Limpeza de Stack Visual:** Removidos pacotes `dash` legados, centralizando 100% o frontend em `Streamlit`.
- **API de Compras PB:** A URL base no swagger estava apontando para a raiz; mapeado com sucesso para o path `/api/v1/compras`. A paginação e formato das chaves `dados` e `anoInicioVigencia` foram embutidos no script `explora_api_compras_pb.py`.
- **Arquitetura de Dados (DuckDB):** Os scripts gravam CSVs que alimentam o banco analítico `data/compras_pb.duckdb` através da rotina `src/etl/build_db.py`. O portal Streamlit consumirá diretamente o banco local para alta performance.
- **CI/CD e Carga Incremental:** Desenvolvido um Workflow de GitHub Actions (`.github/workflows/atualiza_dados.yml`) que roda toda segunda-feira. A extração foi adaptada com a flag `--incremental` que reduz a consulta da API apenas ao ano atual e deduplica usando o Pandas (`drop_duplicates()`) antes de dar o push para a branch main.

## Histórico de Decisões Técnicas (Etapa 2)
- **Modelagem Socioeconômica e Risco:** Criado o script `src/etl/enriquecimento_socioeconomico.py` para traduzir o PDF analítico em tabelas no DuckDB. Foram criadas as dimensões `dim_matriz_teorica` (Scores de Keynes, Furtado e Schumpeter) e `dim_impacto_regional` (Contendo Mecanismos, Reflexos e Riscos Metodológicos).
- **Ponte Relacional:** Implementada a tabela `map_amparo_legal` e a view `vw_analise_socioeconomica` para limpar os amparos legais textuais sujos das APIs e vinculá-los às suas respectivas notas teóricas, permitindo calcular o valor adjudicado por impacto regional.
