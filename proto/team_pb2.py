# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: team.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import hero_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='team.proto',
  package='SanProto',
  serialized_pb=_b('\n\nteam.proto\x12\x08SanProto\x1a\nhero.proto\"\xa7\x01\n\x08TeamInfo\x12\r\n\x05index\x18\x01 \x02(\x05\x12\"\n\x06heroes\x18\x03 \x03(\x0b\x32\x12.SanProto.HeroInfo\x12\x16\n\x0e\x62\x61ttle_node_id\x18\x04 \x01(\x05\x12\x1f\n\x17union_battle_node_index\x18\x05 \x01(\x05\x12\x17\n\x0fin_anneal_sweep\x18\x06 \x01(\x08\x12\x16\n\x0ehero_positions\x18\x07 \x03(\x05\"D\n\x0eModifyTeamsReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\x12!\n\x05teams\x18\x02 \x03(\x0b\x32\x12.SanProto.TeamInfo\" \n\x0eModifyTeamsRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\"-\n\x12RefreshAllTeamsReq\x12\x17\n\x0ftrigger_user_id\x18\x01 \x02(\x04\"$\n\x12RefreshAllTeamsRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\",\n\x19ReceiveRefreshAllTeamsReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\"+\n\x19ReceiveRefreshAllTeamsRes\x12\x0e\n\x06status\x18\x01 \x02(\x05')
  ,
  dependencies=[hero_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_TEAMINFO = _descriptor.Descriptor(
  name='TeamInfo',
  full_name='SanProto.TeamInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='index', full_name='SanProto.TeamInfo.index', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='heroes', full_name='SanProto.TeamInfo.heroes', index=1,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='battle_node_id', full_name='SanProto.TeamInfo.battle_node_id', index=2,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='union_battle_node_index', full_name='SanProto.TeamInfo.union_battle_node_index', index=3,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='in_anneal_sweep', full_name='SanProto.TeamInfo.in_anneal_sweep', index=4,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='hero_positions', full_name='SanProto.TeamInfo.hero_positions', index=5,
      number=7, type=5, cpp_type=1, label=3,
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
  serialized_start=37,
  serialized_end=204,
)


_MODIFYTEAMSREQ = _descriptor.Descriptor(
  name='ModifyTeamsReq',
  full_name='SanProto.ModifyTeamsReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.ModifyTeamsReq.user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='teams', full_name='SanProto.ModifyTeamsReq.teams', index=1,
      number=2, type=11, cpp_type=10, label=3,
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
  serialized_start=206,
  serialized_end=274,
)


_MODIFYTEAMSRES = _descriptor.Descriptor(
  name='ModifyTeamsRes',
  full_name='SanProto.ModifyTeamsRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.ModifyTeamsRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=276,
  serialized_end=308,
)


_REFRESHALLTEAMSREQ = _descriptor.Descriptor(
  name='RefreshAllTeamsReq',
  full_name='SanProto.RefreshAllTeamsReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='trigger_user_id', full_name='SanProto.RefreshAllTeamsReq.trigger_user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=310,
  serialized_end=355,
)


_REFRESHALLTEAMSRES = _descriptor.Descriptor(
  name='RefreshAllTeamsRes',
  full_name='SanProto.RefreshAllTeamsRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.RefreshAllTeamsRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=357,
  serialized_end=393,
)


_RECEIVEREFRESHALLTEAMSREQ = _descriptor.Descriptor(
  name='ReceiveRefreshAllTeamsReq',
  full_name='SanProto.ReceiveRefreshAllTeamsReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.ReceiveRefreshAllTeamsReq.user_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=395,
  serialized_end=439,
)


_RECEIVEREFRESHALLTEAMSRES = _descriptor.Descriptor(
  name='ReceiveRefreshAllTeamsRes',
  full_name='SanProto.ReceiveRefreshAllTeamsRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.ReceiveRefreshAllTeamsRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=441,
  serialized_end=484,
)

_TEAMINFO.fields_by_name['heroes'].message_type = hero_pb2._HEROINFO
_MODIFYTEAMSREQ.fields_by_name['teams'].message_type = _TEAMINFO
DESCRIPTOR.message_types_by_name['TeamInfo'] = _TEAMINFO
DESCRIPTOR.message_types_by_name['ModifyTeamsReq'] = _MODIFYTEAMSREQ
DESCRIPTOR.message_types_by_name['ModifyTeamsRes'] = _MODIFYTEAMSRES
DESCRIPTOR.message_types_by_name['RefreshAllTeamsReq'] = _REFRESHALLTEAMSREQ
DESCRIPTOR.message_types_by_name['RefreshAllTeamsRes'] = _REFRESHALLTEAMSRES
DESCRIPTOR.message_types_by_name['ReceiveRefreshAllTeamsReq'] = _RECEIVEREFRESHALLTEAMSREQ
DESCRIPTOR.message_types_by_name['ReceiveRefreshAllTeamsRes'] = _RECEIVEREFRESHALLTEAMSRES

TeamInfo = _reflection.GeneratedProtocolMessageType('TeamInfo', (_message.Message,), dict(
  DESCRIPTOR = _TEAMINFO,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.TeamInfo)
  ))
_sym_db.RegisterMessage(TeamInfo)

ModifyTeamsReq = _reflection.GeneratedProtocolMessageType('ModifyTeamsReq', (_message.Message,), dict(
  DESCRIPTOR = _MODIFYTEAMSREQ,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ModifyTeamsReq)
  ))
_sym_db.RegisterMessage(ModifyTeamsReq)

ModifyTeamsRes = _reflection.GeneratedProtocolMessageType('ModifyTeamsRes', (_message.Message,), dict(
  DESCRIPTOR = _MODIFYTEAMSRES,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ModifyTeamsRes)
  ))
_sym_db.RegisterMessage(ModifyTeamsRes)

RefreshAllTeamsReq = _reflection.GeneratedProtocolMessageType('RefreshAllTeamsReq', (_message.Message,), dict(
  DESCRIPTOR = _REFRESHALLTEAMSREQ,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.RefreshAllTeamsReq)
  ))
_sym_db.RegisterMessage(RefreshAllTeamsReq)

RefreshAllTeamsRes = _reflection.GeneratedProtocolMessageType('RefreshAllTeamsRes', (_message.Message,), dict(
  DESCRIPTOR = _REFRESHALLTEAMSRES,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.RefreshAllTeamsRes)
  ))
_sym_db.RegisterMessage(RefreshAllTeamsRes)

ReceiveRefreshAllTeamsReq = _reflection.GeneratedProtocolMessageType('ReceiveRefreshAllTeamsReq', (_message.Message,), dict(
  DESCRIPTOR = _RECEIVEREFRESHALLTEAMSREQ,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ReceiveRefreshAllTeamsReq)
  ))
_sym_db.RegisterMessage(ReceiveRefreshAllTeamsReq)

ReceiveRefreshAllTeamsRes = _reflection.GeneratedProtocolMessageType('ReceiveRefreshAllTeamsRes', (_message.Message,), dict(
  DESCRIPTOR = _RECEIVEREFRESHALLTEAMSRES,
  __module__ = 'team_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ReceiveRefreshAllTeamsRes)
  ))
_sym_db.RegisterMessage(ReceiveRefreshAllTeamsRes)


# @@protoc_insertion_point(module_scope)
