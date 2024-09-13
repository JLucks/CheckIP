import socket
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Obtém o diretório onde o script está localizado
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuração do logger
logging.basicConfig(
    filename=os.path.join(script_dir, 'service_logs', 'script_log.txt'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Parâmetros padrão para e-mail (podem ser sobrescritos pelo arquivo de configuração)
DEFAULT_EMAIL_HOST = 'smtp.gmail.com'
DEFAULT_EMAIL_PORT = 587

# Lista de parâmetros obrigatórios a serem carregados do arquivo
REQUIRED_EMAIL_CONFIG = ['EMAIL_USER', 'EMAIL_PASSWORD', 'EMAIL_TO']

def load_email_config(config_file='email_config.txt'):
    """Carrega os parâmetros de configuração de e-mail do arquivo e permite sobrescrever host e porta."""
    config = {
        'EMAIL_HOST': DEFAULT_EMAIL_HOST,
        'EMAIL_PORT': DEFAULT_EMAIL_PORT
    }
    
    config_file_path = os.path.join(script_dir, config_file)

    try:
        with open(config_file_path, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key] = value
        
        # Verifica se todos os parâmetros necessários estão presentes
        missing_params = [param for param in REQUIRED_EMAIL_CONFIG if param not in config or not config[param].strip()]
        if missing_params:
            logging.error(f"Parâmetros ausentes ou inválidos no arquivo de configuração: {', '.join(missing_params)}")
            return None

        # Verifica se EMAIL_PORT é um número, se estiver presente no arquivo
        if 'EMAIL_PORT' in config:
            try:
                config['EMAIL_PORT'] = int(config['EMAIL_PORT'])
            except ValueError:
                logging.error("O parâmetro 'EMAIL_PORT' deve ser um número inteiro.")
                return None

        # Processa o parâmetro EMAIL_TO para permitir múltiplos destinatários
        if 'EMAIL_TO' in config:
            config['EMAIL_TO'] = [email.strip() for email in config['EMAIL_TO'].split(',')]
        else:
            logging.error("O parâmetro 'EMAIL_TO' está faltando no arquivo de configuração.")
            return None

        logging.info(f"Configuração de e-mail carregada de {config_file_path}.")
    except FileNotFoundError:
        logging.warning(f"Arquivo de configuração {config_file_path} não encontrado. Usando valores padrão para host e porta.")
    except Exception as e:
        logging.error(f"Erro ao carregar a configuração de e-mail: {e}")
        return None

    return config

def send_email(subject, body, email_config):
    """Envia o e-mail com os dados da máquina."""
    try:
        if not email_config:
            logging.warning("Configuração de e-mail ausente ou inválida. Envio de e-mail cancelado.")
            return

        # Cria uma nova instância do servidor SMTP
        with smtplib.SMTP(email_config['EMAIL_HOST'], email_config['EMAIL_PORT']) as server:
            server.starttls()
            server.login(email_config['EMAIL_USER'], email_config['EMAIL_PASSWORD'])

            # Envia o e-mail para cada destinatário
            for recipient in email_config['EMAIL_TO']:
                # Cria a mensagem
                msg = MIMEMultipart()
                msg['From'] = email_config['EMAIL_USER']
                msg['To'] = recipient
                msg['Subject'] = subject
                msg['Reply-To'] = email_config['EMAIL_USER']
                msg['X-Mailer'] = 'Python Script'
        
                # Adiciona o corpo da mensagem
                msg.attach(MIMEText(body, 'plain'))

                # Enviando o e-mail
                server.sendmail(email_config['EMAIL_USER'], recipient, msg.as_string())
                logging.info(f"E-mail enviado para {recipient}")

            logging.info("Todos os e-mails foram enviados com sucesso.")

    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}")

def get_machine_info():
    """Obtém o nome da máquina e IP."""
    try:
        hostname = socket.gethostname()

        # Obtendo o IP da máquina
        ip_address = None
        try:
            # Tenta obter o IP externo
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                ip_address = s.getsockname()[0]
        except Exception as e:
            logging.warning(f"Falha ao obter IP externo: {e}")

            try:
                # Tenta obter o IP local
                ip_address = socket.gethostbyname(hostname)
            except Exception as e:
                logging.error(f"Falha ao obter IP local: {e}")
                ip_address = 'Não foi possível obter o IP'

        return hostname, ip_address
    except Exception as e:
        logging.error(f"Erro ao obter informações da máquina: {e}")
        return None, None

def read_file_content(filename):
    """Lê o conteúdo de um arquivo."""
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logging.warning(f"Arquivo '{file_path}' não encontrado.")
        return None
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo '{file_path}': {e}")
        return None

def save_info_to_file(filename, content):
    """Salva as informações da máquina em um arquivo."""
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        # Define permissões para todos os usuários
        os.chmod(file_path, 0o666)
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo '{file_path}': {e}")

def main():
    """Fluxo principal do script."""
    logging.info("Início do script")
    
    # Carrega a configuração de e-mail
    email_config = load_email_config()

    filename = 'machine_info.txt'
    hostname, ip_address = get_machine_info()

    if hostname is None or ip_address is None:
        logging.error("Não foi possível obter todas as informações da máquina.")
        return

    # Formata as informações para salvar
    new_content = (
        f"Nome da Máquina: {hostname}\n"
        f"IP da Máquina: {ip_address}\n"
    )

    # Lê o conteúdo atual do arquivo
    existing_content = read_file_content(filename)

    # Verifica se o conteúdo mudou
    if new_content != existing_content:
        save_info_to_file(filename, new_content)
        logging.info("Informações atualizadas e salvas.")

        # Envia o e-mail com as novas informações
        subject = "Atualização de informações da máquina"
        body = f"As seguintes informações da máquina foram atualizadas:\n\n{new_content}"
        send_email(subject, body, email_config)
    else:
        logging.info("As informações não mudaram. Nada foi alterado.")
    
    logging.info("Fim do script")

if __name__ == "__main__":
    main()
