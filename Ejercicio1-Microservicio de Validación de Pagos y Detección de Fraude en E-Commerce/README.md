# Microservicio de Validación de Pagos y Detección de Fraude en E-Commerce


Servicio de validación de transacciones con tarjeta. El cliente envía una solicitud de pago y el servidor responde si la aprueba, la rechaza por una regla de negocio o la corta con un error gRPC.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)
![gRPC](https://img.shields.io/badge/gRPC-llamada%20unaria-244c5a?style=for-the-badge&logo=grpc&logoColor=white)
![Protobuf](https://img.shields.io/badge/Protocol%20Buffers-proto3-informational?style=for-the-badge)
![HTTP/2](https://img.shields.io/badge/transporte-HTTP%2F2-informational?style=for-the-badge)
![Hilos](https://img.shields.io/badge/servidor-ThreadPool%20(10%20hilos)-orange?style=for-the-badge)
![Arquitectura](https://img.shields.io/badge/arquitectura-cliente--servidor-green?style=for-the-badge)
![Dominio](https://img.shields.io/badge/dominio-validaci%C3%B3n%20de%20pagos-green?style=for-the-badge)
![Interfaz](https://img.shields.io/badge/interfaz-consola-lightgrey?style=for-the-badge)

## Tabla de contenido

- [Descripción general](#descripción-general)
- [Características](#características)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Cómo funciona](#cómo-funciona)
- [Contrato gRPC](#contrato-grpc)
- [Referencia de clases y funciones](#referencia-de-clases-y-funciones)
- [Capturas de pantalla](#capturas-de-pantalla)

## Descripción general

Este proyecto es una práctica de gRPC con el patrón de llamada unaria: el cliente envía una sola solicitud y el servidor devuelve una sola respuesta. Sirve para ver cómo un servicio puede comunicar un resultado de dos maneras distintas, con una respuesta normal que lleva el veredicto y con un código de estado de error.

El servidor define el servicio `ValidadorPagos` con un único método, `VerificarTransaccion`. Recibe el identificador de la transacción, el número de tarjeta, el monto, la moneda y el país de origen, y aplica tres reglas en orden. Si la solicitud pasa todas, responde con un código de autorización.

El cliente envía tres transacciones de prueba fijas, una por cada resultado posible, y muestra en la terminal lo que contesta el servidor. Los datos son de ejemplo y no se conecta con ningún procesador de pagos real.

## Características

- Un método gRPC unario que recibe una solicitud de pago y devuelve un resultado.
- Tres reglas de validación que se evalúan en este orden: argumentos inválidos, tarjeta bloqueada y límite de monto por país.
- Los errores de formato y las tarjetas bloqueadas se devuelven como errores gRPC, con los códigos `INVALID_ARGUMENT` y `PERMISSION_DENIED`.
- El rechazo por monto alto no es un error gRPC. Es una respuesta normal con `aprobado` en falso y el motivo escrito.
- El cliente distingue los dos tipos de respuesta: muestra el resultado cuando la llamada termina bien y captura la excepción `grpc.RpcError` cuando el servidor devuelve un error.
- El servidor atiende varias solicitudes a la vez con un pool de 10 hilos.
- El cliente usa un canal con `with`, así que lo cierra solo al terminar.

## Requisitos previos

- Python 3 [COMPLETAR: versión exacta usada]
- pip
- `grpcio` y `grpcio-tools`

## Instalación

Guarda `servidor.py`, `cliente.py` y `pagos.proto` en una misma carpeta y abre una terminal dentro de ella.

Instala las dependencias:

```bash
pip install grpcio grpcio-tools
```

Si prefieres aislarlas en un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install grpcio grpcio-tools
```

Genera el código de Python a partir del contrato:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. pagos.proto
```

Ese comando crea dos archivos en la carpeta: `pagos_pb2.py`, con las clases de los mensajes, y `pagos_pb2_grpc.py`, con la clase base del servicio y el stub del cliente. El servidor y el cliente los importan, así que hay que generarlos antes de ejecutar cualquiera de los dos. El contrato debe llamarse `pagos.proto` para que los módulos generados se llamen `pagos_pb2` y `pagos_pb2_grpc`, como los importa el código.

## Configuración

| Archivo | Valor en el código | Para qué sirve |
|---|---|---|
| `servidor.py` | `puerto = "50051"` | Puerto donde escucha el servidor. Acepta conexiones en todas las interfaces con la dirección `[::]` |
| `servidor.py` | `max_workers=10` | Cantidad de hilos del servidor, y por tanto de solicitudes que se atienden a la vez |
| `servidor.py` | `len(request.numero_tarjeta) != 16` | Longitud exigida al número de tarjeta |
| `servidor.py` | `startswith("4000")` | Prefijo de las tarjetas que se consideran bloqueadas por fraude |
| `servidor.py` | `request.monto > 10000` | Monto a partir del cual se exige un país de origen permitido |
| `servidor.py` | `["US", "MX"]` | Países de origen permitidos para montos mayores al límite |
| `servidor.py` | `"AUT-99887766"` | Código de autorización que devuelve toda transacción aprobada |
| `cliente.py` | `"localhost:50051"` | Dirección del servidor. Cámbiala por su IP si corre en otro equipo |
| `cliente.py` | Tres llamadas dentro de `run()` | Las transacciones de prueba que se envían |

Si el servidor corre en otro equipo, el cortafuegos debe permitir el puerto 50051.

## Uso

Se necesitan dos terminales. El servidor debe estar corriendo antes de ejecutar el cliente.

### 1. Iniciar el servidor

```bash
python servidor.py
```

Salida esperada:

```text
Servidor gRPC de Pagos escuchando en el puerto 50051...
```

El servidor queda esperando solicitudes y no debes cerrar esta terminal.

### 2. Ejecutar el cliente

```bash
python cliente.py
```

El cliente envía las tres transacciones de prueba una detrás de otra y termina. Salida esperada:

```text
----------------------------------------
Enviando solicitud: TX-SUCCESS-01
[Cliente] ¡Resultado: APROBADO!
          Código de Autorización: AUT-99887766

----------------------------------------
Enviando solicitud: TX-INVALID-02
[Error gRPC Capturado]
 -> Código  : StatusCode.INVALID_ARGUMENT
 -> Detalle : Monto o número de tarjeta inválido

----------------------------------------
Enviando solicitud: TX-DENIED-03
[Error gRPC Capturado]
 -> Código  : StatusCode.PERMISSION_DENIED
 -> Detalle : Tarjeta bloquada por fraude
```

Lo que se ve al mismo tiempo en la terminal del servidor:

```text
[Servidor] Procesando transacción ID: TX-SUCCESS-01
 -> Tarjeta: 4532123456789012 | Monto: 250.5 USD | País: EC
[Servidor] Transacción aprobada con éxito.

[Servidor] Procesando transacción ID: TX-INVALID-02
 -> Tarjeta: 12345678 | Monto: 100.0 USD | País: US

[Servidor] Procesando transacción ID: TX-DENIED-03
 -> Tarjeta: 4000555566667777 | Monto: 50.0 USD | País: MX
```

### Casos de prueba incluidos

| Transacción | Tarjeta | Monto | País | Qué ocurre |
|---|---|---|---|---|
| `TX-SUCCESS-01` | `4532123456789012` | 250.50 USD | EC | Se aprueba con un código de autorización |
| `TX-INVALID-02` | `12345678` | 100.00 USD | US | Error `INVALID_ARGUMENT`, porque la tarjeta no tiene 16 dígitos |
| `TX-DENIED-03` | `4000555566667777` | 50.00 USD | MX | Error `PERMISSION_DENIED`, porque la tarjeta empieza con `4000` |

### Probar el rechazo por monto alto

El cliente no incluye ningún caso para la tercera regla. Para verlo, agrega esta llamada dentro de `run()`, junto a las demás:

```python
enviar_pago(stub, id_tx="TX-LIMIT-04", tarjeta="4532123456789012",
            monto=15000.00, moneda="USD", pais="EC")
```

Como el monto supera 10,000 y el país no es `US` ni `MX`, el cliente muestra un rechazo de negocio y no un error gRPC:

```text
----------------------------------------
Enviando solicitud: TX-LIMIT-04
[Cliente] ¡Resultado: RECHAZADO por reglas de negocio!
          Motivo: Rechazado por política de fraude: Montos mayores a $10,000 requieren origen US or MX
```

Con `pais="US"` o `pais="MX"` la misma transacción se aprueba.

### Errores comunes

| Mensaje | Causa probable | Solución |
|---|---|---|
| `StatusCode.UNAVAILABLE` en el bloque `[Error gRPC Capturado]` | El servidor no está corriendo, o la dirección del cliente no es la del servidor | Inicia `servidor.py` y revisa la dirección en `cliente.py` |
| `ModuleNotFoundError: No module named 'pagos_pb2'` | No se generaron los archivos a partir del `.proto` | Ejecuta el comando `grpc_tools.protoc` de la sección Instalación |
| `ModuleNotFoundError: No module named 'grpc'` | `grpcio` no está instalado | Ejecuta `pip install grpcio grpcio-tools` |
| `Failed to bind to address [::]:50051` al iniciar el servidor | El puerto ya está ocupado, por ejemplo por otra copia del servidor | Cierra el otro proceso o cambia `puerto` en `servidor.py` y la dirección del cliente |


## Cómo funciona

gRPC es un marco de llamadas a procedimientos remotos que usa Protocol Buffers para describir los mensajes y HTTP/2 como transporte. El contrato se escribe una vez en un archivo `.proto` y de él se generan las clases de Python que usan ambos programas. Hay tres piezas:

1. Contrato (`pagos.proto`). Declara el servicio `ValidadorPagos` y los mensajes `SolicitudPago` y `ResultadoPago`. El método `VerificarTransaccion` no usa la palabra `stream`, así que es una llamada unaria: una solicitud y una respuesta.
2. Servidor (`servidor.py`). La clase `ValidadorPagosServicer` hereda de la clase base generada y sobrescribe `VerificarTransaccion`. La función `serve()` crea el servidor con un pool de 10 hilos, registra el servicio, abre el puerto 50051 sin cifrado y se queda esperando con `wait_for_termination()`.
3. Cliente (`cliente.py`). La función `run()` abre un canal hacia el servidor, crea el stub `ValidadorPagosStub` y llama tres veces a `enviar_pago`. Esta función arma la `SolicitudPago`, llama a `stub.VerificarTransaccion` y muestra el resultado.

Reglas que aplica `VerificarTransaccion`, en este orden:

| Orden | Condición | Resultado |
|---|---|---|
| 1 | El monto es menor o igual a 0, o el número de tarjeta no tiene 16 caracteres | Error gRPC `INVALID_ARGUMENT` con el detalle `Monto o número de tarjeta inválido` |
| 2 | El número de tarjeta empieza con `4000` | Error gRPC `PERMISSION_DENIED` con el detalle `Tarjeta bloquada por fraude` |
| 3 | El monto es mayor a 10,000 y el país de origen no es `US` ni `MX` | Respuesta con `aprobado = false` y el motivo del rechazo |
| 4 | Ninguna de las anteriores | Respuesta con `aprobado = true` y el código `AUT-99887766` |

Hay dos formas de decir que no, y el proyecto usa las dos a propósito. Las reglas 1 y 2 son errores de la llamada: el servidor fija el código con `context.set_code` y el texto con `context.set_details`, y el cliente los recibe como una excepción `grpc.RpcError`. La regla 3 es un resultado válido del negocio: la llamada termina bien y el rechazo viaja dentro del mensaje `ResultadoPago`, en los campos `aprobado` y `motivo_rechazo`.

Cuando el servidor fija un código distinto de OK, devuelve igualmente un `ResultadoPago` vacío. gRPC ignora ese mensaje y entrega solo el error al cliente.

Flujo de una transacción aprobada:

```text
cliente.py  ->  servidor.py: VerificarTransaccion(TX-SUCCESS-01, 4532123456789012, 250.5, USD, EC)
servidor.py:                 aplica las reglas 1, 2 y 3, y ninguna se cumple
servidor.py ->  cliente.py:  ResultadoPago(aprobado = true, codigo_autorizacion = "AUT-99887766")
cliente.py:                  imprime "APROBADO" y el código de autorización
```

Flujo de una tarjeta bloqueada:

```text
cliente.py  ->  servidor.py: VerificarTransaccion(TX-DENIED-03, 4000555566667777, 50.0, USD, MX)
servidor.py:                 la regla 2 se cumple y fija PERMISSION_DENIED
servidor.py ->  cliente.py:  error gRPC, sin mensaje de respuesta
cliente.py:                  captura grpc.RpcError e imprime el código y el detalle
```

## Contrato gRPC

Archivo `pagos.proto`:

```protobuf
syntax = "proto3";

package pagos;

service ValidadorPagos {
  rpc VerificarTransaccion (SolicitudPago) returns (ResultadoPago);
}

message SolicitudPago {
  string id_transaccion = 1;
  string numero_tarjeta = 2;
  double monto = 3;
  string codigo_moneda = 4;
  string pais_origen = 5;
}

message ResultadoPago {
  bool aprobado = 1;
  string codigo_autorizacion = 2;
  string motivo_rechazo = 3;
}
```

Mensaje `SolicitudPago`, que envía el cliente:

| Campo | Tipo | Descripción |
|---|---|---|
| `id_transaccion` | `string` | Identificador de la transacción, por ejemplo `TX-SUCCESS-01` |
| `numero_tarjeta` | `string` | Número de tarjeta, que debe tener 16 caracteres |
| `monto` | `double` | Monto de la compra, que debe ser mayor a 0 |
| `codigo_moneda` | `string` | Código de la moneda, por ejemplo `USD`. El servidor lo imprime pero no lo usa en las reglas |
| `pais_origen` | `string` | Código del país de origen, por ejemplo `EC`, `US` o `MX` |

Mensaje `ResultadoPago`, que envía el servidor:

| Campo | Tipo | Descripción |
|---|---|---|
| `aprobado` | `bool` | `true` si la transacción se aprobó |
| `codigo_autorizacion` | `string` | Código de autorización cuando se aprueba, vacío en caso contrario |
| `motivo_rechazo` | `string` | Texto con la razón cuando la regla de monto rechaza la transacción, vacío en caso contrario |

Códigos de estado que usa el servidor:

| Código | Cuándo ocurre |
|---|---|
| `INVALID_ARGUMENT` | El monto no es positivo o el número de tarjeta no tiene 16 caracteres |
| `PERMISSION_DENIED` | La tarjeta empieza con `4000` |

El cliente puede recibir además `UNAVAILABLE` si no logra conectarse con el servidor. Ese código lo genera gRPC y no el servicio.

## Referencia de clases y funciones

### Servidor: clase `ValidadorPagosServicer`

Es la única clase del proyecto. Hereda de `pagos_pb2_grpc.ValidadorPagosServicer`, generada a partir del contrato.

| Método | Qué hace | Devuelve | Errores |
|---|---|---|---|
| `VerificarTransaccion(request, context)` | Imprime la transacción recibida y aplica las tres reglas en orden. Si ninguna rechaza, imprime la aprobación y arma la respuesta | `ResultadoPago`: aprobado con código de autorización, o rechazado con motivo. En los errores devuelve un `ResultadoPago` vacío | `INVALID_ARGUMENT` y `PERMISSION_DENIED`, fijados con `context.set_code` |

### Servidor: función `serve()`

Crea el servidor gRPC con un `ThreadPoolExecutor` de 10 hilos, registra `ValidadorPagosServicer` con `add_ValidadorPagosServicer_to_server`, abre el puerto 50051 con `add_insecure_port`, imprime el aviso de inicio y espera con `wait_for_termination()` hasta que se detenga el proceso.

### Cliente: funciones

| Función | Qué hace | Devuelve |
|---|---|---|
| `enviar_pago(stub, id_tx, tarjeta, monto, moneda, pais)` | Arma la `SolicitudPago`, llama a `VerificarTransaccion` y muestra el resultado. Si la respuesta viene aprobada, imprime el código de autorización. Si viene rechazada, imprime el motivo. Si la llamada falla, captura `grpc.RpcError` e imprime el código y el detalle | Nada |
| `run()` | Abre el canal hacia `localhost:50051` con `with`, crea el stub y llama a `enviar_pago` con las tres transacciones de prueba | Nada |


## Capturas de pantalla


Servidor procesando las tres transacciones:

<img width="763" height="315" alt="image" src="https://github.com/user-attachments/assets/2742e2ec-6f49-4249-a488-43eda50bdfe6" />

Cliente con el pago aprobado y los dos errores:

<img width="873" height="407" alt="image" src="https://github.com/user-attachments/assets/6d4a2d70-d06a-4b8d-9347-878c87258097" />

