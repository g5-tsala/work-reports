# work-reports

Scripts que geram relatórios HTML autocontidos.

## Relatórios

| Diretório | Descrição |
|---|---|
| [`claude-usage/`](claude-usage/) | Uso de Claude AI na G5 Partners — usuários ativos, conversas, atividade no Claude Code, funil de adoção |
| [`gerencial-mfo/`](gerencial-mfo/) | Dashboard gerencial mensal da área de MFO a partir da planilha Gerencial MFO |

## Uso

Cada relatório é autocontido. Entre no diretório e rode o script correspondente:

```bash
cd claude-usage
python3 report.py
# → reports/report-YYYY-MM-DD.html
```

Consulte o `AGENTS.md` do diretório para fontes de dados, referência de schema e armadilhas.
