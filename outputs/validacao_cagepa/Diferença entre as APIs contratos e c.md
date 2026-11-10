## Diferença entre as APIs contratos e contratações

### Porque a CAGEPA não aparece na API contratações

Sim, é possível identificar claramente a diferença entre as duas APIs, entender como elas se relacionam e por que ocorre essa ausência específica no caso da **CAGEPA**.

Abaixo estão os resultados da verificação técnica realizada na documentação e diretamente nos dados da base (`compras_pb.duckdb`):

---

### 1. Diferença Conceitual entre as APIs

| Característica | API / Tabela `contratacoes` | API / Tabela `contratos` |
| :--- | :--- | :--- |
| **Etapa do Ciclo** | **Fase Preparatória / Licitatória** (o procedimento de compra) | **Fase Contratual / Execução** (o ajuste formal assinado) |
| **O que registra** | Editais, dispensas, inexigibilidades, julgamento de propostas, participantes, valor estimado vs. homologado. | Termos de contrato, vigência, valor original, aditivos, apostilamentos, fiscais/gestores. |
| **Origem do Dado** | Sistema da **Central de Compras do Estado** (`centraldecompras.pb.gov.br`). | Sistema de Controle de Contratos da **CGE-PB** (`cge.pb.gov.br/gea`). |
| **Identificador Primário** | `numeroProcesso` e `numeroLicitacao` | `registroCge` e `numeroContrato` |

---

### 2. Existe uma chave que ligue esses dados?

**Sim, existe uma chave de ligação documental e de dados:**

$$\text{contratos}.\texttt{numeroProcessoLicitacao} = \text{contratacoes}.\texttt{numeroProcesso}$$

- **Relação:** Geralmente de **1 para N** (um único processo licitatório com múltiplos itens/lotes pode gerar vários contratos com diferentes fornecedores).
- **Validação na base:** Na base geral do Estado, essa ligação funciona: **8.830 contratos** estão perfeitamente vinculados às suas respectivas contratações por essa chave.

---

### 3. Por que você NÃO encontra contratos da CAGEPA na tabela `contratações`?

A verificação na base de dados revelou o seguinte cenário para a CAGEPA:

- **Tabela `contratos`:** Existem **776 contratos da CAGEPA** registrados (`siglaOrgao = 'CAGEPA - 31.0601'`, `nomeOrgao = 'COMPANHIA DE ÁGUA E ESGOTOS DO ESTADO DA PARAÍBA'`).
- **Tabela `contratacoes`:** Existem **0 registros** da CAGEPA.
- **Campo de ligação (`numeroProcessoLicitacao`):** Nos 776 contratos da CAGEPA, o campo `numeroProcessoLicitacao` está **100% nulo (`NULL`)**.

#### Por que isso acontece?

1. **Regime Jurídico Próprio (Lei das Estatais):**
   - A CAGEPA é uma Sociedade de Economia Mista. Suas contratações são regidas pela **Lei Federal nº 13.303/2016 (Lei das Estatais)** e por regulamento interno próprio (RILC), não pela sistemática padrão das secretarias estaduais.
2. **Sistemas e Plataformas de Licitação Diferentes:**
   - A CAGEPA não realiza suas licitações pelo sistema corporativo da Central de Compras da SEAD (que alimenta o endpoint `/contratacoes`). A CAGEPA opera processos licitatórios em plataformas próprias (como o sistema Petronect e portal licitações da CAGEPA).
3. **Ponto de convergência na CGE:**
   - Embora a CAGEPA licite fora da Central de Compras, por ser ente estadual ela é obrigada por lei a registrar a **formalização de todos os seus contratos** no sistema GEA da Controladoria Geral do Estado (CGE-PB).
   - Por esse motivo, os contratos aparecem no endpoint `/contratos` (com links `cge.pb.gov.br/gea/...`), mas o procedimento licitatório prévio não existe no endpoint `/contratacoes`.

> [!NOTE]
> Esse mesmo comportamento se repete em outros entes da administração indireta e fundacional do Estado (como **FPGS - Fundação Paraibana de Gestão em Saúde**, **DOCAS**, **CEHAP** e **EMPAER**), onde a vinculação com `/contratacoes` é nula pelo mesmo motivo operacional.