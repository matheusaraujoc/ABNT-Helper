# documento.py
# Descrição: Modelo de Dados atualizado com flag para diferenciar capítulos de template.

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from referencia import Referencia, Livro, Artigo, Site

@dataclass
class Tabela:
    titulo: str = ""
    fonte: str = ""
    dados: List[List[str]] = field(default_factory=list)
    estilo_borda: str = 'abnt'
    numero: int = 0

@dataclass
class Figura:
    titulo: str = ""
    fonte: str = ""
    caminho_original: str = ""
    caminho_processado: str = ""
    largura_cm: float = 12.0
    numero: int = 0

@dataclass
class Configuracoes:
    tipo_trabalho: str = "Trabalho de Conclusão de Curso (TCC)"
    instituicao: str = "Universidade Estadual do Piauí (UESPI)"
    curso: str = "Ciência da Computação"
    modalidade_curso: str = "Bacharelado"
    titulo_pretendido: str = "Bacharel"
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
    is_template_item: bool = False  # <-- A LINHA QUE FALTAVA NO SEU ARQUIVO
    filhos: List['Capitulo'] = field(default_factory=list)
    pai: Optional['Capitulo'] = field(default=None, repr=False)
    tabelas: List[Tabela] = field(default_factory=list)
    figuras: List[Figura] = field(default_factory=list)

    def adicionar_filho(self, filho: 'Capitulo'):
        filho.pai = self
        self.filhos.append(filho)
    
    def to_dict(self):
        return {
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "is_template_item": self.is_template_item,
            "tabelas": [t.__dict__ for t in self.tabelas],
            "figuras": [f.__dict__ for f in self.figuras],
            "filhos": [filho.to_dict() for filho in self.filhos],
        }

    @classmethod
    def from_dict(cls, data):
        capitulo = cls(
            titulo=data['titulo'],
            conteudo=data.get('conteudo', ''),
            is_template_item=data.get('is_template_item', False),
            tabelas=[Tabela(**t) for t in data.get('tabelas', [])],
            figuras=[Figura(**f) for f in data.get('figuras', [])]
        )
        for filho_data in data.get('filhos', []):
            filho = Capitulo.from_dict(filho_data)
            capitulo.adicionar_filho(filho)
        return capitulo

class DocumentoABNT:
    def __init__(self):
        self.configuracoes: Configuracoes = Configuracoes()
        self.titulo: str = ""
        self.autores: List[Autor] = []
        self.orientador: str = ""
        self.resumo: str = ""
        self.palavras_chave: str = ""
        self.estrutura_textual = Capitulo(titulo="Raiz do Documento")
        self.referencias: List[Referencia] = []

    def ordenar_referencias(self):
        self.referencias.sort(key=lambda ref: ref.get_chave_ordenacao())
        
    def to_dict(self):
        refs_serializadas = []
        for ref in self.referencias:
            ref_dict = ref.__dict__
            ref_dict['tipo_ref'] = ref.tipo
            refs_serializadas.append(ref_dict)

        return {
            "configuracoes": self.configuracoes.__dict__,
            "titulo": self.titulo,
            "autores": [a.__dict__ for a in self.autores],
            "orientador": self.orientador,
            "resumo": self.resumo,
            "palavras_chave": self.palavras_chave,
            "estrutura_textual": self.estrutura_textual.to_dict(),
            "referencias": refs_serializadas
        }

    @classmethod
    def from_dict(cls, data):
        doc = cls()
        doc.configuracoes = Configuracoes(**data.get('configuracoes', {}))
        doc.titulo = data.get('titulo', '')
        doc.autores = [Autor(**a) for a in data.get('autores', [])]
        doc.orientador = data.get('orientador', '')
        doc.resumo = data.get('resumo', '')
        doc.palavras_chave = data.get('palavras_chave', '')
        doc.estrutura_textual = Capitulo.from_dict(data.get('estrutura_textual', {"titulo": "Raiz"}))
        
        for ref_data in data.get('referencias', []):
            tipo = ref_data.pop('tipo_ref', None)
            if tipo == 'Livro':
                doc.referencias.append(Livro(**ref_data))
            elif tipo == 'Artigo':
                doc.referencias.append(Artigo(**ref_data))
            elif tipo == 'Site':
                doc.referencias.append(Site(**ref_data))
        return doc