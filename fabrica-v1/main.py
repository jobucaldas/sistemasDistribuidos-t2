
import random
import time

import paho.mqtt.client as mqtt


broker = '172.30.0.5'
port = 1883
topic = "pecasfabricadas"
# Generate a Client ID with the publish prefix.
client_id = f'publish-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, rpython/mqtteturn code %d\n", rc)

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    # mqttc.username_pw_set(username, password)
    mqttc.on_connect = on_connect
    mqttc.connect(broker, port)
    return mqttc


def publish(client):
    msg_count = 1
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1
        if msg_count > 5:
            break


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()


if __name__ == '__main__':
    run()