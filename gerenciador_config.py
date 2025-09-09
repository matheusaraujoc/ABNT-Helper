# gerenciador_config.py
# Descrição: Lida com o salvamento e carregamento de configurações da aplicação,
# como a lista de projetos recentes.

import os
import json
from datetime import datetime

CONFIG_FILE = "abnf_helper_config.json"
MAX_RECENT_PROJECTS = 10

def carregar_config():
    """Carrega o arquivo de configuração JSON."""
    if not os.path.exists(CONFIG_FILE):
        return {"recent_projects": []}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Em caso de arquivo corrompido ou erro de leitura, retorna um padrão seguro.
        return {"recent_projects": []}

def salvar_config(data):
    """Salva os dados no arquivo de configuração JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Erro ao salvar configuração: {e}")

def get_projetos_recentes():
    """Retorna a lista de projetos recentes, ordenada pela data da última modificação."""
    config = carregar_config()
    projetos = config.get("recent_projects", [])
    # Ordena para que os mais recentes apareçam primeiro
    projetos.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    return projetos

def add_projeto_recente(caminho_arquivo):
    """Adiciona ou atualiza um projeto na lista de recentes."""
    if not caminho_arquivo:
        return
        
    config = carregar_config()
    projetos = config.get("recent_projects", [])
    
    caminho_abs = os.path.abspath(caminho_arquivo)
    
    # Remove qualquer entrada existente com o mesmo caminho para evitar duplicatas
    projetos = [p for p in projetos if p.get("path") != caminho_abs]

    # Adiciona a nova entrada no início da lista
    novo_projeto = {
        "path": caminho_abs,
        "name": os.path.basename(caminho_abs),
        "timestamp": datetime.now().timestamp()
    }
    projetos.insert(0, novo_projeto)

    # Limita o número de projetos recentes
    config["recent_projects"] = projetos[:MAX_RECENT_PROJECTS]
    salvar_config(config)

def remover_projeto_recente(caminho_arquivo):
    """Remove um projeto da lista de recentes (ex: se o arquivo foi deletado)."""
    config = carregar_config()
    projetos = config.get("recent_projects", [])
    caminho_abs = os.path.abspath(caminho_arquivo)
    
    projetos_atualizados = [p for p in projetos if p.get("path") != caminho_abs]
    
    if len(projetos_atualizados) < len(projetos):
        config["recent_projects"] = projetos_atualizados
        salvar_config(config)