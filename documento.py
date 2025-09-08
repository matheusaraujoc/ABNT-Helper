# documento.py
# Descrição: Modelo de Dados atualizado para incluir a estrutura de Figuras.

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from referencia import Referencia

@dataclass
class Tabela:
    # (sem alterações)
    titulo: str = ""; fonte: str = ""; dados: List[List[str]] = field(default_factory=list)
    estilo_borda: str = 'abnt'; numero: int = 0

# --- ## NOVO: Classe para armazenar os dados de uma Figura ## ---
@dataclass
class Figura:
    titulo: str = ""
    fonte: str = ""
    caminho_original: str = "" # Caminho do arquivo que o usuário selecionou
    caminho_processado: str = "" # Caminho do arquivo convertido/redimensionado
    largura_cm: float = 12.0 # Largura padrão em cm
    numero: int = 0

@dataclass
class Configuracoes:
    # (sem alterações)
    tipo_trabalho: str = "Trabalho de Conclusão de Curso (TCC)"
    instituicao: str = "Universidade Estadual do Piauí (UESPI)"; curso: str = "Ciência da Computação"
    modalidade_curso: str = "Bacharelado"; titulo_pretendido: str = "Bacharel"
    cidade: str = "Araioses"; estado: str = "MA"; ano: int = datetime.now().year
    mes: str = datetime.now().strftime("%B").capitalize()

@dataclass
class Autor:
    # (sem alterações)
    nome_completo: str

@dataclass
class Capitulo:
    # (sem alterações, apenas adiciona a lista de figuras)
    titulo: str
    conteudo: str = ""
    filhos: List['Capitulo'] = field(default_factory=list)
    pai: Optional['Capitulo'] = None
    tabelas: List[Tabela] = field(default_factory=list)
    # --- ## NOVO: Cada capítulo agora pode ter uma lista de figuras ## ---
    figuras: List[Figura] = field(default_factory=list)

    def adicionar_filho(self, filho: 'Capitulo'):
        filho.pai = self
        self.filhos.append(filho)

class DocumentoABNT:
    # (sem alterações)
    def __init__(self):
        self.configuracoes: Configuracoes = Configuracoes()
        self.titulo: str = ""; self.autores: List[Autor] = []; self.orientador: str = ""
        self.resumo: str = ""; self.palavras_chave: str = ""
        self.estrutura_textual = Capitulo(titulo="Raiz do Documento")
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="INTRODUÇÃO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="DESENVOLVIMENTO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="CONCLUSÃO"))
        self.referencias: List[Referencia] = []

    def ordenar_referencias(self):
        self.referencias.sort(key=lambda ref: ref.get_chave_ordenacao())