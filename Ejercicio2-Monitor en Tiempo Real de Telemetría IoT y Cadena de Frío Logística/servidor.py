import random
import time
from concurrent import futures
from datetime import datetime

import grpc
import monitor_pb2        # mensajes generados a partir del .proto
import monitor_pb2_grpc   # clases del servicio generadas a partir del .proto

# Camiones que existen en el sistema, con su posición inicial (latitud, longitud)
CAMIONES = {
    "CAM-001": (-0.1807, -78.4678),
    "CAM-002": (-2.1709, -79.9224),
}

# Rango permitido para la cadena de frío
TEMP_MIN = 2.0
TEMP_MAX = 8.0


# Esta clase implementa el servicio que definimos en el .proto
class MonitorCadenaFrio(monitor_pb2_grpc.MonitorCadenaFrioServicer):

    # Método de server streaming: recibe una sola petición y va devolviendo lecturas con yield
    def TransmitirTelemetria(self, request, context):

        # Si el camión no existe, cortamos con el error NOT_FOUND
        if request.id_camion not in CAMIONES:
            print(f"Suscripción rechazada: {request.id_camion} no existe")
            context.abort(grpc.StatusCode.NOT_FOUND,
                          f"El camión {request.id_camion} no existe")

        # Intervalo 0 lo usa el cliente solo para comprobar que el camión existe
        # Aquí ya sabemos que existe, así que terminamos sin enviar lecturas
        if request.intervalo_segundos == 0:
            return

        # Si llega un intervalo negativo usamos 1 segundo por defecto
        intervalo = request.intervalo_segundos if request.intervalo_segundos > 0 else 1

        # Arrancamos desde la posición inicial del camión
        lat, lon = CAMIONES[request.id_camion]
        print(f"Suscripción recibida: {request.id_camion}, cada {intervalo} s")

        # Seguimos enviando mientras el cliente siga conectado
        while context.is_active():
            # Temperatura simulada entre 1 y 9 °C, así a veces se sale del rango
            temperatura = round(random.uniform(1.0, 9.0), 2)

            # Movemos un poco el camión para simular que avanza
            lat += random.uniform(-0.001, 0.001)
            lon += random.uniform(-0.001, 0.001)

            # Alerta crítica si la temperatura baja de 2 o pasa de 8
            alerta = temperatura < TEMP_MIN or temperatura > TEMP_MAX

            # yield envía la lectura al cliente y el método sigue desde aquí en la siguiente vuelta
            yield monitor_pb2.LecturaSensor(
                id_camion=request.id_camion,
                temperatura_celsius=temperatura,
                latitud=lat,
                longitud=lon,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                alerta_critica=alerta,
            )
            print(f"Enviada a {request.id_camion}: {temperatura} °C {'(ALERTA)' if alerta else ''}")

            # Esperamos el intervalo que pidió el cliente antes de la siguiente lectura
            time.sleep(intervalo)

        # Llegamos aquí cuando el cliente se desconecta (por ejemplo con Ctrl+C)
        print(f"El cliente cerró la suscripción de {request.id_camion}")


# Creamos el servidor con un grupo de hilos para atender varios clientes a la vez
servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# Registramos nuestra clase en el servidor
monitor_pb2_grpc.add_MonitorCadenaFrioServicer_to_server(MonitorCadenaFrio(), servidor)

# Escuchamos en el puerto 50051 por todas las interfaces, para aceptar conexiones de otras máquinas
servidor.add_insecure_port("[::]:50051")
servidor.start()
print("Servidor escuchando en el puerto 50051")

# Mantiene el servidor vivo hasta que lo detengamos
servidor.wait_for_termination()
