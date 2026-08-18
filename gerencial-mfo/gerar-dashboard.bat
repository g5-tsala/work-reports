@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"
title Gerencial MFO - Gerador de Dashboard

echo.
echo ============================================================
echo    GERENCIAL MFO - Gerador de Dashboard
echo    G5 Partners - uso interno
echo ============================================================
echo.

rem ------------------------------------------------------------
rem  1. Localizar (ou instalar) o uv
rem     Instalacao via "pip install uv" - depende de um Python
rem     ja presente na maquina.
rem ------------------------------------------------------------
set "UV="
where uv >nul 2>nul
if not errorlevel 1 (
    set "UV=uv"
) else (
    set "PY="
    py -3 --version >nul 2>nul && set "PY=py -3"
    if not defined PY (
        python --version >nul 2>nul && set "PY=python"
    )
    if not defined PY goto :erro_python

    !PY! -m uv --version >nul 2>nul
    if errorlevel 1 (
        echo [setup] uv nao encontrado. Instalando via pip...
        !PY! -m pip install --upgrade --quiet uv
        if errorlevel 1 goto :erro_pip
        echo [setup] uv instalado.
        echo.
    )
    !PY! -m uv --version >nul 2>nul
    if errorlevel 1 goto :erro_pip
    set "UV=!PY! -m uv"
)

rem ------------------------------------------------------------
rem  2. Sincronizar ambiente e dependencias
rem ------------------------------------------------------------
echo [setup] Sincronizando ambiente virtual e dependencias...
!UV! sync --quiet
if errorlevel 1 goto :erro_sync
echo [setup] Ambiente pronto.
echo.

rem ------------------------------------------------------------
rem  3. Escolher o mes-base
rem ------------------------------------------------------------
if not exist "inputs\" goto :erro_inputs

set "ACHOU="
echo Meses disponiveis em inputs\:
for /d %%D in (inputs\20??-??) do (
    set "ACHOU=1"
    if exist "%%D\Gerencial MFO %%~nxD.xlsx" (
        echo    %%~nxD   [planilha OK]
    ) else (
        echo    %%~nxD   [SEM PLANILHA]
    )
)
if not defined ACHOU (
    echo    (nenhuma subpasta YYYY-MM encontrada em inputs\^)
)
echo.

set "MES="
set /p "MES=Informe o mes-base no formato YYYY-MM: "
if not defined MES goto :erro_mes_vazio

rem remove aspas eventuais
set "MES=!MES:"=!"

if not exist "inputs\!MES!\" goto :erro_pasta
if not exist "inputs\!MES!\Gerencial MFO !MES!.xlsx" goto :erro_planilha

rem ------------------------------------------------------------
rem  4. Rodar o build
rem ------------------------------------------------------------
echo.
echo ------------------------------------------------------------
echo  Processando !MES!...
echo ------------------------------------------------------------
echo.

!UV! run python build.py "!MES!"
if errorlevel 1 goto :erro_build

echo.
echo ------------------------------------------------------------
echo  CONCLUIDO
echo ------------------------------------------------------------
echo   Base:      %CD%\outputs\!MES!\data-!MES!.json
echo   Dashboard: %CD%\outputs\!MES!\dashboard-!MES!.html
echo.
echo   Abra o arquivo dashboard-!MES!.html no navegador para ver o resultado.
goto :fim

rem ------------------------------------------------------------
rem  Erros
rem ------------------------------------------------------------
:erro_python
echo.
echo [ERRO] Nenhuma instalacao de Python encontrada nesta maquina.
echo        O uv e instalado via "pip install uv" e precisa de um
echo        Python ja presente. Instale o Python 3.11 ou superior
echo        e execute este arquivo novamente.
goto :fim

:erro_pip
echo.
echo [ERRO] Falha ao instalar o uv via pip.
echo        Tente manualmente em um prompt de comando:
echo            python -m pip install --upgrade uv
echo        Se houver bloqueio de rede ou proxy, fale com a TI.
goto :fim

:erro_sync
echo.
echo [ERRO] Falha ao sincronizar as dependencias.
echo        Verifique a conexao de rede e o arquivo pyproject.toml.
goto :fim

:erro_mes_vazio
echo.
echo [ERRO] Nenhum mes informado.
goto :fim

:erro_inputs
echo.
echo [ERRO] A pasta "inputs" nao existe.
echo        Crie a pasta inputs\ e coloque dentro dela uma subpasta
echo        por mes, no formato YYYY-MM, com a planilha correspondente.
goto :fim

:erro_pasta
echo.
echo [ERRO] A subpasta "inputs\!MES!" nao existe.
echo        Use o formato YYYY-MM, por exemplo: 2026-07
goto :fim

:erro_planilha
echo.
echo [ERRO] Planilha nao encontrada em:
echo        inputs\!MES!\Gerencial MFO !MES!.xlsx
echo        O nome do arquivo precisa seguir exatamente esse padrao.
goto :fim

:erro_build
echo.
echo [ERRO] O processamento falhou. Veja as mensagens acima.
echo        Nenhum dashboard foi gerado para !MES!.
goto :fim

:fim
echo.
set "DUMMY="
set /p "DUMMY=Digite ENTER para finalizar..."
endlocal
