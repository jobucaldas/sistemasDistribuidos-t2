#!/usr/bin/env python
import json
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
    #print(" [x] Recebendo parte do fornecedor")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='envio_parte_fornecedor')

    def callback(ch, method, properties, body):
        #print(f" [x] Recebida parte {q.size()}/{green}")
        q.enqueue(str(body))
        if(q.size() < yellow):
            requestPart()

    channel.basic_consume(queue='envio_parte_fornecedor', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def sendPart(fabrica, linha):
    # print(" [x] Enviando parte pra fabrica")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica_send')

    message = {"parte": q.dequeue(), "fabrica": fabrica, "linha": linha}

    channel.basic_publish(exchange='', routing_key='fabrica_send', body=json.dumps(message))
    connection.close()

def requestPart():
    #print(" [x] Pedindo parte ao fornecedor")
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fornecedor_request')

    message = "More parts?"

    channel.basic_publish(exchange='', routing_key='fornecedor_request', body=message)
    connection.close()

def main():
    print(" [x] Começando almoxarifado")

    threading.Thread(target=handleReceivingParts).start()
    requestPart()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica_request')

    def callback(ch, method, properties, body):
        content = json.loads(body)

        # print(f" [x] Recebido pedido da fabrica {content["fabrica"]} e linha {content["linha"]}")
        
        if(q.size() < red):
            requestPart()

        sendPart(content["fabrica"], content["linha"])

    channel.basic_consume(queue='fabrica_request', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Almoxarifado interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)