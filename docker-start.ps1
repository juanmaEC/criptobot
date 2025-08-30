# Script de inicio para CryptoPump Bot con Docker en PowerShell
# Uso: .\docker-start.ps1 [start|stop|restart|logs|status|clean]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Colores para output
$Red = "`e[91m"
$Green = "`e[92m"
$Yellow = "`e[93m"
$Blue = "`e[94m"
$NC = "`e[0m"

function Write-Info {
    param([string]$Message)
    Write-Host "$Green[INFO]$NC $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "$Yellow[WARNING]$NC $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "$Red[ERROR]$NC $Message"
}

function Write-Header {
    Write-Host "$Blue================================$NC"
    Write-Host "$Blue  CryptoPump Bot - Docker$NC"
    Write-Host "$Blue================================$NC"
}

function Test-Docker {
    try {
        $null = docker --version
        $null = docker-compose --version
        return $true
    }
    catch {
        Write-Error "Docker no está instalado o no está ejecutándose. Por favor instala Docker Desktop primero."
        return $false
    }
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Error "Archivo .env no encontrado. Por favor crea el archivo .env basado en env_example.txt"
        return $false
    }
    return $true
}

function Create-Directories {
    Write-Info "Creando directorios necesarios..."
    if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Name "logs" | Out-Null }
    if (-not (Test-Path "data")) { New-Item -ItemType Directory -Name "data" | Out-Null }
    if (-not (Test-Path "models")) { New-Item -ItemType Directory -Name "models" | Out-Null }
    Write-Info "Directorios creados correctamente"
}

function Start-Bot {
    Write-Header
    Write-Info "Iniciando CryptoPump Bot con Docker..."
    
    if (-not (Test-Docker)) { return }
    if (-not (Test-EnvFile)) { return }
    Create-Directories
    
    Write-Info "Construyendo imágenes de Docker..."
    docker-compose build
    
    Write-Info "Iniciando servicios..."
    docker-compose up -d
    
    Write-Info "Esperando que los servicios estén listos..."
    Start-Sleep -Seconds 10
    
    Write-Info "Verificando estado de los servicios..."
    docker-compose ps
    
    Write-Info "CryptoPump Bot iniciado correctamente!"
    Write-Info "Accede a Flower (monitoreo): http://localhost:5555"
    Write-Info "Logs: .\docker-start.ps1 logs"
}

function Stop-Bot {
    Write-Header
    Write-Info "Deteniendo CryptoPump Bot..."
    docker-compose down
    Write-Info "Bot detenido correctamente"
}

function Restart-Bot {
    Write-Header
    Write-Info "Reiniciando CryptoPump Bot..."
    docker-compose down
    docker-compose up -d
    Write-Info "Bot reiniciado correctamente"
}

function Show-Logs {
    Write-Header
    Write-Info "Mostrando logs del bot..."
    docker-compose logs -f
}

function Show-Status {
    Write-Header
    Write-Info "Estado de los servicios:"
    docker-compose ps
    
    Write-Host ""
    Write-Info "Uso de recursos:"
    docker stats --no-stream
}

function Clean-All {
    Write-Header
    Write-Warning "Esta acción eliminará todos los contenedores, volúmenes y datos del bot."
    $confirm = Read-Host "¿Estás seguro? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-Info "Limpiando todo..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        Write-Info "Limpieza completada"
    } else {
        Write-Info "Limpieza cancelada"
    }
}

function Show-Help {
    Write-Header
    Write-Host "Uso: .\docker-start.ps1 [COMANDO]"
    Write-Host ""
    Write-Host "Comandos disponibles:"
    Write-Host "  start     - Iniciar el bot"
    Write-Host "  stop      - Detener el bot"
    Write-Host "  restart   - Reiniciar el bot"
    Write-Host "  logs      - Mostrar logs en tiempo real"
    Write-Host "  status    - Mostrar estado de los servicios"
    Write-Host "  clean     - Limpiar contenedores y volúmenes"
    Write-Host "  help      - Mostrar esta ayuda"
    Write-Host ""
    Write-Host "Ejemplos:"
    Write-Host "  .\docker-start.ps1 start"
    Write-Host "  .\docker-start.ps1 logs"
    Write-Host "  .\docker-start.ps1 status"
}

# Procesar comandos
switch ($Command.ToLower()) {
    "start" { Start-Bot }
    "stop" { Stop-Bot }
    "restart" { Restart-Bot }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "clean" { Clean-All }
    "help" { Show-Help }
    default { 
        Write-Error "Comando desconocido: $Command"
        Show-Help
    }
}




