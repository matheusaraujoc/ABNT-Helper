# gerenciador_projeto.py
# Descrição: Lida com a criação, salvamento e carregamento de projetos no formato .abnf.

import os
import json
import zipfile
import tempfile
import shutil
import copy
from documento import DocumentoABNT, Capitulo, Figura, Configuracoes, Autor, Referencia, Livro, Artigo, Site
import gerenciador_config

class GerenciadorProjetos:
    def __init__(self):
        self.diretorio_temporario_atual = None

    def _limpar_diretorio_temporario(self):
        if self.diretorio_temporario_atual and os.path.exists(self.diretorio_temporario_atual):
            try:
                shutil.rmtree(self.diretorio_temporario_atual)
            except OSError as e:
                print(f"Erro ao limpar diretório temporário {self.diretorio_temporario_atual}: {e}")
        self.diretorio_temporario_atual = None

    def salvar_projeto(self, documento: DocumentoABNT, caminho_arquivo: str, add_to_recents: bool = True):
        """
        Salva o estado atual do documento e suas imagens em um arquivo .abnf.
        O parâmetro 'add_to_recents' controla se o arquivo deve ser adicionado
        à lista de projetos recentes, evitando que arquivos de recuperação apareçam lá.
        """
        with tempfile.TemporaryDirectory(prefix="abnf_save_") as temp_dir:
            imagens_dir = os.path.join(temp_dir, 'imagens')
            os.makedirs(imagens_dir)

            doc_para_salvar = copy.deepcopy(documento)

            for figura in doc_para_salvar.banco_figuras:
                if figura.caminho_processado and os.path.exists(figura.caminho_processado):
                    nome_arquivo = os.path.basename(figura.caminho_processado)
                    caminho_destino = os.path.join(imagens_dir, nome_arquivo)
                    shutil.copy2(figura.caminho_processado, caminho_destino)
                    # O caminho salvo no JSON é relativo à raiz do zip
                    figura.caminho_processado = os.path.join('imagens', nome_arquivo).replace('\\', '/')
            
            dados_dict = doc_para_salvar.to_dict()
            caminho_json = os.path.join(temp_dir, 'documento.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados_dict, f, ensure_ascii=False, indent=4)
            
            base_name = os.path.splitext(caminho_arquivo)[0]
            shutil.make_archive(base_name, 'zip', temp_dir)
            
            # Remove o arquivo .abnf antigo antes de renomear o novo .zip para .abnf
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
            os.rename(base_name + '.zip', caminho_arquivo)

        # A adição à lista de recentes agora é condicional
        if add_to_recents:
            gerenciador_config.add_projeto_recente(caminho_arquivo)

    def carregar_projeto(self, caminho_arquivo: str) -> DocumentoABNT:
        """Carrega um projeto de um arquivo .abnf, extraindo seus conteúdos."""
        self._limpar_diretorio_temporario()
        self.diretorio_temporario_atual = tempfile.mkdtemp(prefix="abnf_load_")

        with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
            zip_ref.extractall(self.diretorio_temporario_atual)
        
        caminho_json = os.path.join(self.diretorio_temporario_atual, 'documento.json')
        if not os.path.exists(caminho_json):
            raise FileNotFoundError("Arquivo 'documento.json' não encontrado no projeto.")
            
        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados_dict = json.load(f)
            
        documento_carregado = DocumentoABNT.from_dict(dados_dict)

        # Atualiza os caminhos das figuras para apontar para a pasta temporária
        for figura in documento_carregado.banco_figuras:
            if figura.caminho_processado:
                # O caminho no JSON é relativo (ex: "imagens/foto.png")
                # Nós o transformamos em um caminho absoluto para a pasta temporária
                caminho_absoluto = os.path.join(self.diretorio_temporario_atual, figura.caminho_processado)
                figura.caminho_processado = caminho_absoluto

        return documento_carregado

    def fechar_projeto(self):
        """Deve ser chamado ao fechar o programa para limpar os arquivos temporários."""
        self._limpar_diretorio_temporario()