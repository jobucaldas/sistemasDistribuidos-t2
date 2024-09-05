#!/usr/bin/env python
import pika
import sys
import threading
import uuid

def sendPart():
    print(" [x] Enviando parte")
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='envio_parte_fornecedor')

    message = str(uuid.uuid4())

    channel.basic_publish(exchange='', routing_key='envio_parte_fornecedor', body=message)
    print(" [x] Parte " + message + " enviada")
    connection.close()

def main():
    print(" [x] Iniciando fornecedor")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fornecedor_request')

    def callback(ch, method, properties, body):
        print(f" [x] Recebido pedido")
        sendPart()

    channel.basic_consume(queue='fornecedor_request', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Fornecedor interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)