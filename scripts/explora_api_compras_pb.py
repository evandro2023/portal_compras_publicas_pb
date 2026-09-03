import requests
import pandas as pd
import time
import os
import argparse

# Configurações globais
BASE_URL = "https://api.dados.pb.gov.br/api/v1/compras"
ANOS_ALVO = [2024, 2025, 2026]
ENDPOINTS = [
    "/contratacoes",
    "/contratos",
    "/itens_contratacoes",
    "/plano_anual_contratacao"
]

def parse_args():
    parser = argparse.ArgumentParser(description="Explora as APIs de compras públicas do estado da PB.")
    parser.add_argument('--limite-paginas', type=int, default=2, help="Limite de páginas por ano/endpoint para evitar cargas massivas na fase exploratória. Use 0 para sem limite.")
    parser.add_argument('--incremental', action='store_true', help="Habilita carga incremental: busca apenas dados do ano corrente e deduplica a base CSV.")
    return parser.parse_args()

def fetch_data_from_endpoint(endpoint: str, ano: int, limite_paginas: int) -> list:
    print(f"\n--- Iniciando coleta para o endpoint {endpoint} (Ano: {ano}) ---")
    
    url = f"{BASE_URL}{endpoint}"
    resultados_acumulados = []
    pagina_atual = 1
    
    headers = {
        'Accept': 'application/json'
    }

    while True:
        # Se limite foi definido (maior que 0) e chegamos nele, parar
        if limite_paginas > 0 and pagina_atual > limite_paginas:
            print(f"Limte de {limite_paginas} páginas atingido. Parando.")
            break
            
        print(f"Buscando página {pagina_atual}...")
        
        # Para contratos o ano pode se chamar anoInicioVigencia
        if endpoint == '/contratos':
            params = {
                'anoInicioVigencia': ano,
                'page': pagina_atual
            }
        else:
            params = {
                'ano': ano,
                'page': pagina_atual
            }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                # Se for uma lista direta
                if isinstance(data, list):
                    items = data
                # Se os dados vierem aninhados (ex: data['resultado'] ou data['data'])
                elif isinstance(data, dict):
                    # Tenta adivinhar chaves comuns
                    if 'dados' in data:
                        items = data['dados']
                    elif 'data' in data:
                        items = data['data']
                    elif 'resultados' in data:
                        items = data['resultados']
                    elif 'items' in data:
                        items = data['items']
                    else:
                        print(f"JSON retornado é um dict, mas a chave de dados é desconhecida: {data.keys()}")
                        break
                else:
                    print("Formato de retorno desconhecido.")
                    break
                    
                if not items:
                    print("Nenhum dado retornado nesta página. Concluído.")
                    break
                    
                # Injeta a coluna do ano de referência para diferenciar os dados agregados
                for item in items:
                    item['ano_referencia'] = ano
                    
                resultados_acumulados.extend(items)
                print(f"Página {pagina_atual}: {len(items)} registros encontrados. Total: {len(resultados_acumulados)}")
                
                pagina_atual += 1
                time.sleep(1) # Delay de respeito
                
            else:
                print(f"Erro HTTP {response.status_code}: {response.text}")
                break
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            break

    return resultados_acumulados

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def main():
    args = parse_args()
    
    # Se incremental estiver ativo, substituímos a lista de anos alvo pelo ano corrente.
    from datetime import datetime
    anos_a_processar = [datetime.now().year] if args.incremental else ANOS_ALVO
    
    output_base_dir = "data/raw/compras_pb"
    ensure_dir(f"{output_base_dir}/.keep")
    
    for endpoint in ENDPOINTS:
        # Pega o nome do arquivo a partir do endpoint (ex: /contratacoes -> contratacoes.csv)
        nome_arquivo = f"{endpoint.strip('/')}.csv"
        caminho_arquivo = os.path.join(output_base_dir, nome_arquivo)
        
        dados_endpoint = []
        
        for ano in anos_a_processar:
            dados = fetch_data_from_endpoint(endpoint, ano, args.limite_paginas)
            if dados:
                dados_endpoint.extend(dados)
                
        if dados_endpoint:
            df_novos = pd.DataFrame(dados_endpoint)
            
            # Lógica de Deduplicação e Incremental
            if args.incremental and os.path.exists(caminho_arquivo):
                df_antigo = pd.read_csv(caminho_arquivo, low_memory=False)
                df = pd.concat([df_antigo, df_novos], ignore_index=True)
                
                # Como não temos uma chave primária fixa conhecida para todas as tabelas,
                # e os dados retornados podem vir aninhados como strings na conversão (ex: participantes),
                # faremos o drop_duplicates() com base em colunas primitivas para garantir a deduplicação.
                # Primeiro, converte todas as colunas para string no drop_duplicates para evitar problemas de tipos in-hashables
                df_str = df.astype(str)
                df = df.loc[~df_str.duplicated(keep='last')].reset_index(drop=True)
                print(f"Incremental concluído. Removidas as duplicatas. Novo total de registros: {len(df)}")
            else:
                df = df_novos
            
            # Salva o dataset final
            df.to_csv(caminho_arquivo, index=False)
            print(f"Salvo {len(df)} registros totais em {caminho_arquivo}")
        else:
            print(f"Nenhum dado novo coletado para {endpoint}")

if __name__ == "__main__":
    main()
