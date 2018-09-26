#coding:utf8
"""
Created on 2015-04-10
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 常用工具
"""

import hashlib
import os
import time
import base64
import math
import random
from Crypto.Hash import SHA256
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as pk
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from datalib.data_loader import data_loader
import copy
import logger
import string


START_HOUR = 0
END_HOUR = 24
SECONDS_OF_DAY = 86400
SECONDS_OF_HOUR = 3600
INVITE_CODE_KEY = 'bingchen'

def _get_day_start_hour():
    #if "day_start_hour" in data_loader.OtherBasicInfo_dict.keys():
    #    return int(float(data_loader.OtherBasicInfo_dict['day_start_hour'].value))
    #else:
    #    return START_HOUR

    try:
        return int(float(data_loader.OtherBasicInfo_dict['day_start_hour'].value))
    except:
        return START_HOUR


def _get_day_end_hour():
    #if "day_end_hour" in data_loader.OtherBasicInfo_dict.keys():
    #    return int(float(data_loader.OtherBasicInfo_dict['day_end_hour'].value))
    #else:
    #    return END_HOUR

    try:
        return int(float(data_loader.OtherBasicInfo_dict['day_end_hour'].value))
    except:
        return END_HOUR


def parse_timestring(timestring):
    """解析时间
    Format: YYYY-MM-DD
    """
    fields = timestring.split('-')
    assert len(fields) == 3
    [year, month, day] = map(int, fields)
    assert year >= 2015 and year <= 3000
    assert month >= 1 and month <= 12
    assert day >= 1 and day <= 31
    return (year, month, day)


def get_start_second_by_timestring(timestring):
    """获取指定的一天的开始时刻
    Args:
        timestring[string]: 时间 YYYY-MM-DD
    """
    (year, month, day) = parse_timestring(timestring)

    start = (year, month, day, _get_day_start_hour(), 0, 0, 0, 0, 0)
    return long(time.mktime(start))


def get_end_second_by_timestring(timestring):
    """获取指定的一天的结束时刻
    Args:
        timestring[string]: 时间 YYYY-MM-DD
    """
    (year, month, day) = parse_timestring(timestring)

    end = (year, month, day, _get_day_end_hour(), 0, 0, 0, 0, 0)
    return long(time.mktime(end))


def get_start_second(timestamp):
    """
    获取指定的一天的开始的时刻
    服务器定义：每天的起始从5点整开始
    Args:
        timestamp[int]: 时间戳
    Returns:
        timestamp[int]: 今天5点钟的时间戳
    """
    if timestamp == 0:
        timestamp = 946684800 #2000-01-01 00:00:00 UTC

    date = time.localtime(timestamp)
    start = (date.tm_year, date.tm_mon, date.tm_mday, _get_day_start_hour(), 0, 0,
            date.tm_wday, date.tm_yday, date.tm_isdst)
    start_ts = long(time.mktime(start))

    if timestamp < start_ts:
        start_ts -= SECONDS_OF_DAY

    return start_ts


def get_end_second(timestamp):
    """获取指定的一天的开始时刻"""
    if timestamp == 0:
        timestamp = 946684800 #2000-01-01 00:00:00 UTC
    
    date = time.localtime(timestamp)
    end = (date.tm_year, date.tm_mon, date.tm_mday, _get_day_end_hour(), 0, 0,
            date.tm_wday, date.tm_yday, date.tm_isdst)
    end_ts = long(time.mktime(end))

    if timestamp > end_ts:
        end_ts += SECONDS_OF_DAY

    return end_ts

def get_start_second_of_week(timestamp):
    """
    获取指定的一周的开始的时刻
    服务器定义：这一周周一的5点整，为这一周的开始
    Args:
        timestamp[int]: 时间戳
    Returns:
        timestamp[int]: 本周周一5点钟的时间戳
    """
    timestamp = get_start_second(timestamp)
    date = time.localtime(timestamp)
    timestamp -= SECONDS_OF_DAY * date.tm_wday

    return get_start_second(timestamp)



def get_spec_second(timestamp, spec_string):
    """
    获取今天某个指定时刻的 seconds
    timestamp[int]: 时间戳
    spec_string[string]: 指定时刻字符串(hh:mm)
    """
    t = spec_string.split(':')
    assert len(t) == 2
    hour = int(t[0])
    min = int(t[1])

    if hour == 24:
        assert min == 0
    else:
        assert hour >= 0 and hour < 24

    assert min >= 0 and min < 60

    seconds_per_hour = 3600
    seconds_per_min = 60
    start = get_start_second(timestamp)
    return start + (hour - _get_day_start_hour()) * seconds_per_hour + min * seconds_per_min


def count_days_diff(time1, time2):
    """计算天数差
    计算 time2 - time1 的天数
    """
    day1 = get_start_second(time1)
    day2 = get_start_second(time2)

    diff = day2 - day1
    assert diff % SECONDS_OF_DAY == 0
    num = diff / SECONDS_OF_DAY
    return num


def is_same_day(last_time, cur_time):
    """是否是同一天
    服务器一天起始是5点
    """
    return count_days_diff(last_time, cur_time) == 0


def is_same_month(last_time, cur_time):
    cur_date = time.localtime(cur_time)
    last_date = time.localtime(last_time)
    return cur_date.tm_mon == last_date.tm_mon


FIELD_SEP = '#'

def split_to_int(str_input):
    """
    """
    if str_input == "":
        return []

    int_list = []
    str_list = str_input.split(FIELD_SEP)
    if len(str_list) > 0:
        int_list = map(int, str_list)
    return int_list

def split_to_string(str_input):
    if str_input == "":
        return []

    return str_input.split(FIELD_SEP)

def join_to_string(int_list):
    """
    """
    str_output = FIELD_SEP.join(map(str, int_list))
    return str_output


def sha256_hash(value):
    """SHA256 哈希
    """
    obj = SHA256.new()
    obj.update(value)
    return obj.digest()


def hex_byte(value):
    output = ""
    for c in value:
        output += "{0:0>2X}".format(ord(c))
    return output


ALPHANUMERIC_CANDIDATE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
def random_alphanumeric(length = 10):
    """随机生成一串字母和数字
    """
    chosen = random.sample(ALPHANUMERIC_CANDIDATE, length)
    return "".join(chosen)


def random_salt(length = 32):
    """随机生成盐: 32字节
    Cryptographically Secure Pseudo-Random Number Generator (CSPRNG)
    """
    return os.urandom(length)


def rsa_importkey(keyfile):
    """读入 key
    """
    key = RSA.importKey(open(keyfile, 'r').read())
    return key


def rsa_sign(rawdata, key):
    """RSA 签名
    SHA + RSA
    Returns:
        base64 编码后的签名
    """
    hashdata = SHA.new(rawdata)
    signer = pk.new(key)
    signdata = signer.sign(hashdata)
    encodedata = base64.b64encode(signdata)
    return encodedata


def rsa_verify(rawdata, encodedata, key):
    """RSA 校验
    Args:
        rawdata: 原字符串
        encodedata: 签名+编码后的字符串
        key: 密钥
    Returns:
        True/False
    """
    logger.debug("encodedata=%s" % encodedata)
    logger.debug("rawdata=%s" % rawdata)

    signdata = base64.b64decode(encodedata)
    verifier = pk.new(key)
    return verifier.verify(SHA.new(rawdata), signdata)


def rsa_encrypt(rawdata, keyfile, length=100):
    """公钥签名
    """
    privatekey = open(keyfile, "r").read()
    #encryptor = RSA.importKey(privatekey, passphrase="f00bar")
    rsakey = RSA.importKey(privatekey)

    cipher = Cipher_pkcs1_v1_5.new(rsakey)
    #cipher_text = base64.b64encode(cipher.encrypt(rawdata))                         
    #return cipher_text

    res = []
    for i in range(0, len(rawdata), length):
        res.append(base64.b64encode(cipher.encrypt(rawdata[i:i+length])))
    return "".join(res)


#浮点数比较
ACCURACY = 1e-4     #精度

def float_eq(v1, v2):
    """v1 == v2"""
    return math.fabs(v1 - v2) < ACCURACY

def float_neq(v1, v2):
    """v1 != v2"""
    return not float_eq(v1, v2)

def float_gt(v1, v2):
    """v1 > v2"""
    return v1 - v2 > ACCURACY

def float_lt(v1, v2):
    """v1 < v2"""
    return v2 - v1 > ACCURACY

def float_gte(v1, v2):
    """v1 >= v2"""
    return float_gt(v1, v2) or float_eq(v1, v2)

def float_lte(v1, v2):
    """v1 <= v2"""
    return float_lt(v1, v2) or float_eq(v1, v2)

def floor_to_int(value):
    """向下取整
    """
    return int(round(value, 4))

def round46(value):
    """四舍六入五成双"""
    integer = int(value)
    decimal = integer + 0.5

    if float_gt(value, decimal):
        return integer + 1
    elif float_lt(value, decimal):
        return integer
    else:
        if integer % 2 == 0:
            return integer
        else:
            return integer + 1

def ceil_to_int(value):
    """向上取整
    """
    return int(math.ceil(round(value, 4)))

def object2dict(obj):
    """对象转化成字典"""
    if hasattr(obj, '__slots__'):
        d = {}
        for attr in obj.__slots__:
            d[attr] = getattr(obj, attr)
        return d
    else:
        return obj.__dict__

def random_weight(array, num = 1, back = True):
    """按权重随机抽取
    @args:
        array:权重数组
        num:抽取数量
        back:是否放回
    @return:
        index list
    """
    assert num > 0
    if not back:
        assert num <= len(array)

    array = copy.deepcopy(array)
    ret = []

    for i in xrange(num):
        weight_sum = sum(array)
        rand = random.random() * weight_sum

        pre_weight = 0
        choice = None
        for i, weight in enumerate(array):
            if pre_weight <= rand <= weight + pre_weight:
                choice = i
                break
            pre_weight += weight

        assert choice is not None
        if not back:
            array[choice] = 0
        ret.append(choice)

    return ret

def random_choose_n(array, n):
    """随机选择n个"""
    assert len(array) >= n
    array = copy.deepcopy(array)
    choice = []
    for i in range(n):
        rand_index = random.randint(0, len(array)-1)
        choice.append(array[rand_index])
        array.pop(rand_index)

    return choice

def md5_hash(value):
    """MD5 哈希
    """
    md5 = hashlib.md5()
    md5.update(value)
    hex_value = md5.hexdigest() 
    return hex_value


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags

def encode(strorg,key):
    strlength=len(strorg)
    baselength=len(key)
    hh=[]
    for i in range(strlength):
        hh.append(chr((ord(strorg[i])+ord(key[i % baselength]))%256))
    return base64.b64encode(''.join(hh))

def decode(orig,key):
    try:
        strorg = base64.b64decode(orig)
        strlength=len(strorg)
        keylength=len(key)
        mystr=' '*strlength
        hh=[]
        for i in range(strlength):
            hh.append((ord(strorg[i])-ord(key[i%keylength]))%256)
        return ''.join(chr(i) for i in hh).decode('utf-8')
    except:
        return ""
