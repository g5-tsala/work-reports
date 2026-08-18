"""Registro de paginas.

Cada aba do dashboard e um modulo em `paginas/` que se registra com o decorador
`@pagina(...)`. Nada mais precisa saber que ela existe: o menu, a ordem e o
roteamento saem daqui. Para acrescentar uma aba, crie o modulo, decore a funcao
e importe-o em `paginas/__init__.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

#: Grupos do menu lateral, na ordem em que aparecem (`docs/dashboard.md` §1).
GRUPOS = (
    "Visão Executiva",
    "Performance",
    "Carteira",
    "Captação",
    "Estrutura",
    "Outros",
)


@dataclass(frozen=True)
class Pagina:
    identificador: str
    titulo: str
    grupo: str
    ordem: int
    subtitulo: str
    render: Callable[..., str]

    @property
    def ancora(self) -> str:
        return f"pagina-{self.identificador}"


_REGISTRO: list[Pagina] = []


def pagina(*, identificador: str, titulo: str, grupo: str, ordem: int, subtitulo: str = ""):
    """Registra a funcao de render de uma aba."""
    if grupo not in GRUPOS:
        raise ValueError(f"grupo '{grupo}' nao existe; use um de {GRUPOS}")

    def decorador(funcao: Callable[..., str]) -> Callable[..., str]:
        _REGISTRO.append(
            Pagina(
                identificador=identificador,
                titulo=titulo,
                grupo=grupo,
                ordem=ordem,
                subtitulo=subtitulo,
                render=funcao,
            )
        )
        return funcao

    return decorador


def registradas() -> list[Pagina]:
    """Paginas na ordem do menu: por grupo e, dentro dele, por `ordem`."""
    return sorted(_REGISTRO, key=lambda p: (GRUPOS.index(p.grupo), p.ordem))


def por_grupo() -> list[tuple[str, list[Pagina]]]:
    agrupadas: dict[str, list[Pagina]] = {}
    for item in registradas():
        agrupadas.setdefault(item.grupo, []).append(item)
    return [(grupo, agrupadas[grupo]) for grupo in GRUPOS if grupo in agrupadas]
