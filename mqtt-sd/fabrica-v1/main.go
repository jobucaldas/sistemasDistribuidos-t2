package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

var (
	almoxarifadoPedido = "almoxarifado/pedido1"
	fabricaRecebido    = "fabrica/pedido1"
)

var (
	partesNecessarias   = 53
	produtosNecessarios = 48
	produtosProduzidos  = 0

	partes []string

	kanbamVerde    = 1000 // Vulgo capacidade
	kanbamAmarelo  = 600
	kanbamVermelho = 265
)

var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Connected to MQTT Broker")
}

var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Connection lost: %v\n", err)
}

func main() {
	fmt.Println("Fábrica v1 started")
	var broker = "mqtt"
	var port = 1883
	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	opts.SetClientID("fabrica-v1")
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	sub(client)

	// Inicia primeira linha de produção
	fabricaProduto(client, partesNecessarias)

	// Aguardar sinal para encerrar o programa
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	client.Unsubscribe(fabricaRecebido)
	client.Disconnect(250)
}

func fazerPedido(client mqtt.Client) {
	fmt.Printf("Fazendo pedido ao Almoxarifado (%d de %d)\n", len(partes), kanbamVerde)
	token := client.Publish(almoxarifadoPedido, 0, false, "Fazendo Pedido")
	token.Wait()

	time.Sleep(2 * time.Second)

	if token.Error() != nil {
		fmt.Printf("Erro ao fazer pedido: Tentando novamente...\n")
		time.Sleep(2 * time.Second)
		fazerPedido(client)
	} else {
		fmt.Println("Pedido feito com sucesso!")
	}
}

func fabricaProduto(client mqtt.Client, partesNecessarias int) {
	if len(partes) <= kanbamVermelho {
		for len(partes) < kanbamAmarelo {
			fazerPedido(client)
		}

		// Aguarda chegar
		time.Sleep(4 * time.Second)
	}

	// Fabricar o produto
	fmt.Println("Fabricando o produto...")
	partes = partes[partesNecessarias:]
	time.Sleep(2 * time.Second) // Simulação de processamento
	fmt.Println("Produto fabricado com sucesso!")

	// Incrementar contador de produtos fabricados
	produtosProduzidos++

	// Verificar se precisamos de mais produtos
	if produtosProduzidos < produtosNecessarios {
		fabricaProduto(client, partesNecessarias)
	} else {
		fmt.Println("Todos os produtos foram fabricados!")
	}
}

func parteHandler(client mqtt.Client, msg mqtt.Message) {
	parte := string(msg.Payload())
	fmt.Printf("Recebido parte do almoxarifado: %s\n", parte)

	// Adiciona parte ao estoque
	partes = append(partes, parte)
}

func sub(client mqtt.Client) {
	token := client.Subscribe(fabricaRecebido, 1, parteHandler)
	token.Wait()
	fmt.Printf("Subscribed to topic: %s\n", fabricaRecebido)
}
