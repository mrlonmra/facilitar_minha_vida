import requests
import time
import os
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# API URLs
token_url = 'https://api.go.gov.br/token'
api_url = 'https://api.go.gov.br/sigac/atendimentos/v1.0/agendamento/listarDatasAgendamento?idSenha=58&status=D&codgMunicipio=25300'

# Headers for token request
token_headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.go.gov.br',
    'Referer': 'https://www.go.gov.br/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# WhatsApp notification URL and headers
whatsapp_url = 'http://whatsapp.studiokatyanemendes.com.br:8084/message/sendText/marlon'
whatsapp_headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbnN0YW5jZU5hbWUiOiJtYXJsb24iLCJhcGlOYW1lIjoid2hhdHNhcHAtYXBpIiwidG9rZW5JZCI6IjAxSjVEU0RZM0FQV0gxRVBFOU5IRzFLRlBBIiwiaWF0IjoxNzIzODE4NTA2LCJleHAiOjE3MjM4MTg1MDYsInN1YiI6ImctdCJ9.ZmydGHiWNccUULpXxnAs182iT6q6DYw5SLnNViBvyCk',
    'Content-Type': 'application/json'
}

# Configurable variables
quantidade_dias = ""  # Example: Check dates from today up to 7 days ahead
data_especifica = "06/09/2024"  # Specific date to check

def obter_novo_token():
    payload = {
        'grant_type': 'client_credentials',
        'client_id': 'jMQoyH_T2GpWXwBlH6goWfBBdr0a',
        'client_secret': 'k8BOsIHTF6sARfHq4qBPsvaYjf4a'
    }
    try:
        response = requests.post(token_url, headers=token_headers, data=payload)
        response.raise_for_status()  # Will raise an exception for 4xx/5xx responses
        new_token = response.json().get('access_token')
        if new_token:
            logging.info(f"Novo token obtido com sucesso: {new_token}")
            return new_token
        else:
            logging.error("Falha ao obter novo token: Resposta não contém access_token.")
            return None
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Erro HTTP ao obter novo token: {http_err} - {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro ao obter novo token: {req_err}")
        return None

def consultar_datas(token):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Origin': 'https://www.go.gov.br',
        'Referer': 'https://www.go.gov.br/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    logging.info("Consultando datas de agendamento...")
    response = requests.get(api_url, headers=headers)
    if response.status_code == 401:  # Unauthorized, need to refresh token
        logging.warning("Token expirado. Tentando obter novo token.")
        token = obter_novo_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
            response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        logging.info("Consulta realizada com sucesso.")
        return response.json()
    else:
        logging.error(f"Erro ao consultar API: {response.status_code} - {response.text}")
        return None

def verificar_datas_disponiveis(datas, quantidade_dias=None, data_especifica=None):
    hoje = datetime.now().date()
    datas_filtradas = []

    for data in datas:
        try:
            data_formatada = datetime.strptime(data, '%d/%m/%Y').date()
            if data_especifica:
                if data_formatada == datetime.strptime(data_especifica, '%d/%m/%Y').date():
                    datas_filtradas.append(data)
                    break  # Encontrou a data específica, não precisa continuar
            elif quantidade_dias is not None:
                limite = hoje + timedelta(days=quantidade_dias)
                if hoje <= data_formatada <= limite:
                    datas_filtradas.append(data)
        except ValueError as e:
            logging.error(f"Erro ao formatar data: {e}")

    return datas_filtradas

def enviar_notificacao(locais_com_vagas):
    if locais_com_vagas:
        mensagem = "Locais com vagas disponíveis:\n"
        for local, datas in locais_com_vagas.items():
            mensagem += f"- {local}: {', '.join(datas)}\n"

        payload = {
            "number": "5562985009520@s.whatsapp.net",
            "options": {
                "delay": 1200,
                "presence": "composing"
            },
            "textMessage": {
                "text": mensagem.strip()
            }
        }
        try:
            response = requests.post(whatsapp_url, headers=whatsapp_headers, json=payload)
            response.raise_for_status()  # Will raise an exception for 4xx/5xx responses
            logging.info("Notificação enviada com sucesso!")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar notificação: {e}")
    else:
        logging.info("Nenhum local com vagas disponíveis para os filtros aplicados.")

def main():
    token = obter_novo_token()
    if not token:
        logging.error("Não foi possível obter o token inicial. Abortando...")
        return

    while True:
        agendamentos = consultar_datas(token)
        if agendamentos:
            locais_com_vagas = {}
            for unidade in agendamentos:
                datas_filtradas = verificar_datas_disponiveis(unidade['datas'], quantidade_dias=quantidade_dias, data_especifica=data_especifica)
                if datas_filtradas:
                    locais_com_vagas[unidade['nomeUnidade']] = datas_filtradas

            enviar_notificacao(locais_com_vagas)
        else:
            logging.warning("Nenhum agendamento recebido ou erro na consulta.")

        time.sleep(30)  # Espera 1 minuto antes de nova consulta

if __name__ == "__main__":
    main()