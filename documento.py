# documento.py
# Descrição: Modelo de Dados atualizado para suportar uma estrutura de árvore.

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from referencia import Referencia

@dataclass
class Configuracoes:
    """Armazena as configurações globais do documento."""
    tipo_trabalho: str = "Trabalho de Conclusão de Curso (TCC)"
    instituicao: str = "Universidade Estadual do Piauí (UESPI)"
    curso: str = "Bacharelado em Ciência da Computação"
    cidade: str = "Araioses"
    estado: str = "MA"
    ano: int = datetime.now().year
    mes: str = datetime.now().strftime("%B").capitalize()

@dataclass
class Autor:
    """Representa um autor do trabalho."""
    nome_completo: str

@dataclass
class Capitulo:
    """Representa um nó na árvore de conteúdo (tópico ou subtópico)."""
    titulo: str
    conteudo: str = ""
    filhos: List['Capitulo'] = field(default_factory=list)
    pai: Optional['Capitulo'] = None

    def adicionar_filho(self, filho: 'Capitulo'):
        filho.pai = self
        self.filhos.append(filho)

class DocumentoABNT:
    """
    Classe principal que agrega todas as partes de um documento ABNT.
    """
    def __init__(self):
        self.configuracoes: Configuracoes = Configuracoes()
        self.titulo: str = ""
        self.autores: List[Autor] = []
        self.orientador: str = ""
        self.resumo: str = ""
        self.palavras_chave: str = ""
        
        # Este nó raiz não aparece no documento, ele apenas contém os capítulos principais.
        self.estrutura_textual = Capitulo(titulo="Raiz do Documento")
        
        # Adiciona capítulos iniciais por padrão
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="INTRODUÇÃO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="DESENVOLVIMENTO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="CONCLUSÃO"))
        
        self.referencias: List[Referencia] = []

    def ordenar_referencias(self):
        """Ordena a lista de referências em ordem alfabética."""
        self.referencias.sort(key=lambda ref: ref.get_chave_ordenacao())