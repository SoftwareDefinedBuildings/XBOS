from concurrent import futures
import grpc
import discomfort_pb2
import discomfort_pb2_grpc
import time
import os

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
HOST_ADDRESS = os.environ["DISCOMFORT_HOST_ADDRESS"]


def get_linear_discomfort(request):
    """Returns linear discomfort (float) or None if Error encountered."""

    print("received request:", request.building, request.temperature, request.temperature_low, request.temperature_high, request.occupancy, request.unit)

    if request.unit != "F":
        return None, "not implemented, unit conversion is not implemented yet. Only Fahrenheit is supported."
    if not (0 <= request.occupancy <= 1):
        return None, "invalid input, occupancy is not between 0 and 1."
    if request.temperature_low > request.temperature_high:
        return None, "invalid input, temperature_high is smaller than temperature_low."

    discomfort = max(
        request.temperature_low - request.temperature,
        request.temperature - request.temperature_high,
        0
    )

    return discomfort_pb2.DiscomfortPoint(cost=request.occupancy * discomfort), None


class DiscomfortServicer(discomfort_pb2_grpc.DiscomfortServicer):
    def __init__(self):
        pass

    def GetLinearDiscomfort(self, request, context):
        """A simple RPC.

        Sends the discomfort.
        An error  is returned if discomfort could not be computed.
        """
        discomfort, error = get_linear_discomfort(request)
        if discomfort is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return discomfort_pb2.DiscomfortPoint()
        else:
            return discomfort


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    discomfort_pb2_grpc.add_DiscomfortServicer_to_server(DiscomfortServicer(), server)
    server.add_insecure_port(HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
