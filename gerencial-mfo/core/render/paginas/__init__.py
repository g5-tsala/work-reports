"""As abas do dashboard.

Uma aba = um módulo. Para mudar o que aparece numa aba, abra o arquivo dela e
mais nada. Para criar uma aba nova: escreva o módulo, decore a função com
`@pagina(...)` e acrescente o import aqui — a ordem do menu vem do grupo e do
campo `ordem` do decorador, não da ordem destes imports.

`comum.py` guarda o que abas irmãs (onshore/offshore) usam do mesmo jeito; não
é uma aba e não se registra.
"""

from . import (  # noqa: F401
    administradores_offshore,
    administradores_onshore,
    captacao_executado,
    captacao_grupos,
    captacao_net,
    captacao_portfolios,
    g5jus,
    grupos,
    historico,
    officers,
    portfolios_offshore,
    portfolios_onshore,
    regioes,
    resumo,
    roa_historico,
    visao_geral,
)
