#!/usr/bin/env python
import pika
import threading
import time
from time import sleep

def produce_batch():
    print("[x] Fábrica 1: Produzindo lote de produtos.")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica1_request')

    message = "Produção em andamento, requisitando mais peças"
    channel.basic_publish(
        exchange='',
        routing_key='fabrica1_request',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        ))
    print(f" [x] Pedido enviado para almoxarifado: {message}")
    connection.close()

def consume_parts():
    def callback(ch, method, properties, body):
        print(f" [x] Fábrica 1: Peça recebida {body}")
        sleep(2)
        produce_batch()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica1_send', durable=True)
    channel.basic_consume(queue='fabrica1_send', on_message_callback=callback, auto_ack=True)

    print(" [*] Fábrica 1 esperando por peças. Para sair pressione CTRL+C")
    channel.start_consuming()

def start_consumer():
    threading.Thread(target=consume_parts).start()

if __name__ == "__main__":
    try:
        start_consumer()
    except KeyboardInterrupt:
        print('Fábrica 1 interrompida')