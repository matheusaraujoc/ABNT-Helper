# formula.py
from dataclasses import dataclass

@dataclass
class Formula:
    legenda: str = ""
    codigo_latex: str = r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}"
    # Caminho para o arquivo vetorial original (para preview)
    caminho_svg: str = ""
    # Caminho para a imagem rasterizada (para o DOCX)
    caminho_processado_png: str = ""
    numero: int = 0