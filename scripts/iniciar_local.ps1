param(
    [switch]$SoloBase
)

$ErrorActionPreference = "Stop"
$raizProyecto = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raizProyecto

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop no está instalado o no está disponible en PATH."
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    $dockerExe = (Get-Command docker).Source
    $carpetaDocker = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $dockerExe))
    $dockerDesktop = Join-Path $carpetaDocker "Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw "Docker está instalado, pero no encuentro Docker Desktop para iniciarlo."
    }
    Write-Host "Abriendo Docker Desktop..."
    Start-Process -FilePath $dockerDesktop
    $motorListo = $false
    for ($intento = 0; $intento -lt 60; $intento++) {
        Start-Sleep -Seconds 2
        & docker info *> $null
        if ($LASTEXITCODE -eq 0) {
            $motorListo = $true
            break
        }
    }
    if (-not $motorListo) {
        throw "Docker Desktop no inició el motor. Abre Docker Desktop y espera a que indique que está en ejecución."
    }
}

Write-Host "Iniciando PostgreSQL local..."
& docker compose up -d db
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo iniciar PostgreSQL. Abre Docker Desktop y vuelve a intentarlo."
}

$conectada = $false
for ($intento = 0; $intento -lt 30; $intento++) {
    & docker compose exec -T db pg_isready -U reportes_app -d reportes_presentacion *> $null
    if ($LASTEXITCODE -eq 0) {
        $conectada = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $conectada) {
    throw "PostgreSQL no respondió después de 60 segundos. Revisa Docker Desktop."
}
Write-Host "PostgreSQL está listo. La app leerá la conexión desde .env."

if ($SoloBase) {
    return
}

$pythonw = Join-Path $raizProyecto ".venv\Scripts\pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw)) {
    throw "No encuentro .venv. Crea el entorno e instala requirements.txt primero."
}

Start-Process -FilePath $pythonw -ArgumentList "menu_grafico.py" -WorkingDirectory $raizProyecto
Write-Host "Centro de reportes iniciado. No necesitas escribir la contraseña."
