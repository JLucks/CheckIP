@echo off
setlocal

:: Define variáveis
set "SERVICE_NAME=CheckIPService"
set "SCRIPT_PATH=%~dp0check_ip.py"
set "USER=%USERNAME%"
set "LOG_DIR=%~dp0check_ip_logs"

:: Função para exibir mensagens de erro e sair
:ErrorExit
echo %1
exit /b 1

:: Verifica se o script Python está no mesmo diretório
if not exist "%SCRIPT_PATH%" (
    call :ErrorExit "O script Python não foi encontrado no diretório do instalador. Certifique-se de que check_ip.py está no mesmo diretório que este script."
)

:: Verifica se o Python está no PATH do sistema
where python >nul 2>&1
if %errorlevel% neq 0 (
    call :ErrorExit "Python não encontrado no PATH do sistema. Certifique-se de que o Python está instalado e configurado nas variáveis de ambiente."
)

:: Cria o diretório para arquivos de log, se não existir
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    icacls "%LOG_DIR%" /grant "%USER%:(OI)(CI)F"
)

:: Cria o serviço
echo Criando o serviço...

:: Remove o serviço se ele já existir
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% == 0 (
    echo Serviço já existe. Removendo...
    sc delete %SERVICE_NAME%
)

:: Cria um novo serviço
sc create %SERVICE_NAME% binPath= "\"python %SCRIPT_PATH%\"" start= auto
if %errorlevel% neq 0 (
    call :ErrorExit "Falha ao criar o serviço."
)

:: Atualiza o serviço (não é necessário se já foi criado com o parâmetro 'start= auto')
echo Atualizando o serviço...
sc config %SERVICE_NAME% start= auto
if %errorlevel% neq 0 (
    call :ErrorExit "Falha ao atualizar o serviço."
)

:: Inicia o serviço
echo Iniciando o serviço...
sc start %SERVICE_NAME%
if %errorlevel% neq 0 (
    call :ErrorExit "Falha ao iniciar o serviço."
)

:: Configura o agendador de tarefas para iniciar o serviço diariamente às 7:30
echo Configurando o Agendador de Tarefas...
schtasks /create /tn "%SERVICE_NAME%" /tr "python %SCRIPT_PATH%" /sc daily /st 07:30
if %errorlevel% neq 0 (
    call :ErrorExit "Falha ao configurar o Agendador de Tarefas."
)

:: Mensagem de conclusão
echo Instalação e configuração concluídas com sucesso.
echo Para verificar o status do serviço, use: sc query %SERVICE_NAME%
echo Para parar o serviço, use: sc stop %SERVICE_NAME%

:: Limpeza
del "%~dp0service.vbs" 2>nul

endlocal
