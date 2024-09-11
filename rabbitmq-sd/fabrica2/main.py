#!/usr/bin/env python
import threading
import pika
import sys
import random
from time import sleep

def send_request_to_warehouse(product, quantity):
    print(f"[x] Fábrica 2: Requisitando {quantity} peças para o produto {product}")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica2_request')

    message = f"Requisitando {quantity} peças para produto {product}"
    channel.basic_publish(
        exchange='',
        routing_key='fabrica2_request',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent
        ))
    print(f" [x] Pedido enviado ao almoxarifado: {message}")
    connection.close()

def produce_batch(product, quantity):
    print(f"[x] Fábrica 2: Produzindo lote de {quantity} unidades do produto {product}")
    sleep(random.uniform(1, 3))
    print(f"[x] Fábrica 2: Lote de {quantity} unidades do produto {product} finalizado.")

def consume_parts():
    def callback(ch, method, properties, body):
        print(f"[x] Fábrica 2: Peça recebida {body}")
        product = random.choice(['Pv1', 'Pv2', 'Pv3', 'Pv4', 'Pv5'])
        quantity = random.randint(20, 50)
        produce_batch(product, quantity)
        send_request_to_warehouse(product, quantity)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica2_send', durable=True)
    channel.basic_consume(queue='fabrica2_send', on_message_callback=callback, auto_ack=True)

    print(" [*] Fábrica 2 aguardando peças. Para sair pressione CTRL+C")
    channel.start_consuming()

def start_consumer():
    threading.Thread(target=consume_parts).start()

if __name__ == "__main__":
    try:
        start_consumer()
    except KeyboardInterrupt:
        print('Fábrica 2 interrompida')