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

linhasQueue = []
for i in range(8):
    linhasQueue.append(Queue())

quantidadePartes = [43+20, 43+33, 43+31, 43+29, 43+24]

def handleReceivingParts():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica_send')

    def callback(ch, method, properties, body):
        content = json.loads(body)
        if(content["fabrica"] == 2):
            # print(f" [x] Recebida parte {linhasQueue[content["linha"]-1].size()} da linha  {content["linha"]}")
            linhasQueue[content["linha"]-1].enqueue(content["parte"])

    channel.basic_consume(queue='fabrica_send', on_message_callback=callback, auto_ack=True)

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

def linhaDeProducao(linha):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica2_produz')

    # Fabrica item de acordo com o que a main pedir
    def callback(ch, method, properties, body):
        content = json.loads(body)
        if content["linha"] == linha:
            # Se faltam partes, pedimos para o almoxarifado
            if(linhasQueue[linha-1].size() < quantidadePartes[content["produto"]]):
                requestPart(2, linha)
            # Senão só produzimos
            else:
                depositar(str(uuid.uuid4()), content["produto"])

    channel.basic_consume(queue='fabrica2_produz', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def pedirProducao(linha, produto):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica2_produz')

    message = {"produto": produto, "linha": linha}

    channel.basic_publish(exchange='', routing_key='fabrica2_produz', body=json.dumps(message))
    connection.close()

def main():
    print(" [x] Começando fabrica 2")

    threading.Thread(target=handleReceivingParts).start()

    # Iniciando fabricas
    threading.Thread(target=linhaDeProducao, args=[1]).start()
    threading.Thread(target=linhaDeProducao, args=[2]).start()
    threading.Thread(target=linhaDeProducao, args=[3]).start()
    threading.Thread(target=linhaDeProducao, args=[4]).start()
    threading.Thread(target=linhaDeProducao, args=[5]).start()
    threading.Thread(target=linhaDeProducao, args=[6]).start()
    threading.Thread(target=linhaDeProducao, args=[7]).start()
    threading.Thread(target=linhaDeProducao, args=[8]).start()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='new_day')

    def callback(ch, method, properties, body):
        content = json.loads(body)

        linha = 1

        print("New day!")
        for i in range(5):
            stillNeed = content[i]

            while stillNeed > 0:
                pedirProducao(linha, i)

                if linha == 8:
                    linha = 1
                else:
                    linha += 1

    channel.basic_consume(queue='new_day', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Fabrica 2 interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)