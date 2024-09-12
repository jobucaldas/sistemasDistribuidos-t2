#!/usr/bin/env python
import json
from time import sleep
import uuid
import pika
import threading
import sys
from random import randrange

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

linhasQueue = [Queue(), Queue(), Queue(), Queue(), Queue()] 
itensProduzidos = [0, 0, 0, 0, 0]

tamanhoProducao = 48
produto1 = 43+20
produto2 = 43+33
produto3 = 43+31
produto4 = 43+29
produto5 = 43+24

def handleReceivingParts():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica_send')

    def callback(ch, method, properties, body):
        content = json.loads(body)
        if(content["fabrica"] == 1):
            # print(f" [x] Recebida parte {linhasQueue[content["linha"]-1].size()} da linha  {content["linha"]}")
            linhasQueue[content["linha"]-1].enqueue(content["parte"])

    channel.basic_consume(queue='fabrica_send', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def handleNewDay():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='new_day')

    def callback(ch, method, properties, body):
        # Reset all
        for i in range(5):
            linhasQueue[i] = Queue()
            itensProduzidos[i] = 0

    channel.basic_consume(queue='new_day', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def requestPart(fabrica, linha):
    # print(" [x] Pedindo parte ao almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica_request')

    message = {"fabrica": fabrica, "linha": linha}

    channel.basic_publish(exchange='', routing_key='fabrica_request', body=json.dumps(message))
    connection.close()

def depositar(produto, tipo):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='depositar')

    message = {"produto": produto, "tipo": tipo}

    channel.basic_publish(exchange='', routing_key='depositar', body=json.dumps(message))
    connection.close()

def linhaDeProducao(quantidadePartes, linha):
    while True:
        if(itensProduzidos[linha-1] < tamanhoProducao):
            # Se faltam partes, pedimos para o almoxarifado
            if(linhasQueue[linha-1].size() < quantidadePartes):
                requestPart(1, linha)
            # Senão só produzimos
            else:
                itensProduzidos[linha-1] += 1
                depositar(str(uuid.uuid4()), linha)
                #print(f" [X] Fabricado item {itensProduzidos}/{tamanhoProducao}")

                if(itensProduzidos[linha-1] >= tamanhoProducao):
                    print(f" [X] Linha {linha} concluida!")

def main():
    print(" [x] Começando fabrica 1")

    threading.Thread(target=handleReceivingParts).start()
    threading.Thread(target=handleNewDay).start()

    threading.Thread(target=linhaDeProducao, args=[produto1, 1]).start()
    threading.Thread(target=linhaDeProducao, args=[produto2, 2]).start()
    threading.Thread(target=linhaDeProducao, args=[produto3, 3]).start()
    threading.Thread(target=linhaDeProducao, args=[produto4, 4]).start()
    threading.Thread(target=linhaDeProducao, args=[produto5, 5]).start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Fabrica 1 interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)