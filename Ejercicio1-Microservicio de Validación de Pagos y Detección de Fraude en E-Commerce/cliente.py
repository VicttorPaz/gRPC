import grpc
import pagos_pb2
import pagos_pb2_grpc

# Función auxiliar: arma la solicitud, la envía al servidor
# e imprime el resultado. Así no se repite el código en cada caso de prueba.
def enviar_pago(stub, id_tx, tarjeta, monto, moneda, pais):
    print(f"\n----------------------------------------")
    print(f"Enviando solicitud: {id_tx}")

    # Se construye el mensaje SolicitudPago con los datos recibidos
    peticion = pagos_pb2.SolicitudPago(
        id_transaccion=id_tx,
        numero_tarjeta=tarjeta,
        monto=monto,
        codigo_moneda=moneda,
        pais_origen=pais
    )

    try:
        # Llamada remota: se usa como si fuera una función local
        respuesta = stub.VerificarTransaccion(peticion)

        # Si el servidor respondió normal, se revisa si el pago fue aprobado o no
        if respuesta.aprobado:
            print(f"[Cliente] ¡Resultado: APROBADO!")
            print(f"          Código de Autorización: {respuesta.codigo_autorizacion}")
        else:
            print(f"[Cliente] ¡Resultado: RECHAZADO por reglas de negocio!")
            print(f"          Motivo: {respuesta.motivo_rechazo}")

    except grpc.RpcError as e:
        # Aquí llegan los errores que el servidor marcó con set_code
        # (INVALID_ARGUMENT, PERMISSION_DENIED) y también fallos de red
        print(f"[Error gRPC Capturado]")
        print(f" -> Código  : {e.code()}")
        print(f" -> Detalle : {e.details()}")

def run():
    # Se abre el canal hacia el servidor; "with" lo cierra solo al terminar
    with grpc.insecure_channel("localhost:50051") as channel:
        # El stub es el objeto que permite llamar los métodos remotos
        stub = pagos_pb2_grpc.ValidadorPagosStub(channel)

        # Caso 1: pago correcto (16 dígitos, monto positivo). Debe aprobarse.
        enviar_pago(
            stub,
            id_tx="TX-SUCCESS-01",
            tarjeta="4532123456789012",
            monto=250.50,
            moneda="USD",
            pais="EC"
        )

        # Caso 2: tarjeta con menos de 16 dígitos. El servidor responde INVALID_ARGUMENT.
        enviar_pago(
            stub,
            id_tx="TX-INVALID-02",
            tarjeta="12345678",
            monto=100.00,
            moneda="USD",
            pais="US"
        )

        # Caso 3: tarjeta que empieza con "4000". El servidor responde PERMISSION_DENIED.
        enviar_pago(
            stub,
            id_tx="TX-DENIED-03",
            tarjeta="4000555566667777",
            monto=50.00,
            moneda="USD",
            pais="MX"
        )

run()
