import grpc
import monitor_pb2        # mensajes generados a partir del .proto
import monitor_pb2_grpc   # stub generado a partir del .proto

# Códigos de color para resaltar las alertas en la consola (fondo rojo, texto blanco)
ROJO = "\033[1;37;41m"
RESET = "\033[0m"

id_camion = input("ID del camión (CAM-001 / CAM-002): ").strip()

# Abrimos el canal hacia el servidor (IP y puerto de la máquina donde corre servidor.py)
canal = grpc.insecure_channel("172.17.37.223:50051")

# El stub es el objeto que usamos para llamar a los métodos del servidor
stub = monitor_pb2_grpc.MonitorCadenaFrioStub(canal)

try:
    # Primero un sondeo con intervalo 0: el servidor solo comprueba que el camión exista
    # Si no existe, aquí salta el error NOT_FOUND antes de pedir el intervalo
    for _ in stub.TransmitirTelemetria(
            monitor_pb2.SuscripcionCamion(id_camion=id_camion, intervalo_segundos=0)):
        pass

    # Pedimos el intervalo y repetimos hasta que sea 1 o más
    intervalo = 0
    while intervalo < 1:
        intervalo = int(input("Intervalo en segundos: "))

    # Esta es la única petición de suscripción que manda el cliente
    peticion = monitor_pb2.SuscripcionCamion(id_camion=id_camion, intervalo_segundos=intervalo)

    # El for recibe cada lectura según va llegando del servidor
    for respuesta in stub.TransmitirTelemetria(peticion):
        linea = (f"[{respuesta.timestamp}] {respuesta.id_camion} | "
                 f"{respuesta.temperatura_celsius:.2f} °C | "
                 f"({respuesta.latitud:.5f}, {respuesta.longitud:.5f})")

        # Si la lectura trae alerta crítica la resaltamos en rojo
        if respuesta.alerta_critica:
            print(f"{ROJO} ALERTA CRÍTICA {RESET} {ROJO}{linea}{RESET}")
        else:
            print(f"OK  {linea}")

# Errores que vienen del servidor
except grpc.RpcError as error:
    if error.code() == grpc.StatusCode.NOT_FOUND:
        # El camión no existe
        print(f"Error: {error.details()}")
    else:
        # Cualquier otro fallo, por ejemplo UNAVAILABLE si el servidor está apagado
        print(f"Error gRPC: {error.code()} - {error.details()}")

# Ctrl+C para dejar de recibir lecturas
except KeyboardInterrupt:
    print("\nSuscripción cancelada por el usuario.")

# Cerramos el canal pase lo que pase
finally:
    canal.close()
