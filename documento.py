# documento.py
# Descrição: Modelo de Dados completo do documento ABNT.

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from referencia import Referencia

@dataclass
class Tabela:
    titulo: str = ""
    fonte: str = ""
    dados: List[List[str]] = field(default_factory=list)
    estilo_borda: str = 'abnt' # Opções: 'abnt' ou 'grade'
    numero: int = 0

@dataclass
class Configuracoes:
    tipo_trabalho: str = "Trabalho de Conclusão de Curso (TCC)"
    instituicao: str = "Universidade Estadual do Piauí (UESPI)"
    curso: str = "Bacharelado em Ciência da Computação"
    cidade: str = "Araioses"
    estado: str = "MA"
    ano: int = datetime.now().year
    mes: str = datetime.now().strftime("%B").capitalize()

@dataclass
class Autor:
    nome_completo: str

@dataclass
class Capitulo:
    titulo: str
    conteudo: str = ""
    filhos: List['Capitulo'] = field(default_factory=list)
    pai: Optional['Capitulo'] = None
    tabelas: List[Tabela] = field(default_factory=list)

    def adicionar_filho(self, filho: 'Capitulo'):
        filho.pai = self
        self.filhos.append(filho)

class DocumentoABNT:
    def __init__(self):
        self.configuracoes: Configuracoes = Configuracoes()
        self.titulo: str = ""
        self.autores: List[Autor] = []
        self.orientador: str = ""
        self.resumo: str = ""
        self.palavras_chave: str = ""
        self.estrutura_textual = Capitulo(titulo="Raiz do Documento")
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="INTRODUÇÃO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="DESENVOLVIMENTO"))
        self.estrutura_textual.adicionar_filho(Capitulo(titulo="CONCLUSÃO"))
        self.referencias: List[Referencia] = []

    def ordenar_referencias(self):
        self.referencias.sort(key=lambda ref: ref.get_chave_ordenacao())