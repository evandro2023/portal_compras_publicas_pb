"""Catálogo e funções de mapeamento para CNAE, Setores Econômicos, Intensidade Tecnológica e Localização Geográfica.
"""

from __future__ import annotations
import re

# Estados da Região Nordeste
UFS_NORDESTE = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}


def categorizar_localizacao(uf: str | None, municipio: str | None) -> str:
    """Classifica a localização do fornecedor contratado em 4 categorias:

    - Capital (PB)
    - Interior (PB)
    - Nordeste (Demais UFs)
    - Fora do Nordeste
    """
    if not uf or str(uf).strip() == "" or str(uf).upper() == "NONE":
        return "Não Identificado"

    uf_clean = str(uf).strip().upper()
    mun_clean = str(municipio).strip().upper() if municipio else ""

    # Normalização de acentos em João Pessoa
    mun_norm = re.sub(r"[ÁÀÂÃ]", "A", mun_clean)

    if uf_clean == "PB":
        if "JOAO PESSOA" in mun_norm:
            return "Capital (PB)"
        return "Interior (PB)"
    elif uf_clean in UFS_NORDESTE:
        return "Nordeste (Demais UFs)"
    else:
        return "Fora do Nordeste"


def categorizar_setor_cnae(cnae_code: str | int | None) -> str:
    """Mapeia o código CNAE (ou suas divisões de 2 dígitos) para os 7 Setores Econômicos principais:

    1. Agricultura e Pecuária (Seção A: Divisões 01-03)
    2. Indústria Extrativa (Seção B: Divisões 05-09)
    3. Indústria de Transformação (Seção C: Divisões 10-33)
    4. Serviços Industriais de Utilidade Pública - SIUP (Seções D/E: Divisões 35-39)
    5. Construção Civil (Seção F: Divisões 41-43)
    6. Comércio (Seção G: Divisões 45-47)
    7. Serviços (Seções H a S: Divisões 49-96)
    """
    if not cnae_code:
        return "Não Classificado"

    cnae_str = re.sub(r"\D", "", str(cnae_code))
    if len(cnae_str) < 2:
        return "Não Classificado"

    try:
        divisao = int(cnae_str[:2])
    except ValueError:
        return "Não Classificado"

    if 1 <= divisao <= 3:
        return "Agricultura e Pecuária"
    elif 5 <= divisao <= 9:
        return "Indústria Extrativa"
    elif 10 <= divisao <= 33:
        return "Indústria de Transformação"
    elif 35 <= divisao <= 39:
        return "Serviços Industriais de Utilidade Pública (SIUP)"
    elif 41 <= divisao <= 43:
        return "Construção Civil"
    elif 45 <= divisao <= 47:
        return "Comércio"
    elif 49 <= divisao <= 96:
        return "Serviços"
    else:
        return "Outros / Não Classificado"


def categorizar_intensidade_tecnologica(cnae_code: str | int | None) -> str:
    """Mapeia a intensidade tecnológica de acordo com a taxonomia OCDE/IBGE.

    Foco na Indústria de Transformação (divisões 10 a 33) e Serviços baseados em conhecimento (KIS - TI/Telecom/P&D):
    - Alta Intensidade Tecnológica
    - Média-Alta Intensidade Tecnológica
    - Média-Baixa Intensidade Tecnológica
    - Baixa Intensidade Tecnológica
    - Serviços e Outros Setores (Não-Manufatura)
    """
    if not cnae_code:
        return "Não Classificado"

    cnae_str = re.sub(r"\D", "", str(cnae_code))
    if len(cnae_str) < 2:
        return "Não Classificado"

    try:
        divisao = int(cnae_str[:2])
    except ValueError:
        return "Não Classificado"

    # Alta Intensidade (Transformação + KIS TI/P&D)
    if divisao in {21, 26, 72} or cnae_str.startswith(("303", "304")):
        return "Alta Intensidade Tecnológica"

    # Média-Alta Intensidade
    if divisao in {20, 27, 28, 29, 30} or cnae_str.startswith("325"):
        return "Média-Alta Intensidade Tecnológica"

    # Média-Baixa Intensidade
    if divisao in {19, 22, 23, 24, 25, 33} or cnae_str.startswith("301"):
        return "Média-Baixa Intensidade Tecnológica"

    # Baixa Intensidade
    if divisao in {10, 11, 12, 13, 14, 15, 16, 17, 18, 31, 32}:
        return "Baixa Intensidade Tecnológica"

    # Serviços Intensive Technology / KIS (TI e Telecom)
    if divisao in {61, 62, 63}:
        return "Alta Intensidade Tecnológica (Serviços KIS)"

    return "Serviços e Outros (Não-Industrial)"


def categorizar_grande_setor(cnae_code: str | int | None) -> str:
    """Classifica o código CNAE nas Grandes Categorias Econômicas do IBGE (CGCE / PIM-PF)
    e nos demais macrosetores econômicos da cadeia de compras públicas:

    Grandes Categorias de Bens (IBGE):
    - Bens de Capital
    - Bens Intermediários
    - Bens de Consumo Duráveis
    - Bens de Consumo Semiduráveis e Não Duráveis

    Demais Macrosetores:
    - Construção Civil
    - Serviços Industriais de Utilidade Pública (SIUP)
    - Serviços Gerais
    - Agropecuária
    - Outros / Não Classificado
    """
    if not cnae_code:
        return "Não Classificado"

    cnae_str = re.sub(r"\D", "", str(cnae_code))
    if len(cnae_str) < 2:
        return "Não Classificado"

    try:
        cnae_int = int(cnae_str)
        divisao = int(cnae_str[:2])
        grupo = int(cnae_str[:3]) if len(cnae_str) >= 3 else 0
        subclasse_5 = int(cnae_str[:5]) if len(cnae_str) >= 5 else 0
    except ValueError:
        return "Não Classificado"

    # Bens de Capital (Máquinas, equipamentos, informática, veículos pesados de carga/transporte)
    if (
        divisao == 28
        or (divisao == 26 and grupo in (261, 262, 265))
        or (divisao == 27 and grupo in (271, 273, 279))
        or (divisao == 29 and grupo in (292, 293))
        or (divisao == 30 and grupo in (301, 303, 304, 305))
        or (divisao == 32 and subclasse_5 == 32501)
        or divisao == 33
        or grupo in (466, 465)
        or subclasse_5 == 47512
        or cnae_int in (4511102, 4511104, 4511106)
    ):
        return "Bens de Capital"

    # Bens Intermediários (Insumos industriais, plásticos, produtos químicos básicos, materiais)
    if (
        5 <= divisao <= 9
        or divisao in (16, 17, 22, 23, 24, 25)
        or (divisao == 20 and grupo not in (206, 207))
        or (divisao == 29 and grupo == 294)
        or (divisao == 13 and grupo in (131, 132, 133))
        or grupo in (453, 467, 468)
        or grupo == 474
    ):
        return "Bens Intermediários"

    # Bens de Consumo Duráveis (Mobiliário, eletrodomésticos, automóveis de passeio, eletrônicos de consumo)
    if (
        (divisao == 26 and grupo in (263, 264))
        or (divisao == 27 and grupo == 275)
        or (divisao == 29 and grupo == 291)
        or (divisao == 30 and grupo == 309)
        or divisao == 31
        or (divisao == 32 and grupo in (321, 322, 323, 324))
        or grupo == 454
        or subclasse_5 in (47539, 47547, 46494)
        or cnae_int in (4511101, 4511103, 4511105)
    ):
        return "Bens de Consumo Duráveis"

    # Bens de Consumo Semiduráveis e Não Duráveis (Alimentos, medicamentos, vestuário, combustíveis)
    if (
        divisao in (10, 11, 12, 14, 15, 18, 21)
        or (divisao == 13 and grupo in (134, 135))
        or (divisao == 20 and grupo in (206, 207))
        or (divisao == 32 and grupo == 329)
        or grupo in (462, 463, 464, 471, 472, 473, 476, 477, 478)
    ):
        return "Bens de Consumo Semiduráveis e Não Duráveis"

    # Demais Macrosetores
    if 41 <= divisao <= 43:
        return "Construção Civil"
    elif 35 <= divisao <= 39:
        return "Serviços Industriais de Utilidade Pública (SIUP)"
    elif 49 <= divisao <= 96:
        return "Serviços Gerais"
    elif 1 <= divisao <= 3:
        return "Agropecuária"
    else:
        return "Outros / Não Classificado"
