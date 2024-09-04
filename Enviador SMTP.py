import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from email.header import Header
from datetime import datetime
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket

# Função para ler a lista de SMTPs
def read_smtp_list(file_path):
    smtp_list = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            host, username, password = line.strip().split(';')
            smtp_list.append({'host': host, 'username': username, 'password': password})
    return smtp_list

# Função para ler a lista de destinatários
def read_recipient_list(file_path):
    with open(file_path, 'r') as file:
        emails = [line.strip() for line in file.readlines()]
    return emails

# Função para enviar um único e-mail
def send_email(smtp_list, email, subject_template, body_template, attachment_path='', timeout=30):
    smtp = random.choice(smtp_list)
    try:
        # Configurações do servidor SMTP com timeout
        server = smtplib.SMTP(smtp['host'], 587, timeout=timeout)
        server.starttls()
        server.login(smtp['username'], smtp['password'])
        
        # Gerar timestamp atual
        timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        
        # Gerar assunto e corpo dinâmicos
        subject = subject_template.format(timestamp=timestamp)
        body = body_template.format(timestamp=timestamp)
        
        # Criação do e-mail
        msg = MIMEMultipart()
        msg['From'] = smtp['username']
        msg['To'] = email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()
        msg['Return-Path'] = smtp['username']
        msg['List-Unsubscribe'] = '<mailto:' + smtp['username'] + '>'
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # Anexar arquivo, se fornecido
        if attachment_path:
            with open(attachment_path, 'rb') as attachment:
                part = MIMEApplication(attachment.read(), Name=attachment_path)
                part['Content-Disposition'] = f'attachment; filename="{attachment_path}"'
                msg.attach(part)
        
        # Envio do e-mail
        server.sendmail(smtp['username'], email, msg.as_string())
        print(f'E-mail enviado para {email} usando {smtp["host"]}')
        
        # Fechar a conexão com o servidor SMTP
        server.quit()
    except (smtplib.SMTPException, socket.timeout) as e:
        print(f'Erro ao enviar e-mail para {email}: {e}')

# Função para enviar e-mails com multithreading
def send_emails_multithread(smtp_list, emails, subject_template, body_template, num_threads=20, timeout=30):
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(send_email, smtp_list, email, subject_template, body_template, '', timeout) for email in emails]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'Erro na thread: {e}')

if __name__ == "__main__":
    # Caminhos para os arquivos de lista de SMTPs e destinatários
    smtp_file = 'VALIDOS.txt'
    recipient_file = '2.txt'
    
    # Assunto e corpo do e-mail com placeholders para timestamps
    email_subject = 'Relatorio Pendente - Segue anexo {timestamp}'
    email_body = ('Desculpe a demora para enviar, segue anexo o relatorio. '
                  'Favor confirmar os valores e me retornar o quanto antes.<br><br>'
                  'https://drive.google.com/file/d/15aO6Wdop8cAvL_ZwO48gxdSWzDB_1PZQ/view?usp=sharing<br><br>'
                  'Para melhor visualização acessar pelo computador.'
                  '<br><br>Atenciosamente,<br><br>'
                  '<i><small>E-mail verificado pelo anti-virus em {timestamp}.</small></i>')
    
    # Caminho do arquivo a ser anexado (opcional)
    #attachment_path = 'RelatoriosAtt.rar'  # Defina como '' se não houver anexo

    # Ler as listas de SMTPs e destinatários
    smtp_list = read_smtp_list(smtp_file)
    recipient_emails = read_recipient_list(recipient_file)
    
    # Enviar os e-mails com multithreading
    send_emails_multithread(smtp_list, recipient_emails, email_subject, email_body, num_threads=5, timeout=10)


#formato lista (mail.xxxxxx.com.br;joao.zamorra@xxxxolar.com.br;amanda130)