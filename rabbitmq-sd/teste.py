import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='fornecedor_request')

message = "Pedido de partes"
channel.basic_publish(exchange='', routing_key='fornecedor_request', body=message)

print(" [x] Pedido de teste enviado para 'fornecedor_request'")
connection.close()
