<#
.SYNOPSIS
    Executa o pipeline de automação Apoia-se.

.DESCRIPTION
    Script de deployment local para o pipeline ETL de dados do Apoia-se.
    Este script instala todas as dependências automaticamente e executa
    a transformação dos dados de CSV para YAML/JSON.

    NÃO é necessário ser desenvolvedor para usar este script.

.NOTES
    - Requer Python 3.10+ instalado no sistema
    - Requer o arquivo CSV em data\base-apoiadores-mf.csv
    - Os artefatos serão gerados em artifacts\<data>\<serial>.yaml e .json
#>

# Parar execução em caso de erro
$ErrorActionPreference = "Stop"

# --- Cores para mensagens ---
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [ERRO] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Yellow
}

# --- Vai para a pasta do projeto ---
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir
Write-Info "Diretorio do projeto: $ProjectDir"

# ============================================
# PASSO 1: Verificar se Python está instalado
# ============================================
Write-Step "Passo 1/5 - Verificando se Python esta instalado..."

try {
    $pythonVersion = python --version 2>&1
    Write-Ok "Python encontrado: $pythonVersion"
}
catch {
    Write-Fail "Python NAO foi encontrado no seu sistema."
    Write-Host ""
    Write-Host "  Para instalar:" -ForegroundColor Yellow
    Write-Host "    1. Acesse https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "    2. Baixe o Python 3.10 ou superior" -ForegroundColor White
    Write-Host "    3. Na instalacao, marque 'Add Python to PATH'" -ForegroundColor White
    Write-Host "    4. Reinicie o PowerShell e execute este script novamente" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Verificar versão mínima
$versionMatch = [regex]::Match($pythonVersion, "(\d+)\.(\d+)")
if ($versionMatch.Success) {
    $major = [int]$versionMatch.Groups[1].Value
    $minor = [int]$versionMatch.Groups[2].Value
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Fail "Python 3.10 ou superior e necessario. Versao encontrada: $pythonVersion"
        exit 1
    }
}

# =================================================
# PASSO 2: Verificar se o arquivo CSV está presente
# =================================================
Write-Step "Passo 2/5 - Verificando se o arquivo CSV esta presente..."

$CsvPath = Join-Path $ProjectDir "data\base-apoiadores-mf.csv"
if (Test-Path $CsvPath) {
    $lineCount = (Get-Content $CsvPath | Measure-Object -Line).Lines
    Write-Ok "Arquivo CSV encontrado: $CsvPath ($lineCount linhas)"
}
else {
    Write-Fail "Arquivo CSV NAO encontrado!"
    Write-Host ""
    Write-Host "  O que fazer:" -ForegroundColor Yellow
    Write-Host "    1. Baixe a base de apoiadores do Apoia-se" -ForegroundColor White
    Write-Host "    2. Coloque o arquivo CSV na pasta:" -ForegroundColor White
    Write-Host "       $ProjectDir\data\base-apoiadores-mf.csv" -ForegroundColor White
    Write-Host ""
    exit 1
}

# ==============================================
# PASSO 3: Criar ambiente virtual (venv)
# ==============================================
Write-Step "Passo 3/5 - Preparando ambiente virtual Python..."

$VenvDir = Join-Path $ProjectDir ".venv"
if (Test-Path $VenvDir) {
    Write-Ok "Ambiente virtual ja existe."
}
else {
    Write-Info "Criando ambiente virtual... (pode demorar alguns segundos)"
    python -m venv $VenvDir
    Write-Ok "Ambiente virtual criado em: $VenvDir"
}

# ==============================================
# PASSO 4: Instalar dependências
# ==============================================
Write-Step "Passo 4/5 - Instalando dependencias..."

$PipPath = Join-Path $VenvDir "Scripts\pip.exe"
Write-Info "Instalando bibliotecas necessarias (polars, pyyaml)..."
& $PipPath install polars pyyaml --quiet 2>&1 | Out-Null
Write-Ok "Dependencias instaladas com sucesso."

# ==============================================
# PASSO 5: Executar o pipeline
# ==============================================
Write-Step "Passo 5/5 - Executando o pipeline de transformacao..."

$PythonPath = Join-Path $VenvDir "Scripts\python.exe"
Write-Info "Processando dados do CSV..."
Write-Info "Isso pode demorar alguns segundos para arquivos grandes."
Write-Host ""

& $PythonPath (Join-Path $ProjectDir "main.py")

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Step "Concluido com sucesso!"
    Write-Ok "Os artefatos foram gerados na pasta 'artifacts\'."
    Write-Info "Abra o arquivo .yaml para ver o resumo dos apoiadores."
    Write-Info "O arquivo .json contem os metadados para depuracao."
    Write-Host ""
}
else {
    Write-Host ""
    Write-Fail "Ocorreu um erro ao executar o pipeline."
    Write-Host "  Verifique se o arquivo CSV esta no formato correto." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
