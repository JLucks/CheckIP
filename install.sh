#!/bin/bash

# Define variáveis
SERVICE_NAME="check_ip_service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/check_ip.py"
USER="$(whoami)"
PYTHON_PATH="$(which python3)"
USER_HOME=$(eval echo ~$USER)  # Diretório home do usuário
LOG_DIR="$(dirname "$(realpath "$0")")/service_logs"  # Diretório para os arquivos de log e info
LOG_FILE_STDOUT="$LOG_DIR/script_log.txt"
LOG_FILE_STDERR="$LOG_DIR/error_log.txt"

# Função para exibir mensagens de erro e sair
error_exit() {
    echo "$1" 1>&2
    exit 1
}

# Verifica se o script é executado como root
if [ "$(id -u)" -ne "0" ]; then
    error_exit "Este script precisa ser executado como root."
fi

# Verifica se o script Python está no mesmo diretório
if [ ! -f "$SCRIPT_PATH" ]; then
    error_exit "O script Python não foi encontrado no diretório do instalador. Certifique-se de que check_ip.py está no mesmo diretório que install.sh."
fi

# Cria o diretório para arquivos de log, se não existir
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    chmod 777 "$LOG_DIR"  # Permissão total para todos os usuários
fi

# Cria arquivos de log vazios
touch "$LOG_FILE_STDOUT" "$LOG_FILE_STDERR"

# Define permissões para os arquivos de log
chmod 777 "$LOG_FILE_STDOUT" "$LOG_FILE_STDERR"  # Permissão de leitura e escrita para todos os usuários

# Cria o arquivo de serviço
echo "Criando o arquivo de serviço systemd..."

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Serviço de Verificação de IP
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=${PYTHON_PATH} $SCRIPT_PATH
Restart=on-failure
User=$USER
WorkingDirectory=$LOG_DIR
StandardOutput=file:$LOG_FILE_STDOUT
StandardError=file:$LOG_FILE_STDERR

[Install]
WantedBy=multi-user.target
EOF

# Define permissões para o arquivo de serviço
chmod 644 "$SERVICE_FILE"
chown root:root "$SERVICE_FILE"

# Atualiza o systemd para reconhecer o novo serviço
echo "Atualizando o systemd..."
systemctl daemon-reload

# Habilita e inicia o serviço
echo "Habilitando e iniciando o serviço..."
systemctl enable "${SERVICE_NAME}.service"
systemctl start "${SERVICE_NAME}.service"

# Configura o cron para iniciar o serviço diariamente às 7:30
CRON_JOB="30 7 * * * systemctl start ${SERVICE_NAME}.service"
echo "Configurando o cron..."
(crontab -l 2>/dev/null | grep -v "${SERVICE_NAME}.service" ; echo "$CRON_JOB") | crontab -

# Mensagem de conclusão
echo "Instalação e configuração concluídas com sucesso."
echo "Para verificar o status do serviço, use: systemctl status ${SERVICE_NAME}.service"
echo "Para parar o serviço, use: systemctl stop ${SERVICE_NAME}.service"
