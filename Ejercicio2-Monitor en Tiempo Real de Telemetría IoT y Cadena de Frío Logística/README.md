# Monitor en Tiempo Real de Telemetría IoT y Cadena de Frío Logística


Sistema de telemetría para camiones refrigerados. El cliente se suscribe a un camión y el servidor le envía, cada cierto número de segundos, la temperatura y la posición del vehículo. Las lecturas fuera del rango de 2 a 8 °C se marcan como alerta crítica y el cliente las resalta en rojo.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white)
![gRPC](https://img.shields.io/badge/gRPC-server%20streaming-244c5a?style=for-the-badge&logo=grpc&logoColor=white)
![Protobuf](https://img.shields.io/badge/Protocol%20Buffers-proto3-informational?style=for-the-badge)
![HTTP/2](https://img.shields.io/badge/transporte-HTTP%2F2-informational?style=for-the-badge)
![Hilos](https://img.shields.io/badge/servidor-ThreadPool%20(10%20hilos)-orange?style=for-the-badge)
![Arquitectura](https://img.shields.io/badge/arquitectura-cliente--servidor-green?style=for-the-badge)
![Dominio](https://img.shields.io/badge/dominio-telemetr%C3%ADa%20IoT-green?style=for-the-badge)
![Interfaz](https://img.shields.io/badge/interfaz-consola-lightgrey?style=for-the-badge)


## Tabla de contenido

- [Descripción general](#descripción-general)
- [Características](#características)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Cómo funciona](#cómo-funciona)
- [Contrato gRPC](#contrato-grpc)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Capturas de pantalla](#capturas-de-pantalla)


## Descripción general

Este proyecto es el ejercicio 2 (nivel intermedio) de una práctica de gRPC sobre el patrón de server streaming: el cliente envía una sola petición y el servidor responde con un flujo de mensajes que se mantiene abierto hasta que el cliente lo cierra.

El servidor define el servicio `MonitorCadenaFrio` con un único método, `TransmitirTelemetria`. Hay dos camiones registrados, `CAM-001` y `CAM-002`. Cuando un cliente se suscribe a uno de ellos, el servidor genera una lectura simulada cada `intervalo_segundos` con la temperatura, la posición, la hora y una marca de alerta. Los datos se inventan con números aleatorios, no vienen de sensores reales.

El cliente pide el identificador del camión y el intervalo, y muestra cada lectura en la terminal. Las lecturas normales llevan el prefijo `OK` y las que están fuera de rango se imprimen sobre fondo rojo con la etiqueta `ALERTA CRÍTICA`.

## Características

- Un método gRPC de server streaming que entrega lecturas hasta que el cliente cancela.
- Dos camiones registrados con su posición inicial: `CAM-001` (-0.1807, -78.4678) y `CAM-002` (-2.1709, -79.9224).
- Intervalo de envío elegido por el cliente, en segundos.
- Temperatura simulada entre 1.0 y 9.0 °C. La lectura es alerta crítica si es menor a 2.0 o mayor a 8.0, así que aproximadamente una de cada cuatro lecturas dispara la alerta.
- La posición cambia en cada lectura con un desplazamiento aleatorio de hasta 0.001 grados en latitud y longitud.
- Si el camión no existe, el servidor corta la llamada con el código `NOT_FOUND` y el cliente muestra el mensaje de error.
- El cliente hace un sondeo previo con intervalo 0 para validar el identificador antes de pedir el intervalo.
- El servidor detecta cuando el cliente se desconecta, deja de generar lecturas y lo avisa en su consola.
- El servidor atiende varias suscripciones a la vez con un pool de 10 hilos.
- El cliente cierra el canal siempre, también cuando hay un error o se cancela con Ctrl+C.

## Requisitos previos

- Python 3 [COMPLETAR: versión exacta usada]
- pip
- `grpcio` y `grpcio-tools`
- Una terminal que interprete códigos de color ANSI para ver el resaltado rojo (Linux, macOS, Windows Terminal). En la consola clásica de Windows pueden verse los códigos como texto.

## Instalación

Guarda `servidor.py`, `cliente.py` y `monitor.proto` en una misma carpeta y abre una terminal dentro de ella.

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
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. monitor.proto
```

Ese comando crea dos archivos en la carpeta: `monitor_pb2.py`, con las clases de los mensajes, y `monitor_pb2_grpc.py`, con la clase base del servicio y el stub del cliente. El servidor y el cliente los importan, así que hay que generarlos antes de ejecutar cualquiera de los dos. El archivo del contrato debe llamarse `monitor.proto` para que los módulos generados se llamen `monitor_pb2` y `monitor_pb2_grpc`, como los importa el código.

## Configuración

| Archivo | Valor en el código | Para qué sirve |
|---|---|---|
| `servidor.py` | `"[::]:50051"` | Dirección donde escucha el servidor. Acepta conexiones en todas las interfaces, puerto 50051 |
| `servidor.py` | `CAMIONES` | Diccionario con los camiones registrados y su posición inicial `(latitud, longitud)` |
| `servidor.py` | `TEMP_MIN = 2.0` y `TEMP_MAX = 8.0` | Límites del rango normal. Fuera de él, la lectura es alerta crítica |
| `servidor.py` | `max_workers=10` | Cantidad de hilos del servidor, y por tanto de suscripciones simultáneas |
| `cliente.py` | `"172.17.37.223:50051"` | IP y puerto del servidor. Cámbialo por la IP del equipo donde corre `servidor.py` |
| `cliente.py` | `ROJO` y `RESET` | Códigos ANSI que se usan para resaltar las alertas |

Si cliente y servidor corren en el mismo equipo, usa `"localhost:50051"` en el cliente. Si están en equipos distintos, el cortafuegos del servidor debe permitir el puerto 50051.

## Uso

Se necesitan dos terminales. El servidor debe estar corriendo antes de abrir el cliente.

### 1. Iniciar el servidor

```bash
python servidor.py
```

Salida esperada:

```text
Servidor escuchando en el puerto 50051
```

El servidor queda esperando suscripciones y no debes cerrar esta terminal.

### 2. Ejecutar el cliente

```bash
python cliente.py
```

Ejemplo de una sesión con el camión `CAM-001` y un intervalo de 2 segundos:

```text
ID del camión (CAM-001 / CAM-002): CAM-001
Intervalo en segundos: 2
OK  [2026-11-16T22:10:24] CAM-001 | 5.43 °C | (-0.18123, -78.46801)
OK  [2026-11-16T22:10:26] CAM-001 | 3.07 °C | (-0.18190, -78.46742)
 ALERTA CRÍTICA  [2026-11-16T22:10:28] CAM-001 | 8.76 °C | (-0.18144, -78.46688)
OK  [2026-11-16T22:10:30] CAM-001 | 6.12 °C | (-0.18201, -78.46731)
```

En la terminal real, la línea de alerta aparece con letras blancas sobre fondo rojo. Aquí se muestra sin color. El flujo sigue hasta que se cancela con Ctrl+C:

```text
^C
Suscripción cancelada por el usuario.
```

Lo que se ve al mismo tiempo en la terminal del servidor:

```text
Suscripción recibida: CAM-001, cada 2 s
Enviada a CAM-001: 5.43 °C 
Enviada a CAM-001: 3.07 °C 
Enviada a CAM-001: 8.76 °C (ALERTA)
Enviada a CAM-001: 6.12 °C 
El cliente cerró la suscripción de CAM-001
```

El aviso de cierre aparece unos segundos después de la cancelación, porque el servidor solo comprueba si el cliente sigue conectado al terminar cada espera.

### Ejemplo con un camión que no existe

```text
ID del camión (CAM-001 / CAM-002): CAM-009
Error: El camión CAM-009 no existe
```

En el servidor aparece `Suscripción rechazada: CAM-009 no existe`.

### Varios clientes a la vez

Abre más terminales y ejecuta `python cliente.py` en cada una. Pueden suscribirse a camiones distintos o al mismo. Cada suscripción tiene su propio flujo de lecturas, así que dos clientes del mismo camión ven valores diferentes.

### Errores comunes

| Mensaje | Causa probable | Solución |
|---|---|---|
| `Error gRPC: StatusCode.UNAVAILABLE - ...` | El servidor no está corriendo, o la IP del cliente no es la del servidor | Inicia `servidor.py` y revisa la IP en `cliente.py` |
| `ModuleNotFoundError: No module named 'monitor_pb2'` | No se generaron los archivos a partir del `.proto` | Ejecuta el comando `grpc_tools.protoc` de la sección Instalación |
| `ModuleNotFoundError: No module named 'grpc'` | `grpcio` no está instalado | Ejecuta `pip install grpcio grpcio-tools` |
| `ValueError: invalid literal for int()` | Se escribió texto en lugar de un número en el intervalo | Vuelve a ejecutar el cliente e ingresa un entero. Ver [Limitaciones conocidas](#limitaciones-conocidas) |
| Aparecen símbolos como `[1;37;41m` en las alertas | La terminal no interpreta códigos ANSI | Usa una terminal que los soporte, como Windows Terminal |

## Estructura del proyecto

```text
.
├── monitor.proto        # Contrato: servicio y mensajes
├── monitor_pb2.py       # Generado: clases de los mensajes
├── monitor_pb2_grpc.py  # Generado: servicer base y stub del cliente
├── servidor.py          # Servicio MonitorCadenaFrio y arranque del servidor
├── cliente.py           # Suscripción, sondeo previo y visualización de lecturas
└── README.md            # Este archivo
```

[COMPLETAR: agrega aquí otros archivos si la carpeta tiene más]

## Cómo funciona

gRPC es un marco de llamadas a procedimientos remotos que usa Protocol Buffers para describir los mensajes y HTTP/2 como transporte. El contrato se escribe una vez en un archivo `.proto` y de él se generan las clases de Python que usan ambos programas. En este proyecto hay tres piezas:

1. Contrato (`monitor.proto`). Declara el servicio `MonitorCadenaFrio` y los mensajes `SuscripcionCamion` y `LecturaSensor`. La palabra `stream` en el tipo de retorno de `TransmitirTelemetria` hace que el servidor pueda responder con muchos mensajes a una sola petición.
2. Servidor (`servidor.py`). La clase `MonitorCadenaFrio` hereda de `MonitorCadenaFrioServicer`, la clase base generada, y sobrescribe `TransmitirTelemetria`. Ese método es un generador: cada `yield` envía una lectura al cliente. Al final del archivo se crea el servidor con un `ThreadPoolExecutor` de 10 hilos, se registra el servicio, se abre el puerto 50051 sin cifrado y se queda esperando con `wait_for_termination()`.
3. Cliente (`cliente.py`). Abre un canal hacia el servidor, crea el stub `MonitorCadenaFrioStub` y llama a `TransmitirTelemetria`. Como el método devuelve un flujo, el resultado se recorre con un `for`, y cada iteración recibe una lectura nueva a medida que el servidor la envía.

Lógica de `TransmitirTelemetria` en el servidor:

1. Si el identificador no está en `CAMIONES`, imprime el rechazo y llama a `context.abort` con `NOT_FOUND`, que termina la llamada con error.
2. Si el intervalo es 0, termina sin enviar nada. El cliente usa este caso como sondeo.
3. Si el intervalo es negativo, usa 1 segundo.
4. Toma la posición inicial del camión y entra en un ciclo que dura mientras `context.is_active()` sea verdadero, es decir, mientras el cliente siga conectado.
5. En cada vuelta genera una temperatura aleatoria entre 1.0 y 9.0, mueve la posición un poco, calcula si hay alerta, envía la lectura con `yield`, la imprime en consola y espera `intervalo` segundos.

El sondeo previo del cliente existe por una razón práctica. Con server streaming, un error como `NOT_FOUND` solo llega al cliente cuando este empieza a recorrer el flujo. Por eso el cliente hace primero una llamada con intervalo 0 y la recorre con un `for` vacío. Si el camión no existe, el error salta ahí, antes de pedir el intervalo al usuario. Si existe, el servidor devuelve un flujo vacío y el cliente continúa.

Flujo de una sesión:

```text
cliente.py  ->  servidor.py: TransmitirTelemetria(CAM-001, intervalo 0)   (sondeo)
servidor.py ->  cliente.py:  flujo vacío, el camión existe
cliente.py  ->  servidor.py: TransmitirTelemetria(CAM-001, intervalo 2)
servidor.py ->  cliente.py:  LecturaSensor (5.43 °C)
servidor.py ->  cliente.py:  LecturaSensor (3.07 °C)
servidor.py ->  cliente.py:  LecturaSensor (8.76 °C, alerta_critica = true)
...
cliente.py:                  Ctrl+C, cierra el canal
servidor.py:                 context.is_active() pasa a False, termina el ciclo
```

## Contrato gRPC

Archivo `monitor.proto`:

```protobuf
syntax = "proto3";

service MonitorCadenaFrio {
  rpc TransmitirTelemetria (SuscripcionCamion) returns (stream LecturaSensor);
}

message SuscripcionCamion {
  string id_camion = 1;
  int32 intervalo_segundos = 2;
}

message LecturaSensor {
  string id_camion = 1;
  double temperatura_celsius = 2;
  double latitud = 3;
  double longitud = 4;
  string timestamp = 5;
  bool alerta_critica = 6;
}
```

Mensaje `SuscripcionCamion`, que envía el cliente:

| Campo | Tipo | Descripción |
|---|---|---|
| `id_camion` | `string` | Identificador del camión, por ejemplo `CAM-001` |
| `intervalo_segundos` | `int32` | Segundos entre lecturas. El valor 0 hace un sondeo sin lecturas |

Mensaje `LecturaSensor`, que envía el servidor:

| Campo | Tipo | Descripción |
|---|---|---|
| `id_camion` | `string` | Camión al que pertenece la lectura |
| `temperatura_celsius` | `double` | Temperatura en grados Celsius, con dos decimales |
| `latitud` | `double` | Latitud actual del camión |
| `longitud` | `double` | Longitud actual del camión |
| `timestamp` | `string` | Fecha y hora de la lectura en formato ISO 8601, sin fracciones de segundo |
| `alerta_critica` | `bool` | `true` si la temperatura es menor a 2.0 o mayor a 8.0 |

Códigos de estado que usa el servidor:

| Código | Cuándo ocurre |
|---|---|
| `NOT_FOUND` | El `id_camion` no está registrado en el servidor |


## Capturas de pantalla


Servidor recibiendo la suscripción y enviando lecturas:

<img width="763" height="311" alt="image" src="https://github.com/user-attachments/assets/4faebb96-a593-4f7b-89e7-ca417ac7ceb4" />


<img width="763" height="345" alt="image" src="https://github.com/user-attachments/assets/487344db-a7c8-4cd1-851f-52b75e0beae9" />

Cliente mostrando lecturas normales y una alerta crítica en rojo:

<img width="866" height="448" alt="image" src="https://github.com/user-attachments/assets/68030117-6bb8-482a-8d8c-bd37d67c6779" />


<img width="738" height="475" alt="image" src="https://github.com/user-attachments/assets/536b51b1-eae6-442b-951d-ae740df893b5" />


Error al pedir un camión que no existe:

<img width="763" height="70" alt="image" src="https://github.com/user-attachments/assets/54e98f9b-b4bd-41a8-abbd-e8f8395d4100" />


<img width="1554" height="113" alt="image" src="https://github.com/user-attachments/assets/8835642d-4c1d-446b-b40e-5d9d7d6e6979" />

