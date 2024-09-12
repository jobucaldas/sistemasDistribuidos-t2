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
quantidadePartes = [43+20, 43+33, 43+31, 43+29, 43+24]

def handleReceivingParts():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='fabrica1_send')

    def callback(ch, method, properties, body):
        content = json.loads(body)
        # print(f" [x] Recebida parte {linhasQueue[content["linha"]-1].size()} da linha  {content["linha"]}")
        linhasQueue[content["linha"]-1].enqueue(content["parte"])

    channel.basic_consume(queue='fabrica1_send', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def handleNewDay():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='pedir_fabrica1')

    def callback(ch, method, properties, body):
        print(" [X] Começando dia na fabrica 1")
        # Reset all
        for i in range(5):
            itensProduzidos[i] = 0

    channel.basic_consume(queue='pedir_fabrica1', on_message_callback=callback, auto_ack=True)
    print(" [X] Fabrica 1 aguardando")
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
    pedido = False
    while True:
        if(itensProduzidos[linha-1] < tamanhoProducao):
            #print(f"{itensProduzidos[linha-1]} {linhasQueue[linha-1].size()<quantidadePartes} {quantidadePartes}")
            if not pedido:
                # Pedimos para o almoxarifado
                for i in range(quantidadePartes[linha-1]):
                    requestPart(1, linha)

            pedido = True

            # Espero ter peças
            if(linhasQueue[linha-1].size() >= quantidadePartes[linha-1]):
                pedido = False
                # Daí produzimos um produto unico
                for i in range(quantidadePartes[linha-1]):
                    linhasQueue[linha-1].dequeue()

                itensProduzidos[linha-1] += 1
                depositar(str(uuid.uuid4()), linha)
                #print(f" [X] Fabricado item {itensProduzidos}/{tamanhoProducao}")

            if(itensProduzidos[linha-1] >= tamanhoProducao):
                print(f" [x] Linha {linha} da fabrica 1 concluida!")

def main():
    print(" [x] Começando fabrica 1")

    threading.Thread(target=handleReceivingParts).start()
    threading.Thread(target=handleNewDay).start()

    threading.Thread(target=linhaDeProducao, args=[1]).start()
    threading.Thread(target=linhaDeProducao, args=[2]).start()
    threading.Thread(target=linhaDeProducao, args=[3]).start()
    threading.Thread(target=linhaDeProducao, args=[4]).start()
    threading.Thread(target=linhaDeProducao, args=[5]).start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Fabrica 1 interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)