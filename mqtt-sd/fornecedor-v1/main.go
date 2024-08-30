package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/google/uuid"
)

var (
	fornecedor   = "fornecedor/pedido"
	almoxarifado = "almoxarifado/recebido"

	partesBuffer []string
)

var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Connected to MQTT Broker")
}

var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Connection lost: %v\n", err)
}

func main() {

	fmt.Println("Fornecedor v1 started")
	var broker = "mqtt"
	var port = 1883
	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	opts.SetClientID("fornecedor-v1")
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	sub(client)

	// Wait for a signal to exit the program gracefully
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	client.Unsubscribe(fornecedor)
	client.Disconnect(250)
}

func fornecedorHandler(client mqtt.Client, msg mqtt.Message) {
	fmt.Println("Recebendo Pedido de Peça do Almoxarifado")

	// Gerar e acumular peças do pacote
	for i := 0; i < 10; i++ {
		parte := fmt.Sprintf("Peça: %s", uuid.New().String())
		partesBuffer = append(partesBuffer, parte)
	}

	// Enviar todas as peças acumuladas de uma vez
	for _, parte := range partesBuffer {
		token := client.Publish(almoxarifado, 0, false, parte)
		token.Wait()
		// fmt.Printf("Enviando %s\n", parte)
		// time.Sleep(time.Second) // Simula o tempo de envio de cada produto
	}

	// Limpar o buffer após o envio
	partesBuffer = []string{}
}

func sub(client mqtt.Client) {
	fmt.Println("Subscribing to topic:", fornecedor)
	if token := client.Subscribe(fornecedor, 1, fornecedorHandler); token.Wait() && token.Error() != nil {
		panic(fmt.Sprintf("Error subscribing to topic: %s", token.Error()))
	}
}
