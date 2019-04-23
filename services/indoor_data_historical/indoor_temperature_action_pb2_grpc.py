# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import indoor_temperature_action_pb2 as indoor__temperature__action__pb2


class IndoorTemperatureActionStub(object):
  """The temperature service definition.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.GetRawTemperatures = channel.unary_unary(
        '/indoor_temperature_action.IndoorTemperatureAction/GetRawTemperatures',
        request_serializer=indoor__temperature__action__pb2.Request.SerializeToString,
        response_deserializer=indoor__temperature__action__pb2.RawTemperatureReply.FromString,
        )
    self.GetRawActions = channel.unary_unary(
        '/indoor_temperature_action.IndoorTemperatureAction/GetRawActions',
        request_serializer=indoor__temperature__action__pb2.Request.SerializeToString,
        response_deserializer=indoor__temperature__action__pb2.RawActionReply.FromString,
        )
    self.GetRawTemperatureBands = channel.unary_unary(
        '/indoor_temperature_action.IndoorTemperatureAction/GetRawTemperatureBands',
        request_serializer=indoor__temperature__action__pb2.Request.SerializeToString,
        response_deserializer=indoor__temperature__action__pb2.RawTemperatureBandsReply.FromString,
        )


class IndoorTemperatureActionServicer(object):
  """The temperature service definition.
  """

  def GetRawTemperatures(self, request, context):
    """A simple RPC.

    Sends the outside temperature for a given building, within a duration (start, end), and a requested window
    An error  is returned if there are no temperature for the given request
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetRawActions(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetRawTemperatureBands(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_IndoorTemperatureActionServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'GetRawTemperatures': grpc.unary_unary_rpc_method_handler(
          servicer.GetRawTemperatures,
          request_deserializer=indoor__temperature__action__pb2.Request.FromString,
          response_serializer=indoor__temperature__action__pb2.RawTemperatureReply.SerializeToString,
      ),
      'GetRawActions': grpc.unary_unary_rpc_method_handler(
          servicer.GetRawActions,
          request_deserializer=indoor__temperature__action__pb2.Request.FromString,
          response_serializer=indoor__temperature__action__pb2.RawActionReply.SerializeToString,
      ),
      'GetRawTemperatureBands': grpc.unary_unary_rpc_method_handler(
          servicer.GetRawTemperatureBands,
          request_deserializer=indoor__temperature__action__pb2.Request.FromString,
          response_serializer=indoor__temperature__action__pb2.RawTemperatureBandsReply.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'indoor_temperature_action.IndoorTemperatureAction', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
