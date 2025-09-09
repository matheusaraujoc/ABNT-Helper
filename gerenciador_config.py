# gerenciador_config.py - COMPLETO E CORRIGIDO

import os
import json
from datetime import datetime

CONFIG_FILE = "abnf_helper_config.json"
MAX_RECENT_PROJECTS = 10

def get_default_config():
    """Retorna a estrutura de configuração padrão da aplicação."""
    return {
        "recent_projects": [],
        "recovery": {
            "autosave_enabled": True,
            #AQUI FICA O TIMER DEFINIDO EM MINUTOS DO SISTEMA DE RECUPERAÇÃO DE ARQUIVOS POR FALHAS ABRUPTAS DO SISTEMA
            # MUDANÇA: Agora é um intervalo periódico, não de inatividade. 10 minutos é um padrão seguro.
            "autosave_periodic_interval_min": 1
        },
        "backup": {
            "backup_on_save_enabled": True,
            "max_backups_per_project": 10
        }
    }

def carregar_config():
    """
    Carrega o arquivo de configuração JSON. Se o arquivo não existir ou estiver
    corrompido, retorna uma configuração padrão. Garante que configurações
    antigas sejam atualizadas com as novas chaves sem perder dados.
    """
    if not os.path.exists(CONFIG_FILE):
        return get_default_config()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        defaults = get_default_config()
        # Garante que a seção recovery exista
        config.setdefault('recovery', defaults['recovery'])
        # Atualiza para a nova chave se a antiga existir
        if 'autosave_interval_min' in config['recovery']:
            del config['recovery']['autosave_interval_min']
        config['recovery'].setdefault('autosave_periodic_interval_min', defaults['recovery']['autosave_periodic_interval_min'])
        
        config.setdefault('backup', defaults['backup'])
        
        return config
    except (json.JSONDecodeError, IOError):
        return get_default_config()

# O restante do arquivo (salvar_config, get_projetos_recentes, etc.) permanece o mesmo...
# ... (cole o resto das suas funções aqui)
def salvar_config(data):
    """Salva os dados no arquivo de configuração JSON."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar configuração: {e}")

def get_projetos_recentes():
    """Retorna a lista de projetos recentes, ordenada pela data da última modificação."""
    config = carregar_config()
    projetos = config.get("recent_projects", [])
    projetos.sort(key=lambda p: p.get("timestamp", 0), reverse=True)
    return projetos

def add_projeto_recente(caminho_arquivo):
    """Adiciona ou atualiza um projeto na lista de recentes."""
    if not caminho_arquivo:
        return
    config = carregar_config()
    projetos = config.get("recent_projects", [])
    caminho_abs = os.path.abspath(caminho_arquivo)
    projetos = [p for p in projetos if p.get("path") != caminho_abs]
    novo_projeto = {
        "path": caminho_abs,
        "name": os.path.basename(caminho_abs),
        "timestamp": datetime.now().timestamp()
    }
    projetos.insert(0, novo_projeto)
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