import argparse
import pandas as pd
import requests
import hashlib
import os
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Coleta e baixa as leis a partir do catálogo curado.")
    parser.add_argument('--baixar', action='store_true', help="Se informado, realiza o download efetivo dos documentos.")
    return parser.parse_args()

def calculate_hash(content: bytes) -> str:
    """Calcula um hash SHA256 do conteúdo para versionamento/rastreabilidade."""
    return hashlib.sha256(content).hexdigest()

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_local_path(esfera, identificador, ano):
    base_dir = "data/leis"
    safe_ident = str(identificador).replace("/", "_").replace(".", "_").replace(" ", "_").lower()
    filename = f"{safe_ident}_{ano}.html"
    
    if esfera.lower() == "federal":
        return os.path.join(base_dir, "federais", filename)
    elif esfera.lower() == "pb":
        return os.path.join(base_dir, "estaduais", "pb", filename)
    elif esfera.lower() == "se":
        return os.path.join(base_dir, "estaduais", "se", filename)
    else:
        return os.path.join(base_dir, "outros", filename)

def main():
    args = parse_args()
    
    catalogo_path = "data/catalogo_curado_leis.csv"
    if not os.path.exists(catalogo_path):
        print(f"Erro: Catálogo não encontrado em {catalogo_path}")
        return

    df = pd.read_csv(catalogo_path)
    print(f"Carregadas {len(df)} normas do catálogo.")
    
    resultados = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for index, row in df.iterrows():
        url = str(row.get('url_oficial', 'nan'))
        esfera = str(row.get('esfera', ''))
        ident = str(row.get('identificador', ''))
        ano = str(row.get('ano', ''))
        
        status_download = "Nao Solicitado"
        local_path = get_local_path(esfera, ident, ano)
        doc_hash = row.get('hash_documento', None)

        if url.lower() != 'nan' and url.startswith('http'):
            if args.baixar:
                print(f"Baixando: {ident} - {url}")
                try:
                    time.sleep(1) # Delay para evitar bloqueio
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        content = response.content
                        doc_hash = calculate_hash(content)
                        
                        ensure_dir(local_path)
                        with open(local_path, 'wb') as f:
                            f.write(content)
                            
                        status_download = "Sucesso"
                    else:
                        status_download = f"Erro HTTP {response.status_code}"
                except Exception as e:
                    status_download = f"Erro: {str(e)}"
            else:
                status_download = "Pronto para download (use --baixar)"
        else:
            status_download = "URL Ausente/Invalida"
            local_path = None
            
        resultados.append({
            'esfera': esfera,
            'identificador': ident,
            'ano': ano,
            'url_oficial': url if url.lower() != 'nan' else '',
            'status_coleta': status_download,
            'local_path': local_path if status_download == "Sucesso" else '',
            'hash_documento': doc_hash if not pd.isna(doc_hash) else ''
        })

    df_status = pd.DataFrame(resultados)
    
    if args.baixar:
        df['hash_documento'] = df_status['hash_documento']
        df.to_csv(catalogo_path, index=False)
        print(f"Catálogo curado atualizado com os hashes em {catalogo_path}")

    ensure_dir("outputs/tables/status_coleta_leis.csv")
    df_status.to_csv("outputs/tables/status_coleta_leis.csv", index=False)
    
    print("\nResumo da Coleta:")
    print(df_status['status_coleta'].value_counts())
    print("\nDetalhes salvos em outputs/tables/status_coleta_leis.csv")

if __name__ == "__main__":
    main()
