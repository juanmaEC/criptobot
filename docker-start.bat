@echo off
REM Script de inicio para CryptoPump Bot con Docker en Windows
REM Uso: docker-start.bat [start|stop|restart|logs|status|clean]

setlocal enabledelayedexpansion

REM Colores para output (Windows PowerShell)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Función para imprimir mensajes con colores
:print_message
echo %GREEN%[INFO]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:print_header
echo %BLUE%================================%NC%
echo %BLUE%  CryptoPump Bot - Docker%NC%
echo %BLUE%================================%NC%
goto :eof

REM Verificar que Docker esté instalado
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker no está instalado. Por favor instala Docker Desktop primero."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit /b 1
)
goto :eof

REM Verificar archivo .env
:check_env_file
if not exist ".env" (
    call :print_error "Archivo .env no encontrado. Por favor crea el archivo .env basado en env_example.txt"
    exit /b 1
)
goto :eof

REM Crear directorios necesarios
:create_directories
call :print_message "Creando directorios necesarios..."
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "models" mkdir models
call :print_message "Directorios creados correctamente"
goto :eof

REM Función para iniciar el bot
:start_bot
call :print_header
call :print_message "Iniciando CryptoPump Bot con Docker..."
call :check_docker
call :check_env_file
call :create_directories

call :print_message "Construyendo imágenes de Docker..."
docker-compose build

call :print_message "Iniciando servicios..."
docker-compose up -d

call :print_message "Esperando que los servicios estén listos..."
timeout /t 10 /nobreak >nul

call :print_message "Verificando estado de los servicios..."
docker-compose ps

call :print_message "CryptoPump Bot iniciado correctamente!"
call :print_message "Accede a Flower (monitoreo): http://localhost:5555"
call :print_message "Logs: docker-compose logs -f"
goto :eof

REM Función para detener el bot
:stop_bot
call :print_header
call :print_message "Deteniendo CryptoPump Bot..."
docker-compose down
call :print_message "Bot detenido correctamente"
goto :eof

REM Función para reiniciar el bot
:restart_bot
call :print_header
call :print_message "Reiniciando CryptoPump Bot..."
docker-compose down
docker-compose up -d
call :print_message "Bot reiniciado correctamente"
goto :eof

REM Función para mostrar logs
:show_logs
call :print_header
call :print_message "Mostrando logs del bot..."
docker-compose logs -f
goto :eof

REM Función para mostrar estado
:show_status
call :print_header
call :print_message "Estado de los servicios:"
docker-compose ps

echo.
call :print_message "Uso de recursos:"
docker stats --no-stream
goto :eof

REM Función para limpiar contenedores y volúmenes
:clean_all
call :print_header
call :print_warning "Esta acción eliminará todos los contenedores, volúmenes y datos del bot."
set /p "confirm=¿Estás seguro? (y/N): "
if /i "!confirm!"=="y" (
    call :print_message "Limpiando todo..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    call :print_message "Limpieza completada"
) else (
    call :print_message "Limpieza cancelada"
)
goto :eof

REM Función para mostrar ayuda
:show_help
call :print_header
echo Uso: %~nx0 [COMANDO]
echo.
echo Comandos disponibles:
echo   start     - Iniciar el bot
echo   stop      - Detener el bot
echo   restart   - Reiniciar el bot
echo   logs      - Mostrar logs en tiempo real
echo   status    - Mostrar estado de los servicios
echo   clean     - Limpiar contenedores y volúmenes
echo   help      - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   %~nx0 start
echo   %~nx0 logs
echo   %~nx0 status
goto :eof

REM Función principal
:main
if "%1"=="" goto :show_help
if "%1"=="start" goto :start_bot
if "%1"=="stop" goto :stop_bot
if "%1"=="restart" goto :restart_bot
if "%1"=="logs" goto :show_logs
if "%1"=="status" goto :show_status
if "%1"=="clean" goto :clean_all
if "%1"=="help" goto :show_help
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help

call :print_error "Comando desconocido: %1"
call :show_help
exit /b 1

REM Ejecutar función principal
call :main %*
