# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: boss.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import team_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='boss.proto',
  package='SanProto',
  serialized_pb=_b('\n\nboss.proto\x12\x08SanProto\x1a\nteam.proto\"\xa8\x01\n\x12WorldBossBasicInfo\x12\n\n\x02id\x18\x01 \x02(\x05\x12\x0f\n\x07\x62oss_id\x18\x02 \x02(\x05\x12\x0c\n\x04\x64\x61te\x18\x03 \x01(\x0c\x12\x12\n\nstart_time\x18\x04 \x01(\x0c\x12\x10\n\x08\x65nd_time\x18\x05 \x01(\x0c\x12\x13\n\x0b\x64\x65scription\x18\x06 \x01(\x0c\x12\x19\n\x11total_soldier_num\x18\x07 \x01(\x05\x12\x11\n\tarrays_id\x18\x08 \x03(\x05\"D\n\x14\x41\x64\x64\x42\x61sicWorldBossReq\x12,\n\x06\x62osses\x18\x01 \x03(\x0b\x32\x1c.SanProto.WorldBossBasicInfo\"&\n\x14\x41\x64\x64\x42\x61sicWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\"&\n\x17\x44\x65leteBasicWorldBossReq\x12\x0b\n\x03ids\x18\x01 \x03(\x05\")\n\x17\x44\x65leteBasicWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\"5\n\x16QueryBasicWorldBossReq\x12\x0e\n\x06is_all\x18\x01 \x01(\x08\x12\x0b\n\x03ids\x18\x02 \x03(\x05\"V\n\x16QueryBasicWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12,\n\x06\x62osses\x18\x02 \x03(\x0b\x32\x1c.SanProto.WorldBossBasicInfo\"\xfd\x03\n\rWorldBossInfo\x12.\n\x06status\x18\x01 \x01(\x0e\x32\x1e.SanProto.WorldBossInfo.STATUS\x12\x10\n\x08\x65nd_time\x18\x02 \x01(\x05\x12\x13\n\x0blimit_level\x18\x03 \x01(\x05\x12\x19\n\x11total_soldier_num\x18\x04 \x01(\x05\x12\x1b\n\x13\x63urrent_soldier_num\x18\x05 \x01(\x05\x12\x13\n\x0b\x64\x65scription\x18\x06 \x01(\x0c\x12\'\n\x0b\x66irst_teams\x18\x07 \x03(\x0b\x32\x12.SanProto.TeamInfo\x12(\n\x0csecond_teams\x18\x08 \x03(\x0b\x32\x12.SanProto.TeamInfo\x12\'\n\x0bthird_teams\x18\t \x03(\x0b\x32\x12.SanProto.TeamInfo\x12\x1e\n\x16\x63\x61n_attack_teams_index\x18\n \x03(\x05\x12\x19\n\x11teams_coefficient\x18\x0b \x03(\x02\x12\x16\n\x0ekill_user_name\x18\x0c \x01(\x0c\x12\x14\n\x0ckill_user_id\x18\r \x01(\x04\"c\n\x06STATUS\x12\x0c\n\x08INACTIVE\x10\x01\x12\x11\n\rBEFORE_BATTLE\x10\x02\x12\r\n\tIN_BATTLE\x10\x03\x12\x10\n\x0c\x41\x46TER_BATTLE\x10\x04\x12\n\n\x06LOCKED\x10\x05\x12\x0b\n\x07\x44ISABLE\x10\x06\"\x13\n\x11QueryWorldBossReq\"p\n\x11QueryWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12$\n\x03ret\x18\x02 \x01(\x0e\x32\x17.SanProto.WORLDBOSS_RET\x12%\n\x04\x62oss\x18\x03 \x01(\x0b\x32\x17.SanProto.WorldBossInfo\"\xbb\x01\n\x17QueryCommonWorldBossReq\x12\x12\n\narise_time\x18\x01 \x01(\x05\x12\x12\n\nstart_time\x18\x02 \x01(\x05\x12\x10\n\x08\x65nd_time\x18\x03 \x01(\x05\x12\x0f\n\x07\x62oss_id\x18\x04 \x01(\x05\x12\x19\n\x11total_soldier_num\x18\x05 \x01(\x05\x12\x0f\n\x07user_id\x18\x06 \x01(\x04\x12\x11\n\tuser_name\x18\x07 \x01(\x0c\x12\x16\n\x0ekills_addition\x18\x08 \x01(\x05\"\x8f\x01\n\x17QueryCommonWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\x12\x19\n\x11total_soldier_num\x18\x02 \x01(\x05\x12\x1b\n\x13\x63urrent_soldier_num\x18\x03 \x01(\x05\x12\x16\n\x0ekill_user_name\x18\x04 \x01(\x0c\x12\x14\n\x0ckill_user_id\x18\x05 \x01(\x04\"z\n\x12ModifyWorldBossReq\x12\x19\n\x11total_soldier_num\x18\x01 \x01(\x05\x12\x1b\n\x13\x63urrent_soldier_num\x18\x02 \x01(\x05\x12\x16\n\x0ekill_user_name\x18\x03 \x01(\x0c\x12\x14\n\x0ckill_user_id\x18\x04 \x01(\x04\"$\n\x12ModifyWorldBossRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\")\n\x16\x43learWorldBossMeritReq\x12\x0f\n\x07user_id\x18\x01 \x02(\x04\"(\n\x16\x43learWorldBossMeritRes\x12\x0e\n\x06status\x18\x01 \x02(\x05\"\x1f\n\x1dReceiveClearWorldBossMeritReq\"/\n\x1dReceiveClearWorldBossMeritRes\x12\x0e\n\x06status\x18\x01 \x02(\x05*R\n\rWORLDBOSS_RET\x12\x0b\n\x07\x42OSS_OK\x10\x00\x12\x0f\n\x0b\x42OSS_KILLED\x10\x01\x12\x10\n\x0c\x42OSS_EXPIRED\x10\x02\x12\x11\n\rBOSS_OVERTIME\x10\x03')
  ,
  dependencies=[team_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_WORLDBOSS_RET = _descriptor.EnumDescriptor(
  name='WORLDBOSS_RET',
  full_name='SanProto.WORLDBOSS_RET',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='BOSS_OK', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BOSS_KILLED', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BOSS_EXPIRED', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BOSS_OVERTIME', index=3, number=3,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=1855,
  serialized_end=1937,
)
_sym_db.RegisterEnumDescriptor(_WORLDBOSS_RET)

WORLDBOSS_RET = enum_type_wrapper.EnumTypeWrapper(_WORLDBOSS_RET)
BOSS_OK = 0
BOSS_KILLED = 1
BOSS_EXPIRED = 2
BOSS_OVERTIME = 3


_WORLDBOSSINFO_STATUS = _descriptor.EnumDescriptor(
  name='STATUS',
  full_name='SanProto.WorldBossInfo.STATUS',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='INACTIVE', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BEFORE_BATTLE', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='IN_BATTLE', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='AFTER_BATTLE', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LOCKED', index=4, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DISABLE', index=5, number=6,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=954,
  serialized_end=1053,
)
_sym_db.RegisterEnumDescriptor(_WORLDBOSSINFO_STATUS)


_WORLDBOSSBASICINFO = _descriptor.Descriptor(
  name='WorldBossBasicInfo',
  full_name='SanProto.WorldBossBasicInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='SanProto.WorldBossBasicInfo.id', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='boss_id', full_name='SanProto.WorldBossBasicInfo.boss_id', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='date', full_name='SanProto.WorldBossBasicInfo.date', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='start_time', full_name='SanProto.WorldBossBasicInfo.start_time', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='end_time', full_name='SanProto.WorldBossBasicInfo.end_time', index=4,
      number=5, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='description', full_name='SanProto.WorldBossBasicInfo.description', index=5,
      number=6, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_soldier_num', full_name='SanProto.WorldBossBasicInfo.total_soldier_num', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='arrays_id', full_name='SanProto.WorldBossBasicInfo.arrays_id', index=7,
      number=8, type=5, cpp_type=1, label=3,
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
  serialized_end=205,
)


_ADDBASICWORLDBOSSREQ = _descriptor.Descriptor(
  name='AddBasicWorldBossReq',
  full_name='SanProto.AddBasicWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bosses', full_name='SanProto.AddBasicWorldBossReq.bosses', index=0,
      number=1, type=11, cpp_type=10, label=3,
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
  serialized_start=207,
  serialized_end=275,
)


_ADDBASICWORLDBOSSRES = _descriptor.Descriptor(
  name='AddBasicWorldBossRes',
  full_name='SanProto.AddBasicWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.AddBasicWorldBossRes.status', index=0,
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
  serialized_start=277,
  serialized_end=315,
)


_DELETEBASICWORLDBOSSREQ = _descriptor.Descriptor(
  name='DeleteBasicWorldBossReq',
  full_name='SanProto.DeleteBasicWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ids', full_name='SanProto.DeleteBasicWorldBossReq.ids', index=0,
      number=1, type=5, cpp_type=1, label=3,
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
  serialized_start=317,
  serialized_end=355,
)


_DELETEBASICWORLDBOSSRES = _descriptor.Descriptor(
  name='DeleteBasicWorldBossRes',
  full_name='SanProto.DeleteBasicWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.DeleteBasicWorldBossRes.status', index=0,
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
  serialized_end=398,
)


_QUERYBASICWORLDBOSSREQ = _descriptor.Descriptor(
  name='QueryBasicWorldBossReq',
  full_name='SanProto.QueryBasicWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='is_all', full_name='SanProto.QueryBasicWorldBossReq.is_all', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ids', full_name='SanProto.QueryBasicWorldBossReq.ids', index=1,
      number=2, type=5, cpp_type=1, label=3,
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
  serialized_start=400,
  serialized_end=453,
)


_QUERYBASICWORLDBOSSRES = _descriptor.Descriptor(
  name='QueryBasicWorldBossRes',
  full_name='SanProto.QueryBasicWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.QueryBasicWorldBossRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='bosses', full_name='SanProto.QueryBasicWorldBossRes.bosses', index=1,
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
  serialized_start=455,
  serialized_end=541,
)


_WORLDBOSSINFO = _descriptor.Descriptor(
  name='WorldBossInfo',
  full_name='SanProto.WorldBossInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.WorldBossInfo.status', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='end_time', full_name='SanProto.WorldBossInfo.end_time', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='limit_level', full_name='SanProto.WorldBossInfo.limit_level', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_soldier_num', full_name='SanProto.WorldBossInfo.total_soldier_num', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='current_soldier_num', full_name='SanProto.WorldBossInfo.current_soldier_num', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='description', full_name='SanProto.WorldBossInfo.description', index=5,
      number=6, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='first_teams', full_name='SanProto.WorldBossInfo.first_teams', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='second_teams', full_name='SanProto.WorldBossInfo.second_teams', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='third_teams', full_name='SanProto.WorldBossInfo.third_teams', index=8,
      number=9, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='can_attack_teams_index', full_name='SanProto.WorldBossInfo.can_attack_teams_index', index=9,
      number=10, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='teams_coefficient', full_name='SanProto.WorldBossInfo.teams_coefficient', index=10,
      number=11, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_name', full_name='SanProto.WorldBossInfo.kill_user_name', index=11,
      number=12, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_id', full_name='SanProto.WorldBossInfo.kill_user_id', index=12,
      number=13, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _WORLDBOSSINFO_STATUS,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=544,
  serialized_end=1053,
)


_QUERYWORLDBOSSREQ = _descriptor.Descriptor(
  name='QueryWorldBossReq',
  full_name='SanProto.QueryWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
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
  serialized_start=1055,
  serialized_end=1074,
)


_QUERYWORLDBOSSRES = _descriptor.Descriptor(
  name='QueryWorldBossRes',
  full_name='SanProto.QueryWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.QueryWorldBossRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ret', full_name='SanProto.QueryWorldBossRes.ret', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='boss', full_name='SanProto.QueryWorldBossRes.boss', index=2,
      number=3, type=11, cpp_type=10, label=1,
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
  serialized_start=1076,
  serialized_end=1188,
)


_QUERYCOMMONWORLDBOSSREQ = _descriptor.Descriptor(
  name='QueryCommonWorldBossReq',
  full_name='SanProto.QueryCommonWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='arise_time', full_name='SanProto.QueryCommonWorldBossReq.arise_time', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='start_time', full_name='SanProto.QueryCommonWorldBossReq.start_time', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='end_time', full_name='SanProto.QueryCommonWorldBossReq.end_time', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='boss_id', full_name='SanProto.QueryCommonWorldBossReq.boss_id', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_soldier_num', full_name='SanProto.QueryCommonWorldBossReq.total_soldier_num', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.QueryCommonWorldBossReq.user_id', index=5,
      number=6, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='user_name', full_name='SanProto.QueryCommonWorldBossReq.user_name', index=6,
      number=7, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kills_addition', full_name='SanProto.QueryCommonWorldBossReq.kills_addition', index=7,
      number=8, type=5, cpp_type=1, label=1,
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
  serialized_start=1191,
  serialized_end=1378,
)


_QUERYCOMMONWORLDBOSSRES = _descriptor.Descriptor(
  name='QueryCommonWorldBossRes',
  full_name='SanProto.QueryCommonWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.QueryCommonWorldBossRes.status', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_soldier_num', full_name='SanProto.QueryCommonWorldBossRes.total_soldier_num', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='current_soldier_num', full_name='SanProto.QueryCommonWorldBossRes.current_soldier_num', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_name', full_name='SanProto.QueryCommonWorldBossRes.kill_user_name', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_id', full_name='SanProto.QueryCommonWorldBossRes.kill_user_id', index=4,
      number=5, type=4, cpp_type=4, label=1,
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
  serialized_start=1381,
  serialized_end=1524,
)


_MODIFYWORLDBOSSREQ = _descriptor.Descriptor(
  name='ModifyWorldBossReq',
  full_name='SanProto.ModifyWorldBossReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='total_soldier_num', full_name='SanProto.ModifyWorldBossReq.total_soldier_num', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='current_soldier_num', full_name='SanProto.ModifyWorldBossReq.current_soldier_num', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_name', full_name='SanProto.ModifyWorldBossReq.kill_user_name', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='kill_user_id', full_name='SanProto.ModifyWorldBossReq.kill_user_id', index=3,
      number=4, type=4, cpp_type=4, label=1,
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
  serialized_start=1526,
  serialized_end=1648,
)


_MODIFYWORLDBOSSRES = _descriptor.Descriptor(
  name='ModifyWorldBossRes',
  full_name='SanProto.ModifyWorldBossRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.ModifyWorldBossRes.status', index=0,
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
  serialized_start=1650,
  serialized_end=1686,
)


_CLEARWORLDBOSSMERITREQ = _descriptor.Descriptor(
  name='ClearWorldBossMeritReq',
  full_name='SanProto.ClearWorldBossMeritReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='SanProto.ClearWorldBossMeritReq.user_id', index=0,
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
  serialized_start=1688,
  serialized_end=1729,
)


_CLEARWORLDBOSSMERITRES = _descriptor.Descriptor(
  name='ClearWorldBossMeritRes',
  full_name='SanProto.ClearWorldBossMeritRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.ClearWorldBossMeritRes.status', index=0,
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
  serialized_start=1731,
  serialized_end=1771,
)


_RECEIVECLEARWORLDBOSSMERITREQ = _descriptor.Descriptor(
  name='ReceiveClearWorldBossMeritReq',
  full_name='SanProto.ReceiveClearWorldBossMeritReq',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
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
  serialized_start=1773,
  serialized_end=1804,
)


_RECEIVECLEARWORLDBOSSMERITRES = _descriptor.Descriptor(
  name='ReceiveClearWorldBossMeritRes',
  full_name='SanProto.ReceiveClearWorldBossMeritRes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='SanProto.ReceiveClearWorldBossMeritRes.status', index=0,
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
  serialized_start=1806,
  serialized_end=1853,
)

_ADDBASICWORLDBOSSREQ.fields_by_name['bosses'].message_type = _WORLDBOSSBASICINFO
_QUERYBASICWORLDBOSSRES.fields_by_name['bosses'].message_type = _WORLDBOSSBASICINFO
_WORLDBOSSINFO.fields_by_name['status'].enum_type = _WORLDBOSSINFO_STATUS
_WORLDBOSSINFO.fields_by_name['first_teams'].message_type = team_pb2._TEAMINFO
_WORLDBOSSINFO.fields_by_name['second_teams'].message_type = team_pb2._TEAMINFO
_WORLDBOSSINFO.fields_by_name['third_teams'].message_type = team_pb2._TEAMINFO
_WORLDBOSSINFO_STATUS.containing_type = _WORLDBOSSINFO
_QUERYWORLDBOSSRES.fields_by_name['ret'].enum_type = _WORLDBOSS_RET
_QUERYWORLDBOSSRES.fields_by_name['boss'].message_type = _WORLDBOSSINFO
DESCRIPTOR.message_types_by_name['WorldBossBasicInfo'] = _WORLDBOSSBASICINFO
DESCRIPTOR.message_types_by_name['AddBasicWorldBossReq'] = _ADDBASICWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['AddBasicWorldBossRes'] = _ADDBASICWORLDBOSSRES
DESCRIPTOR.message_types_by_name['DeleteBasicWorldBossReq'] = _DELETEBASICWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['DeleteBasicWorldBossRes'] = _DELETEBASICWORLDBOSSRES
DESCRIPTOR.message_types_by_name['QueryBasicWorldBossReq'] = _QUERYBASICWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['QueryBasicWorldBossRes'] = _QUERYBASICWORLDBOSSRES
DESCRIPTOR.message_types_by_name['WorldBossInfo'] = _WORLDBOSSINFO
DESCRIPTOR.message_types_by_name['QueryWorldBossReq'] = _QUERYWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['QueryWorldBossRes'] = _QUERYWORLDBOSSRES
DESCRIPTOR.message_types_by_name['QueryCommonWorldBossReq'] = _QUERYCOMMONWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['QueryCommonWorldBossRes'] = _QUERYCOMMONWORLDBOSSRES
DESCRIPTOR.message_types_by_name['ModifyWorldBossReq'] = _MODIFYWORLDBOSSREQ
DESCRIPTOR.message_types_by_name['ModifyWorldBossRes'] = _MODIFYWORLDBOSSRES
DESCRIPTOR.message_types_by_name['ClearWorldBossMeritReq'] = _CLEARWORLDBOSSMERITREQ
DESCRIPTOR.message_types_by_name['ClearWorldBossMeritRes'] = _CLEARWORLDBOSSMERITRES
DESCRIPTOR.message_types_by_name['ReceiveClearWorldBossMeritReq'] = _RECEIVECLEARWORLDBOSSMERITREQ
DESCRIPTOR.message_types_by_name['ReceiveClearWorldBossMeritRes'] = _RECEIVECLEARWORLDBOSSMERITRES
DESCRIPTOR.enum_types_by_name['WORLDBOSS_RET'] = _WORLDBOSS_RET

WorldBossBasicInfo = _reflection.GeneratedProtocolMessageType('WorldBossBasicInfo', (_message.Message,), dict(
  DESCRIPTOR = _WORLDBOSSBASICINFO,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.WorldBossBasicInfo)
  ))
_sym_db.RegisterMessage(WorldBossBasicInfo)

AddBasicWorldBossReq = _reflection.GeneratedProtocolMessageType('AddBasicWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _ADDBASICWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.AddBasicWorldBossReq)
  ))
_sym_db.RegisterMessage(AddBasicWorldBossReq)

AddBasicWorldBossRes = _reflection.GeneratedProtocolMessageType('AddBasicWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _ADDBASICWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.AddBasicWorldBossRes)
  ))
_sym_db.RegisterMessage(AddBasicWorldBossRes)

DeleteBasicWorldBossReq = _reflection.GeneratedProtocolMessageType('DeleteBasicWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _DELETEBASICWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.DeleteBasicWorldBossReq)
  ))
_sym_db.RegisterMessage(DeleteBasicWorldBossReq)

DeleteBasicWorldBossRes = _reflection.GeneratedProtocolMessageType('DeleteBasicWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _DELETEBASICWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.DeleteBasicWorldBossRes)
  ))
_sym_db.RegisterMessage(DeleteBasicWorldBossRes)

QueryBasicWorldBossReq = _reflection.GeneratedProtocolMessageType('QueryBasicWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _QUERYBASICWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryBasicWorldBossReq)
  ))
_sym_db.RegisterMessage(QueryBasicWorldBossReq)

QueryBasicWorldBossRes = _reflection.GeneratedProtocolMessageType('QueryBasicWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _QUERYBASICWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryBasicWorldBossRes)
  ))
_sym_db.RegisterMessage(QueryBasicWorldBossRes)

WorldBossInfo = _reflection.GeneratedProtocolMessageType('WorldBossInfo', (_message.Message,), dict(
  DESCRIPTOR = _WORLDBOSSINFO,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.WorldBossInfo)
  ))
_sym_db.RegisterMessage(WorldBossInfo)

QueryWorldBossReq = _reflection.GeneratedProtocolMessageType('QueryWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _QUERYWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryWorldBossReq)
  ))
_sym_db.RegisterMessage(QueryWorldBossReq)

QueryWorldBossRes = _reflection.GeneratedProtocolMessageType('QueryWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _QUERYWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryWorldBossRes)
  ))
_sym_db.RegisterMessage(QueryWorldBossRes)

QueryCommonWorldBossReq = _reflection.GeneratedProtocolMessageType('QueryCommonWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _QUERYCOMMONWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryCommonWorldBossReq)
  ))
_sym_db.RegisterMessage(QueryCommonWorldBossReq)

QueryCommonWorldBossRes = _reflection.GeneratedProtocolMessageType('QueryCommonWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _QUERYCOMMONWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.QueryCommonWorldBossRes)
  ))
_sym_db.RegisterMessage(QueryCommonWorldBossRes)

ModifyWorldBossReq = _reflection.GeneratedProtocolMessageType('ModifyWorldBossReq', (_message.Message,), dict(
  DESCRIPTOR = _MODIFYWORLDBOSSREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ModifyWorldBossReq)
  ))
_sym_db.RegisterMessage(ModifyWorldBossReq)

ModifyWorldBossRes = _reflection.GeneratedProtocolMessageType('ModifyWorldBossRes', (_message.Message,), dict(
  DESCRIPTOR = _MODIFYWORLDBOSSRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ModifyWorldBossRes)
  ))
_sym_db.RegisterMessage(ModifyWorldBossRes)

ClearWorldBossMeritReq = _reflection.GeneratedProtocolMessageType('ClearWorldBossMeritReq', (_message.Message,), dict(
  DESCRIPTOR = _CLEARWORLDBOSSMERITREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ClearWorldBossMeritReq)
  ))
_sym_db.RegisterMessage(ClearWorldBossMeritReq)

ClearWorldBossMeritRes = _reflection.GeneratedProtocolMessageType('ClearWorldBossMeritRes', (_message.Message,), dict(
  DESCRIPTOR = _CLEARWORLDBOSSMERITRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ClearWorldBossMeritRes)
  ))
_sym_db.RegisterMessage(ClearWorldBossMeritRes)

ReceiveClearWorldBossMeritReq = _reflection.GeneratedProtocolMessageType('ReceiveClearWorldBossMeritReq', (_message.Message,), dict(
  DESCRIPTOR = _RECEIVECLEARWORLDBOSSMERITREQ,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ReceiveClearWorldBossMeritReq)
  ))
_sym_db.RegisterMessage(ReceiveClearWorldBossMeritReq)

ReceiveClearWorldBossMeritRes = _reflection.GeneratedProtocolMessageType('ReceiveClearWorldBossMeritRes', (_message.Message,), dict(
  DESCRIPTOR = _RECEIVECLEARWORLDBOSSMERITRES,
  __module__ = 'boss_pb2'
  # @@protoc_insertion_point(class_scope:SanProto.ReceiveClearWorldBossMeritRes)
  ))
_sym_db.RegisterMessage(ReceiveClearWorldBossMeritRes)


# @@protoc_insertion_point(module_scope)