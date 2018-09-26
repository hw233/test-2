# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: appoint.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import conscript_pb2
import battle_pb2
import item_pb2
import resource_pb2
import node_pb2
import mail_pb2
import hero_pb2
import monarch_pb2
import energy_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='appoint.proto',
  package='SanProto',
  serialized_pb=_b('\n\rappoint.proto\x12\x08SanProto\x1a\x0f\x63onscript.proto\x1a\x0c\x62\x61ttle.proto\x1a\nitem.proto\x1a\x0eresource.proto\x1a\nnode.proto\x1a\nmail.proto\x1a\nhero.proto\x1a\rmonarch.proto\x1a\x0c\x65nergy.proto\"F\n\x11GetAppointItemReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\x12 \n\x04item\x18\x02 \x02(\x0b\x32\x12.SanProto.ItemInfo\"M\n\x11GetAppointItemRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12(\n\x08resource\x18\x02 \x01(\x0b\x32\x16.SanProto.ResourceInfo\"\x91\x01\n\x0fStartAppointReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\x12)\n\x06\x62\x61ttle\x18\x02 \x02(\x0b\x32\x19.SanProto.BattleInputInfo\x12 \n\x04node\x18\x03 \x01(\x0b\x32\x12.SanProto.NodeInfo\x12 \n\x04item\x18\x04 \x01(\x0b\x32\x12.SanProto.ItemInfo\"x\n\x0fStartAppointRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12(\n\x08resource\x18\x02 \x01(\x0b\x32\x16.SanProto.ResourceInfo\x12+\n\nconscripts\x18\x03 \x03(\x0b\x32\x17.SanProto.ConscriptInfo\"E\n\x10\x46inishAppointReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\x12 \n\x04node\x18\x02 \x01(\x0b\x32\x12.SanProto.NodeInfo\"\xe7\x03\n\x10\x46inishAppointRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12&\n\x06reward\x18\x02 \x01(\x0b\x32\x16.SanProto.BattleReward\x12(\n\x08resource\x18\x03 \x01(\x0b\x32\x16.SanProto.ResourceInfo\x12&\n\x07monarch\x18\x04 \x01(\x0b\x32\x15.SanProto.MonarchInfo\x12+\n\nconscripts\x18\x05 \x03(\x0b\x32\x17.SanProto.ConscriptInfo\x12!\n\x05nodes\x18\x06 \x03(\x0b\x32\x12.SanProto.NodeInfo\x12!\n\x05items\x18\x07 \x03(\x0b\x32\x12.SanProto.ItemInfo\x12!\n\x05heros\x18\x08 \x03(\x0b\x32\x12.SanProto.HeroInfo\x12!\n\x05mails\x18\t \x03(\x0b\x32\x12.SanProto.MailInfo\x12+\n\x03ret\x18\n \x01(\x0e\x32\x1e.SanProto.FinishAppointRes.RET\x12 \n\x04node\x18\x0b \x01(\x0b\x32\x12.SanProto.NodeInfo\x12$\n\x06\x65nergy\x18\x0c \x01(\x0b\x32\x14.SanProto.EnergyInfo\"\x1b\n\x03RET\x12\x06\n\x02OK\x10\x00\x12\x0c\n\x08\x46INISHED\x10\x01')
  ,
  dependencies=[conscript_pb2.DESCRIPTOR,battle_pb2.DESCRIPTOR,item_pb2.DESCRIPTOR,resource_pb2.DESCRIPTOR,node_pb2.DESCRIPTOR,mail_pb2.DESCRIPTOR,hero_pb2.DESCRIPTOR,monarch_pb2.DESCRIPTOR,energy_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_FINISHAPPOINTRES_RET = _descriptor.EnumDescriptor(
  name='RET',
  full_name='SanProto.FinishAppointRes.RET',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OK', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='FINISHED', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=1104,
  serialized_end=1131,
)
_sym_db.RegisterEnumDescriptor(_FINISHAPPOINTRES_RET)


_GETAPPOINTITEMREQ = _descriptor.Descriptor(
  name='GetAppointItemReq',
  full_name='SanProto.GetAppointItemReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.GetAppointItemReq.user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='item', full_name='SanProto.GetAppointItemReq.item', index=1,
      number=2, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=151,
  serialized_end=221,
)


_GETAPPOINTITEMRES = _descriptor.Descriptor(
  name='GetAppointItemRes',
  full_name='SanProto.GetAppointItemRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.GetAppointItemRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='resource', full_name='SanProto.GetAppointItemRes.resource', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=223,
  serialized_end=300,
)


_STARTAPPOINTREQ = _descriptor.Descriptor(
  name='StartAppointReq',
  full_name='SanProto.StartAppointReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.StartAppointReq.user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='battle', full_name='SanProto.StartAppointReq.battle', index=1,
      number=2, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='node', full_name='SanProto.StartAppointReq.node', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='item', full_name='SanProto.StartAppointReq.item', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=303,
  serialized_end=448,
)


_STARTAPPOINTRES = _descriptor.Descriptor(
  name='StartAppointRes',
  full_name='SanProto.StartAppointRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.StartAppointRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='resource', full_name='SanProto.StartAppointRes.resource', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='conscripts', full_name='SanProto.StartAppointRes.conscripts', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=450,
  serialized_end=570,
)


_FINISHAPPOINTREQ = _descriptor.Descriptor(
  name='FinishAppointReq',
  full_name='SanProto.FinishAppointReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.FinishAppointReq.user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='node', full_name='SanProto.FinishAppointReq.node', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=572,
  serialized_end=641,
)


_FINISHAPPOINTRES = _descriptor.Descriptor(
  name='FinishAppointRes',
  full_name='SanProto.FinishAppointRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.FinishAppointRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='reward', full_name='SanProto.FinishAppointRes.reward', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='resource', full_name='SanProto.FinishAppointRes.resource', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='monarch', full_name='SanProto.FinishAppointRes.monarch', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='conscripts', full_name='SanProto.FinishAppointRes.conscripts', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='nodes', full_name='SanProto.FinishAppointRes.nodes', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='items', full_name='SanProto.FinishAppointRes.items', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='heros', full_name='SanProto.FinishAppointRes.heros', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='mails', full_name='SanProto.FinishAppointRes.mails', index=8,
      number=9, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ret', full_name='SanProto.FinishAppointRes.ret', index=9,
      number=10, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='node', full_name='SanProto.FinishAppointRes.node', index=10,
      number=11, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='energy', full_name='SanProto.FinishAppointRes.energy', index=11,
      number=12, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _FINISHAPPOINTRES_RET,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=644,
  serialized_end=1131,
)

_GETAPPOINTITEMREQ.fields_by_name['item'].message_type = item_pb2._ITEMINFO
_GETAPPOINTITEMRES.fields_by_name['resource'].message_type = resource_pb2._RESOURCEINFO
_STARTAPPOINTREQ.fields_by_name['battle'].message_type = battle_pb2._BATTLEINPUTINFO
_STARTAPPOINTREQ.fields_by_name['node'].message_type = node_pb2._NODEINFO
_STARTAPPOINTREQ.fields_by_name['item'].message_type = item_pb2._ITEMINFO
_STARTAPPOINTRES.fields_by_name['resource'].message_type = resource_pb2._RESOURCEINFO
_STARTAPPOINTRES.fields_by_name['conscripts'].message_type = conscript_pb2._CONSCRIPTINFO
_FINISHAPPOINTREQ.fields_by_name['node'].message_type = node_pb2._NODEINFO
_FINISHAPPOINTRES.fields_by_name['reward'].message_type = battle_pb2._BATTLEREWARD
_FINISHAPPOINTRES.fields_by_name['resource'].message_type = resource_pb2._RESOURCEINFO
_FINISHAPPOINTRES.fields_by_name['monarch'].message_type = monarch_pb2._MONARCHINFO
_FINISHAPPOINTRES.fields_by_name['conscripts'].message_type = conscript_pb2._CONSCRIPTINFO
_FINISHAPPOINTRES.fields_by_name['nodes'].message_type = node_pb2._NODEINFO
_FINISHAPPOINTRES.fields_by_name['items'].message_type = item_pb2._ITEMINFO
_FINISHAPPOINTRES.fields_by_name['heros'].message_type = hero_pb2._HEROINFO
_FINISHAPPOINTRES.fields_by_name['mails'].message_type = mail_pb2._MAILINFO
_FINISHAPPOINTRES.fields_by_name['ret'].enum_type = _FINISHAPPOINTRES_RET
_FINISHAPPOINTRES.fields_by_name['node'].message_type = node_pb2._NODEINFO
_FINISHAPPOINTRES.fields_by_name['energy'].message_type = energy_pb2._ENERGYINFO
_FINISHAPPOINTRES_RET.containing_type = _FINISHAPPOINTRES
DESCRIPTOR.message_types_by_name['GetAppointItemReq'] = _GETAPPOINTITEMREQ
DESCRIPTOR.message_types_by_name['GetAppointItemRes'] = _GETAPPOINTITEMRES
DESCRIPTOR.message_types_by_name['StartAppointReq'] = _STARTAPPOINTREQ
DESCRIPTOR.message_types_by_name['StartAppointRes'] = _STARTAPPOINTRES
DESCRIPTOR.message_types_by_name['FinishAppointReq'] = _FINISHAPPOINTREQ
DESCRIPTOR.message_types_by_name['FinishAppointRes'] = _FINISHAPPOINTRES

GetAppointItemReq = _reflection.GeneratedProtocolMessageType('GetAppointItemReq', (_message.Message,), dict(
  DESCRIPTOR = _GETAPPOINTITEMREQ,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.GetAppointItemReq)
  ))
_sym_db.RegisterMessage(GetAppointItemReq)

GetAppointItemRes = _reflection.GeneratedProtocolMessageType('GetAppointItemRes', (_message.Message,), dict(
  DESCRIPTOR = _GETAPPOINTITEMRES,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.GetAppointItemRes)
  ))
_sym_db.RegisterMessage(GetAppointItemRes)

StartAppointReq = _reflection.GeneratedProtocolMessageType('StartAppointReq', (_message.Message,), dict(
  DESCRIPTOR = _STARTAPPOINTREQ,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.StartAppointReq)
  ))
_sym_db.RegisterMessage(StartAppointReq)

StartAppointRes = _reflection.GeneratedProtocolMessageType('StartAppointRes', (_message.Message,), dict(
  DESCRIPTOR = _STARTAPPOINTRES,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.StartAppointRes)
  ))
_sym_db.RegisterMessage(StartAppointRes)

FinishAppointReq = _reflection.GeneratedProtocolMessageType('FinishAppointReq', (_message.Message,), dict(
  DESCRIPTOR = _FINISHAPPOINTREQ,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.FinishAppointReq)
  ))
_sym_db.RegisterMessage(FinishAppointReq)

FinishAppointRes = _reflection.GeneratedProtocolMessageType('FinishAppointRes', (_message.Message,), dict(
  DESCRIPTOR = _FINISHAPPOINTRES,
  __module__ = 'appoint_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.FinishAppointRes)
  ))
_sym_db.RegisterMessage(FinishAppointRes)


# @@protoc_insertion_point(module_scope)