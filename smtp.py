import base64
import json
import os
import socket
import ssl
from datetime import datetime

TIMEOUT = 1


def request(socket, request):
    socket.send((request + '\n').encode())
    recv_data = b""
    try:
        while chunk := socket.recv(4096):
            recv_data += chunk
    finally:
        return recv_data.decode()


def message_prepare():
    with open('smtp_config.json', 'r') as json_file:  # новое
        file = json.load(json_file)
        user_name_from = file['from']  # считываем из конфига кто отправляет
        user_name_to = file[
            'to']  # считываем из конфига кому отправляем (сделать список)
        attachment_folder_name = file['attachment']
        attachment_folder_dir = os.getcwd() + '\\' + attachment_folder_name

        subject_msg = file['subject']

    boundary_msg = "bound.40629"
    cur_time = datetime.now()
    headers = [
        f'From: {user_name_from}',
        f'To: {user_name_to}',
        f'Subject: {subject_msg}',
        f"Date: {cur_time.strftime('%d/%m/%y')}"
        f'MIME-Version: 1.0',
        'Content-Type: multipart/mixed;'
        f'  boundary={boundary_msg}',
        ''
    ]
    headers_str = '\n'.join(headers)
    #print(headers_str)
    message_body = []

    with open('msg.txt') as file_msg:
        # тело сообщения началось
        message_body = [f'--{boundary_msg}']
        message_body.append('Content-Type: text/plain; charset=utf-8\n')
        msg = file_msg.read()
        msg = msg.replace('.','..')
        message_body.append(msg)

    # attachments(only pictures)
    for filename in os.listdir(attachment_folder_dir):
        #check types
        message_body.append(f'--{boundary_msg}')
        message_body.append(f'Content-Disposition: attachment;')
        message_body.append(f'   filename="{filename}"')
        message_body.append('Content-Transfer-Encoding: base64')
        message_body.append('Content-Type: image/jpeg;\n')

        with open(os.path.join(attachment_folder_dir, filename),
                  'rb') as picture_file:
            picture = base64.b64encode(picture_file.read()).decode("UTF-8")
        message_body.append(picture)

    message_body.append(f'--{boundary_msg}--')
    message_body_str = '\n'.join(message_body)

    message = headers_str + '\n' + message_body_str + '\n.\n'
    return message

HOST_ADDR = 'smtp.yandex.ru'
PORT = 465
with open('smtp_config.json', 'r') as f:
    content = json.load(f)
    USER_NAME = content['login']
    password = content['password'] # считываем пароль из файла

ssl_contex = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_contex.check_hostname = False
ssl_contex.verify_mode = ssl.CERT_NONE

def send_msg():
    with socket.create_connection((HOST_ADDR, PORT),timeout=TIMEOUT) as sock:
        with ssl_contex.wrap_socket(sock, server_hostname=HOST_ADDR) as client:
            print(client.recv(1024))  # в smpt сервер первый говорит
            print(request(client, f'ehlo {USER_NAME}'))  # hello->helo->ehlo

            base64login = base64.b64encode(
                USER_NAME.encode()).decode()  # Переводим в Base64 формат
            base64password = base64.b64encode(
                password.encode()).decode()  # Base64 кодирование, НЕ ШИФРОВАНИЕ

            print(request(client, 'AUTH LOGIN'))
            print(request(client, base64login))
            print(request(client, base64password))
            print(request(client, f'MAIL FROM:{USER_NAME}'))
            print(request(client, f"RCPT TO:{USER_NAME}"))
            print(request(client, 'DATA'))
            print(request(client, message_prepare()))

if __name__ == '__main__':
    send_msg()