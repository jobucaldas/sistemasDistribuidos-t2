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

linhasQueue = [Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue()]

produtosAFazer = [0, 0, 0, 0, 0]

quantidadePartes = [43+20, 43+33, 43+31, 43+29, 43+24]

def handleReceivingParts():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica2_send')

    def callback(ch, method, properties, body):
        content = json.loads(body)
        # print(f" [x] Recebida parte { linhasQueue[content['linha']-1].size()} da linha  {content['linha']}" )
        linhasQueue[content['linha']-1].enqueue(content['parte'])

    channel.basic_consume(queue='fabrica2_send', on_message_callback=callback, auto_ack=True)

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

    # print(f"Enviando produto {produto} de tipo de produto {tipo}")

    channel.basic_publish(exchange='', routing_key='depositar', body=json.dumps(message))
    connection.close()

def linhaDeProducao(linha):
    curProduct = 1
    pedido = False
    while True:
        if produtosAFazer[curProduct-1] > 0:
            # print(quantidadePartes)

            if not pedido:
                # Pede partes que precisa
                for i in range(quantidadePartes[curProduct-1]):
                    # print(f"Pedindo parte para linha {linha}")
                    requestPart(2, linha)
            pedido = True

            # Espero ter peças
            if(linhasQueue[linha-1].size() >= quantidadePartes[curProduct-1]):
                produtosAFazer[curProduct-1] -= 1
                pedido = False
                # Daí produzimos um produto unico
                for i in range(quantidadePartes[curProduct-1]):
                    linhasQueue[linha-1].dequeue()

                depositar(str(uuid.uuid4()), curProduct)
        else:
            if curProduct >= 5:
                curProduct = 1
            else:
                curProduct += 1

def main():
    print(" [x] Começando fabrica 2")

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='pedido_fabrica2')

    # Iniciando fabricas
    threading.Thread(target=linhaDeProducao, args=[1]).start()
    threading.Thread(target=linhaDeProducao, args=[2]).start()
    threading.Thread(target=linhaDeProducao, args=[3]).start()
    threading.Thread(target=linhaDeProducao, args=[4]).start()
    threading.Thread(target=linhaDeProducao, args=[5]).start()
    threading.Thread(target=linhaDeProducao, args=[6]).start()
    threading.Thread(target=linhaDeProducao, args=[7]).start()
    threading.Thread(target=linhaDeProducao, args=[8]).start()

    def callback(ch, method, properties, body):
        global produtosAFazer

        produtosAFazer = json.loads(body)

        print(" [X] Começando dia na fabrica 2")

    channel.basic_consume(queue='pedido_fabrica2', on_message_callback=callback, auto_ack=True)
    print(" [X] Fabrica 2 aguardando")
    channel.start_consuming()

if __name__ == '__main__':
    try:
        threading.Thread(target=handleReceivingParts).start()
        main()
    except KeyboardInterrupt:
        print('Fabrica 2 interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)