#!/usr/bin/env python
import pika
import threading
import time

def produce():
    def on_open(connection):
        connection.channel(on_open_callback=on_channel_open)

    def on_channel_open(channel):
        print(" [*] Waiting for messages. To exit press CTRL+C")
        def publish_message():
            message = "fabrica1"
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                ))
            print(f" [x] Sent {message}")
            connection.ioloop.call_later(5, publish_message)
        
        publish_message()

    parameters = pika.ConnectionParameters(host='rabbitmq')
    connection = pika.SelectConnection(parameters, on_open_callback=on_open)
    connection.ioloop.start()

def start_producer():
    threading.Thread(target=produce).start()

channel_consume = None

def consume():
    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")

    def on_open(connection):
        print("creating channel")
        connection.channel(on_open_callback=on_channel_open)

    def on_channel_open(channel):
        global channel_consume
        channel_consume = channel

        print("declaring queue")
        channel_consume.queue_declare(queue='task_queue', durable=True, callback=on_queue_declared)
    
    def on_queue_declared(frame):
        print("starting consuming")
        channel_consume.basic_consume(queue='task_queue', on_message_callback=callback, auto_ack=True)
        print(" [*] Waiting for messages. To exit press CTRL+C")

    def on_close(connection, exception):
        connection.ioloop.stop()

    print("starting connection")

    parameters = pika.ConnectionParameters(host='rabbitmq')
    connection = pika.SelectConnection(parameters, on_open_callback=on_open, on_close_callback=on_close)
    
    print(" [*] Waiting for messages. To exit press CTRL+C")

    try:
        connection.ioloop.start()
    except KeyboardInterrupt:
        connection.close()
        connection.ioloop.start()

def start_consumer():
    threading.Thread(target=consume).start()

# Start producer thread
# start_producer()

# Start consumer in the main thread
consume()