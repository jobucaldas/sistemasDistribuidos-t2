#!/usr/bin/env python
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
        print(f" [x] Recebida parte {q.size()}/{green}")
        q.enqueue(str(body))
        if(q.size() < yellow):
            requestPart()

    channel.basic_consume(queue='envio_parte_fornecedor', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def sendPart():
    print(" [x] Enviando parte pra fabrica")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica1_send')

    message = q.dequeue()

    channel.basic_publish(exchange='', routing_key='fabrica1_send', body=message)
    print(" [x] Parte {message} enviada")
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

    def callback(ch, method, properties, body):
        print(f" [x] Received request")
        if(q.size() < red):
            requestPart()
            sleep(1000) # Tempo até o carregamento do fornecedor chegar

        sendPart()

    channel.basic_consume(queue='fabrica1_request', on_message_callback=callback, auto_ack=True)

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