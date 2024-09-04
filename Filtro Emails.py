# Lista de domínios a serem excluídos
excluded_domains = ["gmail.com", "hotmail.com", "hotmail.com.br", "outlook.com", "outlook.com.br", "yahoo.com.br", "yahoo.com"]

def filter_emails(input_file, output_file, excluded_domains):
    with open(input_file, 'r') as file:
        emails = file.readlines()
    
    filtered_emails = []
    
    for email in emails:
        email = email.strip()  # Remove espaços em branco
        domain = email.split('@')[-1]
        if domain not in excluded_domains:
            filtered_emails.append(email)
    
    with open(output_file, 'w') as file:
        for email in filtered_emails:
            file.write(email + '\n')

# Nome dos arquivos de entrada e saída
input_file = 'lista.txt'
output_file = 'filtered_emails.txt'

filter_emails(input_file, output_file, excluded_domains)

print(f"E-mails filtrados foram salvos em {output_file}")
