# TP0: Docker + Comunicaciones + Concurrencia

## Protocolo de Comunicación
### Modulos
El protocolo de comunicación está compuesto de 2 partes, un módulo de de/serialización de mensajes y
una capa de red construida sobre TCP que se encarga de la transmisión de estos mensajes abstrayendo al
usuario de las particularidades de las librerías del sistema operativo, como son el short-read y 
short-write.
El módulo de de/serialización no conoce a la capa de red, y la capa de red ignora los tipos de mensajes que
existen.

### Tipos de mensajes
En cuanto a los mensajes propios del protocolo, todos los mensajes enviados por la red son Batch, es decir,
una lista de payloads que puede tener largo 1. El caso más común para estos payloads sería el tipo
BetPayload enviado por el cliente para notificar al servidor de nuevas apuestas, al cual el servidor
respondería con otro mensaje Batch formado por un AckPayload para cada una de las apuestas. Los mensajes
Batch tienen la particularidad de que todos sus payloads son del mismo tipo, ya sean todos BetPayload,
AckPayload u otro.

### Serialización en la capa de red
La capa de red se abstrae de la estructura interna de los mensajes y delega al módulo de de/serialización el
convertir mensajes en arrays de bytes. Lo que sí hace la capa de red es anteponer 4 bytes (un UINT32) para 
indicar el tamaño del array de bytes siendo transferido. Cuando los bytes se leen del otro lado de la 
conexión, se convierten estos 4 bytes en un UINT32 y se lee la totalidad del mensaje entrante, aunque la 
operación sea bloqueante y el mensaje todavía no haya sido transmitido en su totalidad.

### Serialización de un mensaje
La clase Message hace casi lo mismo que la capa de red en lo que respecta a de/serialización, con el
detalle de que dedica solo 1 byte para indicar largo de cada payload individual. Esto restringe el largo 
máximo de un payload a 255 bytes.
Además, al principio del array de bytes resultado de concatenar todos los payloads se agrega un byte para 
indicar el _tipo_ de payloads que se serialiazó, si eran todos BetPayload, AckPayload u otro. Esto sirve
para a la hora de deserializar los bytes, saber a qué `class` delegarle la deserialización de los payloads.

### Serialización de un payload
Los payloads se serializan en formato csv, almacenando únicamente los valores de los campos. Para 
deserilizar se utiliza la posición de cada valor para saber a qué campo corresponde cada valor.
Este csv después se encodea con utf-8 antes de pasarse a la capa de red.
