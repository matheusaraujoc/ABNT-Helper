# gerenciador_projeto.py
# Descrição: Lida com a criação, salvamento e carregamento de projetos no formato .abnf,
# agora com suporte integrado para salvar e carregar as imagens SVG das fórmulas.

import os
import json
import zipfile
import tempfile
import shutil
import copy
from documento import DocumentoABNT, Capitulo, Figura, Formula, Configuracoes, Autor, Referencia, Livro, Artigo, Site
import gerenciador_config

class GerenciadorProjetos:
    def __init__(self):
        self.diretorio_temporario_atual = None

    def _limpar_diretorio_temporario(self):
        """Limpa o diretório temporário usado para carregar o projeto atual."""
        if self.diretorio_temporario_atual and os.path.exists(self.diretorio_temporario_atual):
            try:
                shutil.rmtree(self.diretorio_temporario_atual)
            except OSError as e:
                print(f"Erro ao limpar diretório temporário {self.diretorio_temporario_atual}: {e}")
        self.diretorio_temporario_atual = None

    def salvar_projeto(self, documento: DocumentoABNT, caminho_arquivo: str, add_to_recents: bool = True):
        """
        Salva o estado atual do documento, suas figuras (imagens) e fórmulas (svg)
        em um único arquivo .abnf (que é um zip).
        """
        with tempfile.TemporaryDirectory(prefix="abnf_save_") as temp_dir:
            # Cria subdiretórios dentro do zip para organização
            imagens_dir = os.path.join(temp_dir, 'imagens')
            os.makedirs(imagens_dir)
            
            # NOVO: Diretório para as fórmulas
            formulas_dir = os.path.join(temp_dir, 'formulas')
            os.makedirs(formulas_dir)

            # Faz uma cópia profunda para não modificar o documento em memória
            doc_para_salvar = copy.deepcopy(documento)

            # Processa as figuras
            for figura in doc_para_salvar.banco_figuras:
                if figura.caminho_processado and os.path.exists(figura.caminho_processado):
                    nome_arquivo = os.path.basename(figura.caminho_processado)
                    caminho_destino = os.path.join(imagens_dir, nome_arquivo)
                    shutil.copy2(figura.caminho_processado, caminho_destino)
                    # O caminho salvo no JSON é relativo à raiz do zip
                    figura.caminho_processado = os.path.join('imagens', nome_arquivo).replace('\\', '/')
            
            # NOVO: Processa as fórmulas
            for formula in doc_para_salvar.banco_formulas:
                if formula.caminho_imagem and os.path.exists(formula.caminho_imagem):
                    nome_arquivo = os.path.basename(formula.caminho_imagem)
                    caminho_destino = os.path.join(formulas_dir, nome_arquivo)
                    shutil.copy2(formula.caminho_imagem, caminho_destino)
                    # O caminho salvo no JSON também é relativo
                    formula.caminho_imagem = os.path.join('formulas', nome_arquivo).replace('\\', '/')
            
            # Serializa o objeto Documento para JSON
            dados_dict = doc_para_salvar.to_dict()
            caminho_json = os.path.join(temp_dir, 'documento.json')
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados_dict, f, ensure_ascii=False, indent=4)
            
            # Cria o arquivo .zip
            base_name = os.path.splitext(caminho_arquivo)[0]
            shutil.make_archive(base_name, 'zip', temp_dir)
            
            # Renomeia o .zip para .abnf, substituindo o antigo se existir
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
            os.rename(base_name + '.zip', caminho_arquivo)

        if add_to_recents:
            gerenciador_config.add_projeto_recente(caminho_arquivo)

    def carregar_projeto(self, caminho_arquivo: str) -> DocumentoABNT:
        """Carrega um projeto de um arquivo .abnf, extraindo seus conteúdos para um diretório temporário."""
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
                caminho_absoluto = os.path.join(self.diretorio_temporario_atual, figura.caminho_processado)
                figura.caminho_processado = caminho_absoluto

        # NOVO: Atualiza os caminhos das fórmulas para apontar para a pasta temporária
        for formula in documento_carregado.banco_formulas:
            if formula.caminho_imagem:
                caminho_absoluto = os.path.join(self.diretorio_temporario_atual, formula.caminho_imagem)
                formula.caminho_imagem = caminho_absoluto

        return documento_carregado

    def fechar_projeto(self):
        """Deve ser chamado ao fechar o programa ou um projeto para limpar os arquivos temporários."""
        self._limpar_diretorio_temporario()