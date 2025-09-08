# documento.py
# Descrição: Define o Modelo de Dados para o documento ABNT.

from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from referencia import Referencia  # Importa a classe base de referência

@dataclass
class Configuracoes:
    """Armazena as configurações globais do documento."""
    tipo_trabalho: str = "Trabalho de Conclusão de Curso (TCC)"
    instituicao: str = "Universidade Estadual do Piauí (UESPI)"
    curso: str = "Bacharelado em Ciência da Computação"
    cidade: str = "Parnaíba"
    estado: str = "PI"
    ano: int = datetime.now().year
    mes: str = datetime.now().strftime("%B").capitalize()

@dataclass
class Autor:
    """Representa um autor do trabalho."""
    nome_completo: str

@dataclass
class Capitulo:
    """Representa uma seção/capítulo do conteúdo textual."""
    titulo: str
    conteudo: str = ""

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
        
        self.capitulos: List[Capitulo] = [
            Capitulo(titulo="INTRODUÇÃO"),
            Capitulo(titulo="DESENVOLVIMENTO"),
            Capitulo(titulo="CONCLUSÃO")
        ]
        
        self.referencias: List[Referencia] = []

    def ordenar_referencias(self):
        """Ordena a lista de referências em ordem alfabética."""
        self.referencias.sort(key=lambda ref: ref.get_chave_ordenacao())