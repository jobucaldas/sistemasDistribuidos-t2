package main

import (
	"fmt"
	"math"
	"os"
	"os/signal"
	"syscall"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

var (
	fornecedor    = "fornecedor/pedido"
	almoxarifado  = "almoxarifado/recebido"
	fabrica1      = "almoxarifado/pedido1"
	fabrica1envio = "fabrica/pedido1"

	partesBrutas []string

	capacidadeKanbam = 100000
	kanbamAmarelo    = roundFloat(float64(capacidadeKanbam)*0.6, 0)
	kanbamVermelho   = roundFloat(float64(capacidadeKanbam)*0.25, 0)
)

var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Connected")
}

var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Connect lost: %v", err)
}

func roundFloat(val float64, precision uint) float64 {
	ratio := math.Pow(10, float64(precision))
	return math.Round(val*ratio) / ratio
}

func main() {
	fmt.Println("Almoxarifado v1 started")
	var broker = "mqtt"
	var port = 1883
	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	opts.SetClientID("almoxarifado-v1")
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

	client.Unsubscribe(almoxarifado)
	client.Unsubscribe(fabrica1)
	client.Disconnect(250)
}

func almoxarifadoHandler(client mqtt.Client, msg mqtt.Message) {
	fmt.Println("Recebendo Peça do Fornecedor")
	if len(partesBrutas) <= int(kanbamAmarelo) {
		// Pedir mais peças ao fornecedor
		token := client.Publish(fornecedor, 0, false, "")
		token.Wait()

	}

	parte := string(msg.Payload())

	// time.Sleep(time.Second)
	partesBrutas = append(partesBrutas, parte)
}

func pedePartes(client mqtt.Client) {
	token := client.Publish(fornecedor, 0, false, "")
	token.Wait()
}

func pedidoFabrica1Handler(client mqtt.Client, msg mqtt.Message) {
	fmt.Println("Recebendo Pedido de Peça da Fábrica 1")

	if len(partesBrutas) <= int(kanbamVermelho) {
		fmt.Println("Pedindo mais peças ao fornecedor")

		// Pedir mais partes ao fornecedor
		for i := 0; i < int(kanbamAmarelo); i++ {
			go pedePartes(client)
		}
	}

	parte := partesBrutas[0]
	partesBrutas = partesBrutas[1:]

	fmt.Println("Enviando Peça para a Fábrica 1")
	token := client.Publish(fabrica1envio, 0, false, parte)
	token.Wait()

}

func sub(client mqtt.Client) {
	token := client.Subscribe(almoxarifado, 1, almoxarifadoHandler)
	token.Wait()
	fmt.Printf("Subscribed to topic: %s\n", almoxarifado)

	token = client.Subscribe(fabrica1, 1, pedidoFabrica1Handler)
	token.Wait()
	fmt.Printf("Subscribed to topic: %s\n", fabrica1)
}
