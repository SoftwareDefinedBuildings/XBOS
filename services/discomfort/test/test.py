
from __future__ import print_function

import grpc

import sys
sys.path.append("../")
import discomfort_pb2
import discomfort_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    with grpc.insecure_channel('localhost:50060') as channel:
        stub = discomfort_pb2_grpc.DiscomfortStub(channel)
        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(building="ciee", temperature=66,
                                                                                    temperature_low=65,
                                                                                    temperature_high=69,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=1234,
                                                                                    temperature_low=12,
                                                                                    temperature_high=234,
                                                                                    unit="F",
                                                                                    occupancy=0.2))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=68,
                                                                                    temperature_low=70,
                                                                                    temperature_high=69,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=70,
                                                                                    temperature_low=68,
                                                                                    temperature_high=69,
                                                                                    unit="C",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=70,
                                                                                    temperature_low=68,
                                                                                    temperature_high=68,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=70,
                                                                                    temperature_low=68,
                                                                                    temperature_high=69,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=68,
                                                                                    temperature_low=68,
                                                                                    temperature_high=68,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=-12,
                                                                                    temperature_low=-200,
                                                                                    temperature_high=-1,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)

        try:
            discomfort_response = stub.GetLinearDiscomfort(discomfort_pb2.Request(temperature=-210,
                                                                                    temperature_low=-200,
                                                                                    temperature_high=-1,
                                                                                    unit="F",
                                                                                    occupancy=1))
            print("Cost: %f" % discomfort_response.cost)
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
