param(
    [switch]$SoloBase
)

$ErrorActionPreference = "Stop"
# PowerShell 7 puede convertir un motor apagado en una excepción antes del reintento.
$PSNativeCommandUseErrorActionPreference = $false
$raizProyecto = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raizProyecto

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $rutasDocker = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin'),
        (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin')
    )
    foreach ($rutaDocker in $rutasDocker) {
        if (Test-Path -LiteralPath (Join-Path $rutaDocker 'docker.exe')) {
            $env:PATH = "$rutaDocker;$env:PATH"
            break
        }
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "No encuentro Docker Desktop. Instálalo o comprueba su ubicación antes de iniciar el proyecto."
    }
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
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
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
        & docker info
        throw "Docker no inició después de 120 segundos. Revisa el error anterior y el estado del motor en Docker Desktop."
    }
}

& docker compose version
if ($LASTEXITCODE -ne 0) {
    throw "Docker responde, pero Docker Compose no está disponible. Repara o actualiza Docker Desktop."
}

Write-Host "Iniciando PostgreSQL local..."
& docker compose up -d db
if ($LASTEXITCODE -ne 0) {
    & docker compose ps -a
    & docker compose logs --tail 20 db
    throw "No se pudo iniciar PostgreSQL. Revisa el error anterior; si indica que el puerto 5434 está ocupado, comprueba qué proceso lo utiliza."
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
    & docker compose ps -a
    & docker compose logs --tail 20 db
    throw "Docker está activo, pero PostgreSQL no respondió después de 60 segundos. Revisa los registros anteriores."
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
