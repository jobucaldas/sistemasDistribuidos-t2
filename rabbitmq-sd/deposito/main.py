#!/usr/bin/env python
import json
from time import sleep
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

totalDia = 0

produtos = [Queue(), Queue(), Queue(), Queue(), Queue()]

def handleReceivingProducts():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='depositar')

    def callback(ch, method, properties, body):
        content = json.loads(body)

        print(f"Recebendo produto {content["tipo"]}")

        produtos[content["tipo"]-1].enqueue(content["produto"])

        # Testo se acabou a produção do dia
        producaoDia = 0
        for i in range(5):
            producaoDia += produtos[i].size()

        if producaoDia >= totalDia:
            sleep(2)
            startNewDay()

    channel.basic_consume(queue='depositar', on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

def startNewDay():
    # print(" [x] Recebendo parte do almoxarifado")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='new_day')

    for i in range(5):
        produtos[i] = Queue()

    produtos1 = randrange(5,35)
    produtos2 = randrange(5,35)
    produtos3 = randrange(5,35)
    produtos4 = randrange(5,35)
    produtos5 = randrange(5,35)

    totalDia = produtos1 + produtos2 + produtos3 + produtos4 + produtos5 + 48*5

    print(" [X] Starting New Day")
    channel.basic_publish(exchange='', routing_key='new_day', body=json.dumps([produtos1, produtos2, produtos3, produtos4, produtos5])) # Envio a quantidade extra que quero no dia para a fabrica2 saber o que produzir
    connection.close()

def main():
    print(" [x] Começando deposito")

    threading.Thread(target=handleReceivingProducts).start()
    startNewDay()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Deposito interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)