# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: indoor_temperature_action.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='indoor_temperature_action.proto',
  package='indoor_temperature_action',
  syntax='proto3',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x1findoor_temperature_action.proto\x12\x19indoor_temperature_action\"U\n\x07Request\x12\x10\n\x08\x62uilding\x18\x01 \x01(\t\x12\x0c\n\x04zone\x18\x02 \x01(\t\x12\r\n\x05start\x18\x03 \x01(\x03\x12\x0b\n\x03\x65nd\x18\x04 \x01(\x03\x12\x0e\n\x06window\x18\x05 \x01(\t\"Y\n\x08Setpoint\x12\x0c\n\x04time\x18\x01 \x01(\x03\x12\x17\n\x0ftemperature_low\x18\x02 \x01(\x01\x12\x18\n\x10temperature_high\x18\x03 \x01(\x01\x12\x0c\n\x04unit\x18\x04 \x01(\t\"C\n\x10TemperaturePoint\x12\x0c\n\x04time\x18\x01 \x01(\x03\x12\x13\n\x0btemperature\x18\x02 \x01(\x01\x12\x0c\n\x04unit\x18\x03 \x01(\t\"+\n\x0b\x41\x63tionPoint\x12\x0c\n\x04time\x18\x01 \x01(\x03\x12\x0e\n\x06\x61\x63tion\x18\x02 \x01(\x01\"X\n\x13RawTemperatureReply\x12\x41\n\x0ctemperatures\x18\x01 \x03(\x0b\x32+.indoor_temperature_action.TemperaturePoint\"I\n\x0eRawActionReply\x12\x37\n\x07\x61\x63tions\x18\x01 \x03(\x0b\x32&.indoor_temperature_action.ActionPoint\"R\n\x18RawTemperatureBandsReply\x12\x36\n\tsetpoints\x18\x01 \x03(\x0b\x32#.indoor_temperature_action.Setpoint2\xdc\x02\n\x17IndoorTemperatureAction\x12j\n\x12GetRawTemperatures\x12\".indoor_temperature_action.Request\x1a..indoor_temperature_action.RawTemperatureReply\"\x00\x12`\n\rGetRawActions\x12\".indoor_temperature_action.Request\x1a).indoor_temperature_action.RawActionReply\"\x00\x12s\n\x16GetRawTemperatureBands\x12\".indoor_temperature_action.Request\x1a\x33.indoor_temperature_action.RawTemperatureBandsReply\"\x00\x42\x02P\x01\x62\x06proto3')
)




_REQUEST = _descriptor.Descriptor(
  name='Request',
  full_name='indoor_temperature_action.Request',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='building', full_name='indoor_temperature_action.Request.building', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='zone', full_name='indoor_temperature_action.Request.zone', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='start', full_name='indoor_temperature_action.Request.start', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='end', full_name='indoor_temperature_action.Request.end', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='window', full_name='indoor_temperature_action.Request.window', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=62,
  serialized_end=147,
)


_SETPOINT = _descriptor.Descriptor(
  name='Setpoint',
  full_name='indoor_temperature_action.Setpoint',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='indoor_temperature_action.Setpoint.time', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='temperature_low', full_name='indoor_temperature_action.Setpoint.temperature_low', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='temperature_high', full_name='indoor_temperature_action.Setpoint.temperature_high', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='unit', full_name='indoor_temperature_action.Setpoint.unit', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=149,
  serialized_end=238,
)


_TEMPERATUREPOINT = _descriptor.Descriptor(
  name='TemperaturePoint',
  full_name='indoor_temperature_action.TemperaturePoint',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='indoor_temperature_action.TemperaturePoint.time', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='temperature', full_name='indoor_temperature_action.TemperaturePoint.temperature', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='unit', full_name='indoor_temperature_action.TemperaturePoint.unit', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=240,
  serialized_end=307,
)


_ACTIONPOINT = _descriptor.Descriptor(
  name='ActionPoint',
  full_name='indoor_temperature_action.ActionPoint',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time', full_name='indoor_temperature_action.ActionPoint.time', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='action', full_name='indoor_temperature_action.ActionPoint.action', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=309,
  serialized_end=352,
)


_RAWTEMPERATUREREPLY = _descriptor.Descriptor(
  name='RawTemperatureReply',
  full_name='indoor_temperature_action.RawTemperatureReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='temperatures', full_name='indoor_temperature_action.RawTemperatureReply.temperatures', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=354,
  serialized_end=442,
)


_RAWACTIONREPLY = _descriptor.Descriptor(
  name='RawActionReply',
  full_name='indoor_temperature_action.RawActionReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='actions', full_name='indoor_temperature_action.RawActionReply.actions', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=444,
  serialized_end=517,
)


_RAWTEMPERATUREBANDSREPLY = _descriptor.Descriptor(
  name='RawTemperatureBandsReply',
  full_name='indoor_temperature_action.RawTemperatureBandsReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='setpoints', full_name='indoor_temperature_action.RawTemperatureBandsReply.setpoints', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=519,
  serialized_end=601,
)

_RAWTEMPERATUREREPLY.fields_by_name['temperatures'].message_type = _TEMPERATUREPOINT
_RAWACTIONREPLY.fields_by_name['actions'].message_type = _ACTIONPOINT
_RAWTEMPERATUREBANDSREPLY.fields_by_name['setpoints'].message_type = _SETPOINT
DESCRIPTOR.message_types_by_name['Request'] = _REQUEST
DESCRIPTOR.message_types_by_name['Setpoint'] = _SETPOINT
DESCRIPTOR.message_types_by_name['TemperaturePoint'] = _TEMPERATUREPOINT
DESCRIPTOR.message_types_by_name['ActionPoint'] = _ACTIONPOINT
DESCRIPTOR.message_types_by_name['RawTemperatureReply'] = _RAWTEMPERATUREREPLY
DESCRIPTOR.message_types_by_name['RawActionReply'] = _RAWACTIONREPLY
DESCRIPTOR.message_types_by_name['RawTemperatureBandsReply'] = _RAWTEMPERATUREBANDSREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Request = _reflection.GeneratedProtocolMessageType('Request', (_message.Message,), dict(
  DESCRIPTOR = _REQUEST,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.Request)
  ))
_sym_db.RegisterMessage(Request)

Setpoint = _reflection.GeneratedProtocolMessageType('Setpoint', (_message.Message,), dict(
  DESCRIPTOR = _SETPOINT,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.Setpoint)
  ))
_sym_db.RegisterMessage(Setpoint)

TemperaturePoint = _reflection.GeneratedProtocolMessageType('TemperaturePoint', (_message.Message,), dict(
  DESCRIPTOR = _TEMPERATUREPOINT,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.TemperaturePoint)
  ))
_sym_db.RegisterMessage(TemperaturePoint)

ActionPoint = _reflection.GeneratedProtocolMessageType('ActionPoint', (_message.Message,), dict(
  DESCRIPTOR = _ACTIONPOINT,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.ActionPoint)
  ))
_sym_db.RegisterMessage(ActionPoint)

RawTemperatureReply = _reflection.GeneratedProtocolMessageType('RawTemperatureReply', (_message.Message,), dict(
  DESCRIPTOR = _RAWTEMPERATUREREPLY,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.RawTemperatureReply)
  ))
_sym_db.RegisterMessage(RawTemperatureReply)

RawActionReply = _reflection.GeneratedProtocolMessageType('RawActionReply', (_message.Message,), dict(
  DESCRIPTOR = _RAWACTIONREPLY,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.RawActionReply)
  ))
_sym_db.RegisterMessage(RawActionReply)

RawTemperatureBandsReply = _reflection.GeneratedProtocolMessageType('RawTemperatureBandsReply', (_message.Message,), dict(
  DESCRIPTOR = _RAWTEMPERATUREBANDSREPLY,
  __module__ = 'indoor_temperature_action_pb2'
  # @@protoc_insertion_point(class_scope:indoor_temperature_action.RawTemperatureBandsReply)
  ))
_sym_db.RegisterMessage(RawTemperatureBandsReply)


DESCRIPTOR._options = None

_INDOORTEMPERATUREACTION = _descriptor.ServiceDescriptor(
  name='IndoorTemperatureAction',
  full_name='indoor_temperature_action.IndoorTemperatureAction',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=604,
  serialized_end=952,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetRawTemperatures',
    full_name='indoor_temperature_action.IndoorTemperatureAction.GetRawTemperatures',
    index=0,
    containing_service=None,
    input_type=_REQUEST,
    output_type=_RAWTEMPERATUREREPLY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetRawActions',
    full_name='indoor_temperature_action.IndoorTemperatureAction.GetRawActions',
    index=1,
    containing_service=None,
    input_type=_REQUEST,
    output_type=_RAWACTIONREPLY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetRawTemperatureBands',
    full_name='indoor_temperature_action.IndoorTemperatureAction.GetRawTemperatureBands',
    index=2,
    containing_service=None,
    input_type=_REQUEST,
    output_type=_RAWTEMPERATUREBANDSREPLY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_INDOORTEMPERATUREACTION)

DESCRIPTOR.services_by_name['IndoorTemperatureAction'] = _INDOORTEMPERATUREACTION

# @@protoc_insertion_point(module_scope)
