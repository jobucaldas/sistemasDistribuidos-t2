#!/usr/bin/env python
import os
from time import sleep
import pika
import threading
import sys

class Queue:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

q = Queue()
green = 10000
yellow = green*0.6+1
red = green*0.25+1

def handleReceivingParts():
    print(" [x] Recebendo parte do fornecedor")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='envio_parte_fornecedor')

    def callback(ch, method, properties, body):
        q.enqueue(str(body))
        print(f" [x] Recebida parte {q.size()}/{green}")
        if q.size() < yellow:
            requestPart()

    channel.basic_consume(queue='envio_parte_fornecedor', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def sendPart(fabrica_queue):
    if q.isEmpty():
        print(" [x] Nenhuma parte disponível para envio")
        return

    print(f" [x] Enviando parte para {fabrica_queue}")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue=fabrica_queue)

    message = q.dequeue()

    channel.basic_publish(exchange='', routing_key=fabrica_queue, body=message)
    print(f" [x] Parte {message} enviada para {fabrica_queue}")
    connection.close()

def requestPart():
    print(" [x] Pedindo parte ao fornecedor")
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fornecedor_request')

    message = "More parts please"

    channel.basic_publish(exchange='', routing_key='fornecedor_request', body=message)
    connection.close()

def main():
    print(" [x] Começando almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica1_request')
    channel.queue_declare(queue='fabrica2_request')

    def callback(ch, method, properties, body):
        print(f" [x] Pedido recebido de {method.routing_key}")
        if(q.size() < red):
            requestPart()
            # sleep(1000)

        if method.routing_key == 'fabrica1_request':
            if not q.isEmpty():
                sendPart('fabrica1_send')
        elif method.routing_key == 'fabrica2_request':
            if not q.isEmpty():
                sendPart('fabrica2_send')

    channel.basic_consume(queue='fabrica1_request', on_message_callback=callback, auto_ack=True)
    channel.basic_consume(queue='fabrica2_request', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    try:
        threading.Thread(target=handleReceivingParts).start()
        requestPart()
        main()
    except KeyboardInterrupt:
        print('Almoxarifado interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)