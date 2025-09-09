# formula.py (sem alterações, apenas para referência)
from dataclasses import dataclass

@dataclass
class Formula:
    legenda: str = ""
    codigo_latex: str = r"\frac{-b \pm \sqrt{b^2-4ac}}{2a}"
    caminho_imagem: str = ""  # ATENÇÃO: Este caminho agora será para um arquivo .svg
    numero: int = 0