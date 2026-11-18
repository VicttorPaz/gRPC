
from concurrent import futures
import grpc
import pagos_pb2
import pagos_pb2_grpc

class ValidadorPagosServicer(pagos_pb2_grpc.ValidadorPagosServicer):

    # Método remoto (llamada unaria): recibe una SolicitudPago
    # y devuelve un ResultadoPago.
    # "context" sirve para devolver códigos de error al cliente.
    def VerificarTransaccion(self, request, context):
        # Se muestran en consola los datos que llegaron
        print(f"\n[Servidor] Procesando transacción ID: {request.id_transaccion}")
        print(f" -> Tarjeta: {request.numero_tarjeta} | Monto: {request.monto} {request.codigo_moneda} | País: {request.pais_origen}")

        # Regla 1: datos inválidos (monto <= 0 o tarjeta que no tiene 16 dígitos).
        # Se responde con el estado INVALID_ARGUMENT y se corta aquí.
        if request.monto <= 0 or len(request.numero_tarjeta) != 16:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Monto o número de tarjeta inválido")
            return pagos_pb2.ResultadoPago()

        # Regla 2: tarjetas que empiezan con "4000" se consideran bloqueadas
        # por fraude. Se responde con PERMISSION_DENIED.
        if request.numero_tarjeta.startswith("4000"):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Tarjeta bloquada por fraude")
            return pagos_pb2.ResultadoPago()

        # Regla 3: montos mayores a 10,000 solo se aceptan si el país
        # de origen es US o MX. Aquí no se usa un error gRPC: la llamada
        # funciona bien, pero el pago se rechaza por regla de negocio.
        if request.monto > 10000:
            if request.pais_origen not in ["US", "MX"]:
                return pagos_pb2.ResultadoPago(
                    aprobado=False,
                    codigo_autorizacion="",
                    motivo_rechazo="Rechazado por política de fraude: Montos mayores a $10,000 requieren origen US or MX"
                )

        # Si pasó todas las reglas, el pago se aprueba con un código fijo
        print("[Servidor] Transacción aprobada con éxito.")
        return pagos_pb2.ResultadoPago(
            aprobado=True,
            codigo_autorizacion="AUT-99887766",
            motivo_rechazo=""
        )

def serve():
    # Servidor con un pool de hasta 10 hilos para atender varias peticiones a la vez
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Se registra nuestra clase como la que atiende el servicio ValidadorPagos
    pagos_pb2_grpc.add_ValidadorPagosServicer_to_server(ValidadorPagosServicer(), server)
    puerto = "50051"
    # "[::]" escucha en todas las interfaces; el puerto es sin cifrado (insecure)
    server.add_insecure_port(f"[::]:{puerto}")
    server.start()
    print(f"Servidor gRPC de Pagos escuchando en el puerto {puerto}...")
    # Mantiene el programa vivo hasta que se detenga con Ctrl+C
    server.wait_for_termination()

serve()
