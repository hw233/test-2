#coding:utf8
"""
Created on 2016-03-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 充值过程逻辑，应付各个平台不同的充值逻辑
"""

import time
import os
import re
import json
import socket
import random
from urllib import urlencode
from firefly.server.globalobject import GlobalObject
from firefly.utils.singleton import Singleton
from utils.redis_agent import RedisAgent
from utils import logger
from utils import utils
from app.data.pay import PayPool
from datalib.data_loader import data_loader


class PayRedisAgent(object):
    """访问充值记录 Reids
    """
    __metaclass__ = Singleton

    def connect(self, ip, port, db = '0', password = None, timeout = 1):
        """初始化
        Args:
            timeout : 连接超时事件，单位 s
        """
        self.redis = RedisAgent()
        self.redis.connect(ip, port, db, password, timeout)


    def get(self, order_no):
        """根据订单号，获取订单信息
        Returns:
            如果订单号未完成，返回 None
        """
        value = self.redis.client.get(order_no)
        if value is None:
            return value
        return value.split('&')


    def finish(self, order_no):
        """完成订单
        Returns:
            True/False
        """
        if self.redis.client.delete(order_no) == 0:
            logger.warning("Delete order no failed[order_no=%s]" % order_no)
            return False
        return True


    def get_set(self, server_id, user_id):
        """根据服务器 id 和用户 id，获取其所有完成订单信息
        SET: server_id & user_id - [ product_id & order_number ]
        """
        key = "&".join(map(str, [server_id, user_id]))
        result = []
        members = self.redis.client.smembers(key)
        for m in members:
            result.append(m.split('&'))
        return result


    def finish_set(self, server_id, user_id, orders):
        """完成订单
        """
        key = "&".join(map(str, [server_id, user_id]))
        count = len(orders)
        pipeline = self.redis.client.pipeline()
        for (pid, onum) in orders:
            pipeline.srem(key, "&".join([pid, onum]))
        res = pipeline.execute()

        result = True
        for index, r in enumerate(res):
            if r != 1:
                logger.warning("Delete order no failed[server_id=%d][user_id=%d][order=%s]" %
                        (server_id, user_id, orders[index]))
                result = False

        return result


class PayLogic(object):
    """充值过程逻辑
    """
    __metaclass__ = Singleton

    PLATFORM_ALIPAY = 1   #支付宝
    PLATFORM_QIHOO = 2    #奇虎360
    PLATFORM_ANYSDK = 3   #ANYSDK
    PLATFORM_SOHA = 4     #SOHA
    PLATFORM_LUNPLAY = 5  #LUNPLAY
    PLATFORM_PYW = 6      #PYW(朋友玩)
    PLATFORM_ANQU = 7     #ANQU(安趣)
    PLATFORM_185SY = 8    #185SY
    PLATFORM_456SY = 9    #456SY(骑士助手)
    PLATFORM_ALI = 10     #阿里游戏
    PLATFORM_YYB = 11     #应用宝
    PLATFORM_APPSTORE = 12     #app store
    PLATFORM_YIJIE = 13        #易接
    PLATFORM_ZHANGLING = 14    #掌灵H5
    PLATFORM_QUICK = 15        #Quick
    PLATFORM_SY39 = 16         #三九互娱
    PLATFORM_ZYF = 17          #掌宜付
    PLATFORM_SY94WAN = 18        #94玩
    PLATFORM_FINGER = 19         #指尖
    PLATFORM_MIYU = 20           #米娱
    PLATFORM_ASDK = 21           #asdk
    PLATFORM_ONESTORE = 23       #onestore
    PLATFORM_GOOGLE = 24         #google



    def init_pay(self, conf_path):
        """初始化支付信息
        """
        self._init_runtime_info()
        self._init_pay_logic(conf_path)


    def _init_runtime_info(self):
        """获取本机 ip、进程 id
        """
        #获取本机电脑名
        myname = socket.getfqdn(socket.gethostname())
        #获取本机ip
        myaddr = socket.gethostbyname(myname)
        self.ip = myaddr

        #获取进程 id
        self.pid = os.getpid()


    def _init_pay_logic(self, conf_path):
        """初始化各个不同的支付过程逻辑
        """
        self._logics = {}

        config = json.load(open(conf_path, 'r'))
        self.is_sandbox = config.get("sandbox")
        self.enable_multi_count = config.get("enable_multi_count")

        platform_conf = config.get("platform")
        for pname in platform_conf:
            # if pname == "alipay":
            #     logic = PayLogicAlipay()
            #     logic.init_info(platform_conf[pname])
            #     self._logics[self.PLATFORM_ALIPAY] = logic
            # elif pname == "qihoo":
            #     logic = PayLogicQihoo()
            #     logic.init_info(platform_conf[pname])
            #     self._logics[self.PLATFORM_QIHOO] = logic

            #暂时仅支持 anysdk 和 soha
            if pname == "anysdk":
                logic = PayLogicAnySDK()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ANYSDK] = logic
            elif pname == "soha":
                logic = PayLogicSoha()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_SOHA] = logic
            elif pname == "lunplay":
                logic = PayLogicLunplay()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_LUNPLAY] = logic
            elif pname == "pyw":
                logic = PayLogicPyw()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_PYW] = logic
            elif pname == "anqu":
                logic = PayLogicAnqu()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ANQU] = logic
            elif pname == "185sy":
                logic = PayLogic185sy()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_185SY] = logic
            elif pname == "456sy":
                logic = PayLogic456sy()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_456SY] = logic
            elif pname == "ali":
                logic = PayLogicAli()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ALI] = logic
            elif pname == "yyb":
                logic = PayLogicYyb()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_YYB] = logic
            elif pname == "appstore":
                logic = PayLogicAppStore()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_APPSTORE] = logic
            elif pname == "yijie":
                logic = PayLogicYijie()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_YIJIE] = logic
            elif pname == "zhangling":
                logic = PayLogicZhangling()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ZHANGLING] = logic
            elif pname == "quick":
                logic = PayLogicQuick()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_QUICK] = logic
            elif pname == "sy39":
                logic = PayLogicSY39()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_SY39] = logic
            elif pname == "zyf":
                logic = PayLogicZYF()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ZYF] = logic
            elif pname == "sy94wan":
                logic = PayLogicSY94Wan()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_SY94WAN] = logic
            elif pname == "finger":
                logic = PayLogicFinger()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_FINGER] = logic
            elif pname == "miyu":
                logic = PayLogicMiyu()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_MIYU] = logic
            elif pname == "asdk":
                logic = PayLogicASDK()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ASDK] = logic
            elif pname == "onestore":
                logic = PayLogicOnestore()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_ONESTORE] = logic
            elif pname == "google":
                logic = PayLogicGoogle()
                logic.init_info(platform_conf[pname], self.is_sandbox)
                self._logics[self.PLATFORM_GOOGLE] = logic


    def _get_server_id(self):
        """获取 server id
        """
        if self.is_sandbox:
            server_id = 999#ios iap 沙盒环境服务器 id
        else:
            server_id = GlobalObject().server_id
        return server_id


    ORDER_NUMBER_LENGTH_MAX = 32
    ORDER_NUMBER_SIGN_LENGHT = 22
    def _calc_order_number(self, user_id, pay_id, now):
        """生成订单编号（历史上唯一）
        string 32位
        pay_id - sign(user_id + time + server_id + pid + random)
        """
        message = "[user_id=%d][time=%d][server_id=%d][pid=%d][random=%s]" % (
                user_id, now, self._get_server_id(), self.pid, utils.random_salt())

        hash_message = utils.sha256_hash(message)
        hex_message = utils.hex_byte(hash_message)
        hex_message = hex_message[:self.ORDER_NUMBER_SIGN_LENGHT]

        number = "%d-%s" % (pay_id, hex_message)
        if len(number) > self.ORDER_NUMBER_LENGTH_MAX:
            raise Exception("Calc order number failed")

        return number


    def calc_order_info(self, user_id, platform, pay_id, now, value):
        """计算支付信息
        Args:
            user_id[int]: 玩家 id
            platform[int]: 平台 id
            pay_id[int]: 商品 id
            now[int]: 当前时间戳
            value[string]: 有些平台在发起支付时需要传一些参数
        Returns:
            info[string]: 订单信息，提供给客户端支付使用
            order_number[string]: 全局唯一订单号
            order[dict]: 商品信息
        """
        if platform not in self._logics:
            raise Exception("Unexpect platform[platform=%d]" % platform)

        order = PayPool().get(pay_id)
        server_id = self._get_server_id()

        #生成订单号
        order_number = self._calc_order_number(user_id, pay_id, now)

        info = self._logics[platform].calc_order_info(
                user_id, server_id, order, order_number, now, value)
        return (info, order_number, order)


    def check_order_reply(self, user_id, platform, order_number, reply, now, server_id = 0):
        """检查支付响应
        Args:
            user_id[int]: 玩家 id
            platform[int]: 平台 id
            order_number[string]: 全局唯一订单号
            reply[string]: 客户端响应信息
            now[int]: 当前时间戳
        Returns:
            orders: list(order), 完成支付的商品信息列表
            None: 失败
        """
        if platform not in self._logics:
            raise Exception("Unexpect platform[platform=%d]" % platform)

        if server_id == 0:
            server_id = self._get_server_id()

        info = self._logics[platform].check_order_reply(
                user_id, server_id, reply, order_number, now)
        if info is None:
            return None

        if isinstance(info, list):
            return info
        else:
            return [info]


class PayLogicAnySDK(object):
    """AnySDK 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 anysdk 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.enable_amount_check = config.get("enable_amount_check")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照AnySDK API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_name":order.subject.encode("utf-8"),
                "product_price":price / order.productCount,
                "product_count":order.productCount,
                "coin_name":"元宝",
                "coin_rate":10,#RMB 和元宝的兑换比例
                "server_id":server_id,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 AnySDK 的充值响应，检查 Pay Redis（由 AnySDK-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        orders = []
        
        #先检查有没有其他的充值（通过redis set方式存储，目前只用于客服补发接口）
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) != 0:
            logger.notice("Anysdk pay set info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            
            for (product_id, pay_order_number) in infos:
                o = PayPool().get_by_product_id(product_id)
                if o is None:
                    logger.warning("Order not found[product_id=%s]" % product_id)
                    continue
                    
                ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
                if product_id == ADD_GOLD_PRODUCT_ID:
                    str_list = pay_order_number.split('_')
                    vip = str_list[0]
                    gold = str_list[1]
                    
                    o.gold = gold
                    if vip == "1":  
                        #vip = 1不加vip经验
                        #vip = 2 加vip经验
                        o.truePrice = 0
                    else:
                        o.truePrice = int(gold) / int(float(
                                data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))
                
                    orders.append((o, pay_order_number))

            #完成购买
            if PayRedisAgent().finish_set(server_id, user_id, infos):
                for (product_id, pay_order_number) in infos:
                    logger.notice("Finish order[server_id=%d][user_id=%d]"
                            "[product_id=%s][order_number=%s]" % (
                            server_id, user_id, product_id, pay_order_number))

        #根据 order_number 检查充值是否完成
        ret = PayRedisAgent().get(order_number)
        if ret is None:
            logger.warning("Pay order number not valid, no notify[order_number=%s]" %
                    order_number)
            return orders

        #从order_number中截取order_id
        order_id = (order_number.split('-', 1))[0]
        [pay_server_id, pay_user_id, pay_product_id, pay_amount] = ret

        #获取商品信息
        order = PayPool().get_by_product_id(pay_product_id, order_id)
        if order is None:
            logger.warning("Order not found[product_id=%s][order_id=%s]" % (pay_product_id, order_id))
            return orders

        amount = int(order.truePrice)

        #检查用户 id，服务器 id，商品价格
        if (str(user_id) == pay_user_id and
                str(server_id) == pay_server_id and
                str(amount) == pay_amount if self.enable_amount_check else True):
            if PayRedisAgent().finish(order_number):
                logger.notice("Check and finish order[order_number=%s][user_id=%d]"
                        "[server_id=%d][pay_id=%d]" % (
                    order_number, user_id, server_id, order.id))
                orders.append((order, order_number))
                return orders
        else:
            logger.warning("Check order failed"
                    "[user_id=%s][server_id=%s][product_id=%s][amount=%s]"
                    "[real user_id=%d][real server_id=%d][real pay id=%d][real amount=%d]" %
                    (pay_user_id, pay_server_id, pay_product_id, pay_amount,
                        user_id, server_id, order.id, amount))

        return orders


class PayLogicLunplay(object):
    """AnySDK 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 anysdk 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.enable_amount_check = config.get("enable_amount_check")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_count":order.productCount,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 lunplay 的充值响应，检查 Pay Redis（由 lunplay-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过lunplay product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None



class PayLogicSoha(object):
    """Soha 充值过程
    """
    def init_info(self, config, is_sandbox):
        """获取 soha 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, id_3rd):
        """计算支付信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        info = {
                "card":order.cardType != 0,
                "product_count":order.productCount,
                "ext":order_number
                }
        info = json.dumps(info)
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 Soha 的充值响应，检查 Pay Redis（由 Soha-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            (order, order_number): 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过soha product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None


class PayLogicAlipay(object):
    """支付宝充值过程
    直接接入支付宝
    """
    def init_info(self, config):
        """获取支付宝支付配置
        """
        self.region = int(config.get("region"))
        self.partner_id = config.get("partner_id").encode("utf-8")
        self.seller_id = config.get("seller_id").encode("utf-8")
        self.notify_url = config.get("notify_url").encode("utf-8")
        self.private_key = utils.rsa_importkey(config.get("private_key"))
        self.ali_public_key = utils.rsa_importkey(config.get("ali_public_key"))


    def calc_order_info(self, user_id, pay_id, now):
        """计算支付信息
        按照支付宝 API 要求的格式
        Returns:
            (info, order_number)
        """
        order = data_loader.PayBasicInfo_dict[pay_id]

        order_no = self._calc_order_number(user_id, pay_id, now)
        subject = order.subject.encode("utf-8")
        body = order.body.encode("utf-8")

        info = ("partner=\"{0}\""
                "&seller_id=\"{1}\""
                "&out_trade_no=\"{2}\""
                "&subject=\"{3}\""
                "&body=\"{4}\""
                "&total_fee=\"{5:.2f}\""
                "&notify_url=\"{6}\""
                "&service=\"mobile.securitypay.pay\""
                "&payment_type=\"1\""
                "&_input_charset=\"utf-8\"".format(
                    self.partner_id, self.seller_id, order_no,
                    subject, body, order.truePrice, self.notify_url))

        sign = utils.rsa_sign(info, self.private_key)
        encode = urlencode({"s": sign})
        sign = encode[len('s='):]
        info += "&sign=\"%s\"&sign_type=\"RSA\"" % sign

        logger.notice("Generate order info"
                "[user id=%d][pay id=%d][order no=%s][now=%d]"
                "[region=%d][pid=%d][info=%s]" %
                (user_id, pay_id, order_no, now, self.region, self.pid, info))
        return (info, order_no)


    def check_order_reply(self, user_id, reply, pay_id, order_number, now):
        """检查支付宝的同步响应，从客户端传来
        Returns:
            None: 失败
            product_id: 用户购买的商品 id
        """
        check_return_status = False
        check_sign = False
        check_success = False
        check_order_number = False

        fields = reply.split(';')
        for field in fields:

            # resultStatus 等于 9000 表示支付成功
            # https://doc.open.alipay.com/doc2/detail?treeId=59&articleId=103671&docType=1
            if field.startswith("resultStatus="):
                ret = field[len("resultStatus={"):]
                ret = ret[:len(ret)-len("}")]
                if ret == "9000":
                    check_return_status = True
                else:
                    logger.warning("Pay replay resutl status error[status=%s]" % ret)
                    return None

            elif field.startswith("result="):
                field = field[len("result={"):]
                field = field[:len(field)-len("}")]
                args = field.split('&')

                for argument in args:
                    if argument.startswith("sign="):
                        sign = argument[len("sign=\""):]
                        sign = sign[:len(sign)-len("\"")]
                        logger.debug("sign after:%s" % sign)

                    elif argument.startswith("success="):
                        success = argument[len("success=\""):]
                        success = success[:len(success)-len("\"")]
                        if success == "true":
                            check_success = True
                        else:
                            logger.warning("Pay replay argument error[%s]" % argument)
                            return None

                    elif argument.startswith("out_trade_no="):
                        order_no = argument[len("out_trade_no=\""):]
                        order_no = order_no[:len(order_no)-len("\"")]
                        if order_no == order_number:
                            check_order_number = True
                        else:
                            logger.warning("Pay reply argument error[%s]" % order_no)
                            return None

                #除去 sign, sign_type 字段
                index = min(field.rfind("&sign="), field.rfind("&sign_type="))
                raw_string = field[:index]

                #检查签名
                if utils.rsa_verify(raw_string, sign, self.ali_public_key):
                    check_sign = True
                else:
                    logger.warning("Pay replay check error")
                    return None

        if not check_return_status:
            logger.warning("Pay replay return status miss")
            return None

        if not check_sign:
            logger.warning("Pay replay sign miss")
            return None

        if not check_success:
            logger.warning("Pay replay success miss")
            return None

        if not check_order_number:
            logger.warning("Pay replay order number miss")
            return None

        logger.notice("Check pay reply ok"
                "[user id=%d][order no=%s][now=%d]"
                "[region=%d][pid=%d][reply=%s]" %
                (user_id, order_number, now, self.region, self.pid, reply))
        return pay_id


class PayLogicQihoo(object):
    """奇虎360充值过程
    直接接入360平台
    """

    def init_info(self, config):
        """获取奇虎360支付配置
        """
        self.notify_url = config.get("notify_url").encode("utf-8")


    def calc_order_info(self, user_id, pay_id, now):
        """计算支付信息
        按照360 API 要求的格式
        Returns:
            (info, order_number)
        """
        order = data_loader.PayBasicInfo_dict[pay_id]

        order_no = self._calc_order_number(user_id, pay_id, now)

        amount = int(order.truePrice * 100)#单位为分，且消费金额只支持整数元
        assert amount % 100 == 0
        rate = 10 #RMB 和元宝的兑换比例

        info = {"amount":amount,
                "rate":rate,
                "product_name":order.subject.encode("utf-8"),
                "product_id":pay_id,
                "product_count":order.productCount,
                "notify_uri":self.notify_url,
                "app_name":u"再无三国".encode("utf-8"),
                "app_user_id":user_id,
                "order_id":order_no,
                "ext":order_number}
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user id=%d][pay id=%d][order no=%s][now=%d]"
                "[region=%d][pid=%d][info=%s]" %
                (user_id, pay_id, order_no, now, self.region, self.pid, info))
        return (info, order_no)


    def check_order_reply(self, user_id, reply, pay_id, order_number, now):
        """检查360的同步响应，从客户端传来
        Returns:
            None: 失败
            product_id: 用户购买的商品 id
        """
        if reply == "success":
            return pay_id
        else:
            return None


class PayLogicPyw(object):
    """Pyw 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 pyw 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照pyw API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_name":order.subject.encode("utf-8"),
                "product_price":price,
                "product_count":order.productCount,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 pyw 的充值响应，检查 Pay Redis（由 Pyw-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #根据 order_number 检查充值是否完成
        ret = PayRedisAgent().get(order_number)
        if ret is None:
            logger.warning("Pay order number not valid, no notify[order_number=%s]" %
                    order_number)
            return None

        #从order_number中截取order_id
        order_id = (order_number.split('-', 1))[0]
        [pay_server_id, pay_user_id, pay_product_id, pay_amount] = ret

        #获取商品信息
        order = PayPool().get_by_product_id(pay_product_id, order_id)
        if order is None:
            logger.warning("Order not found[product_id=%s][order_id=%s]" % (pay_product_id, order_id))
            return None

        amount = int(order.truePrice)

        #检查用户 id，服务器 id，商品价格
        if (str(user_id) == pay_user_id and
                str(server_id) == pay_server_id and
                str(amount) == pay_amount):
            if PayRedisAgent().finish(order_number):
                logger.notice("Check and finish order[order_number=%s][user_id=%d]"
                        "[server_id=%d][pay_id=%d]" % (
                    order_number, user_id, server_id, order.id))
                return (order, order_number)
        else:
            logger.warning("Check order failed"
                    "[user_id=%s][server_id=%s][product_id=%s][amount=%s]"
                    "[real user_id=%d][real server_id=%d][real pay id=%d][real amount=%d]" %
                    (pay_user_id, pay_server_id, pay_product_id, pay_amount,
                        user_id, server_id, order.id, amount))

        return None


class PayLogicAnqu(object):
    """Anqu 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 anqu 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照anqu API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_name":order.subject.encode("utf-8"),
                "product_description":order.body.encode("utf-8"),
                "product_price":price,
                "product_count":order.productCount,
                "order_number":order_number,
                "server_id":server_id,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 anqu 的充值响应，检查 Pay Redis（由 Anqu-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #根据 order_number 检查充值是否完成
        ret = PayRedisAgent().get(order_number)
        if ret is None:
            logger.warning("Pay order number not valid, no notify[order_number=%s]" %
                    order_number)
            return None

        #从order_number中截取order_id
        order_id = (order_number.split('-', 1))[0]
        [pay_server_id, pay_user_id, pay_product_id, pay_amount] = ret

        #获取商品信息
        order = PayPool().get_by_product_id(pay_product_id, order_id)
        if order is None:
            logger.warning("Order not found[product_id=%s][order_id=%s]" % (pay_product_id, order_id))
            return None

        amount = int(order.truePrice)

        #检查用户 id，服务器 id，商品价格
        if (str(user_id) == pay_user_id and
                str(server_id) == pay_server_id and
                str(amount) == pay_amount):
            if PayRedisAgent().finish(order_number):
                logger.notice("Check and finish order[order_number=%s][user_id=%d]"
                        "[server_id=%d][pay_id=%d]" % (
                    order_number, user_id, server_id, order.id))
                return (order, order_number)
        else:
            logger.warning("Check order failed"
                    "[user_id=%s][server_id=%s][product_id=%s][amount=%s]"
                    "[real user_id=%d][real server_id=%d][real pay id=%d][real amount=%d]" %
                    (pay_user_id, pay_server_id, pay_product_id, pay_amount,
                        user_id, server_id, order.id, amount))

        return None


class PayLogic185sy(object):
    """185sy 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 185sy 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照185sy API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "server_id":server_id,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 185sy 的充值响应，检查 Pay Redis（由 185sy-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过185sy product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)

            ADD_GOLD_PRODUCT_ID = "com.185sy.fhsgApp.msws99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]

                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / 300

            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None


class PayLogic456sy(object):
    """456sy 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 456sy 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照456sy API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        info = {
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "server_id":server_id,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 456sy 的充值响应，检查 Pay Redis（由 456sy-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过456sy product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)

            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None


class PayLogicAli(object):
    """Ali 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 ali 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.notify_url = config.get("notify_url").encode("utf-8")
        self.api_key = config.get("api_key").encode("utf-8")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照ali API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        #签名
        sign_content = "accountId=" + id_3rd + "amount=" + str(price) + ".00callbackInfo=userId=" +\
                str(user_id) + "#productId=" + product_id + "#servId=" + str(server_id) + "#time=" +\
                str(timestamp) + "cpOrderId=" + order_number + "notifyUrl=" + self.notify_url +\
                self.api_key
        md5 = utils.md5_hash(sign_content)
        logger.debug("sign_content=%s md5=%s" % (sign_content, md5))

        info = {
                "time":timestamp,
                "server_id":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "order_number":order_number,
                "notifyUrl":self.notify_url,
                "signType":"MD5",
                "sign":md5,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 ali 的充值响应，检查 Pay Redis（由 Pyw-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)

            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None


class PayLogicYyb(object):
    """应用宝 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 yyb 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        按照ali API 要求的格式生成订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 ali 的充值响应，检查 Pay Redis（由 Pyw-server 的异步通知更新）
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)

            orders.append((o, order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, order_number))

            return orders

        return None



class PayLogicAppStore(object):
    """苹果商店充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 appstore 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 appstore 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicYijie(object):
    """苹果商店充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 yijie 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 appstore 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            infos = PayRedisAgent().get_set(server_id, user_id % (server_id*10000000)) #应用宝不知为何出现短id，临时处理
            if len(infos) == 0:
                logger.warning("No pay info[server_id=%d][user_id=%d]" %
                        (server_id, user_id))
                return None

        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders
        elif PayRedisAgent().finish_set(server_id, user_id % (server_id*10000000), infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))
                        
            return orders

        return None


class PayLogicZhangling(object):
    """掌灵充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 zhangling 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.app_id = config.get("app_id").encode("utf-8")
        self.app_key = config.get("app_key").encode("utf-8")
        self.notify_url = config.get("notify_url").encode("utf-8")
        self.key_file_name = config.get("zhangling_public_key")
        self.zhangling_public_key = utils.rsa_importkey(config.get("zhangling_public_key"))


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        ip = value
        timestamp = int(time.time())

        #先md5签名，再rsa签名（放在服务器做）
        #md5
        md5_source = ("amount=%d00"
                      "&appid=%s"
                      "&clientIp=%s"
                      "&mchntOrderNo=%s"
                      "&notifyUrl=%s"
                      "&subject=%s"
                      "&version=h5_NoEncrypt"
                      "&key=%s"
                      % (price, self.app_id, ip, 
                          order_number, self.notify_url, 
                          order.subject.encode("utf-8"), 
                          self.app_key))
        logger.debug("md5_source=%s" % md5_source)
        md5_str = utils.md5_hash(md5_source)
        logger.debug("md5_sign=%s" % md5_str)
        #rsa
        info = ("{\"amount\":\"%d00\""
                ",\"appid\":\"%s\""
                ",\"clientIp\":\"%s\""
                ",\"mchntOrderNo\":\"%s\""
                ",\"notifyUrl\":\"%s\""
                ",\"subject\":\"%s\""
                ",\"version\":\"h5_NoEncrypt\""
                ",\"signature\":\"%s\"}"
                % (price, self.app_id, ip,
                    order_number, self.notify_url, 
                    order.subject.encode("utf-8"),
                    self.app_key))
        logger.debug("rsa_source=%s" % info)
        #sign = utils.rsa_sign(info, self.zhangling_public_key)
        sign = utils.rsa_encrypt(info, self.key_file_name, 117)
        logger.debug("rsa_sign=%s" % sign)

        info = {
                "time":timestamp,
                "server_id":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "order_number":order_number,
                "notifyUrl":self.notify_url,
                "orderInfo":sign,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 appstore 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicQuick(object):
    """quick充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 quick 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.titleKey,
                "product_description":order.descKey,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 quick 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicSY39(object):
    """sy39 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 sy39 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.titleKey,
                "product_description":order.descKey,
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 quick 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicZYF(object):
    """zyf 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 zyf 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "order_number":(order_number + "_" + str(user_id) + "_" + str(server_id) + "_" + product_id),
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 zyf 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicSY94Wan(object):
    """sy94wan 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 sy94wan 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 zyf 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicFinger(object):
    """finger北京指尖 充值过程
    """

    def init_info(self, config, is_sandbox):
        """获取 sy94wan 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.notify_url = config.get("notify_url").encode("utf-8")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "order_number":order_number,
                "notifyUrl":self.notify_url,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 zyf 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicMiyu(object):
    """Miyu
    """

    def init_info(self, config, is_sandbox):
        """获取 miyu 的支付配置
        """
        self.is_sandbox = is_sandbox


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "product_description":order.subject.encode("utf-8"),
                "order_number":order_number,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 zyf 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicASDK(object):
    """asdk
    """

    def init_info(self, config, is_sandbox):
        """获取 asdk 的支付配置
        """
        self.is_sandbox = is_sandbox
        self.notify_url = config.get("notify_url").encode("utf-8")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId
        pay_id = order.id

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "pay_id":pay_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "product_description":order.descKey.encode("utf-8"),
                "order_number":order_number,
                "notifyUrl":self.notify_url,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 zyf 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    o.truePrice = int(gold) / int(float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicOnestore(object):
    """韩国onestore
    """

    def init_info(self, config, is_sandbox):
        """获取 onestore 的支付配置
        """
        self.is_sandbox = is_sandbox
        #self.notify_url = config.get("notify_url").encode("utf-8")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId
        pay_id = order.id

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "pay_id":pay_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "product_description":order.descKey.encode("utf-8"),
                "order_number":order_number,
                #"notifyUrl":self.notify_url,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 onestore 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    gold2price = {}
                    gold2price[60] = 1100
                    gold2price[300] = 5500
                    gold2price[600] = 11000
                    gold2price[1800] = 33000
                    gold2price[3000] = 55000
                    gold2price[6000] = 110000
                    gold2price[300] = 4400
                    gold2price[700] = 12100

                    if gold2price.has_key(int(gold)):
                        o.truePrice = gold2price[int(gold)]
                    else:
                        o.truePrice = int(int(gold) / float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value))

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


class PayLogicGoogle(object):
    """google
    """

    def init_info(self, config, is_sandbox):
        """获取 google 的支付配置
        """
        self.is_sandbox = is_sandbox
        #self.notify_url = config.get("notify_url").encode("utf-8")


    def calc_order_info(self, user_id, server_id, order, order_number, now, value):
        """支付前，计算支付订单信息
        Args:
            user_id[int]: 玩家 id
            server_id[int]: 服务器 id
            order[object]: 商品信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            info: 支付订单信息
        """
        price = int(order.truePrice)
        product_id = order.productId
        pay_id = order.id

        id_3rd = value
        timestamp = int(time.time())

        info = {
                "time":timestamp,
                "server_id":server_id,
                "server_name":server_id,
                "pay_id":pay_id,
                "product_id":product_id,
                "product_price":price,
                "product_count":order.productCount,
                "product_name":order.subject.encode("utf-8"),
                "product_description":order.descKey.encode("utf-8"),
                "order_number":order_number,
                #"notifyUrl":self.notify_url,
                "ext":order_number
                }
        info = json.dumps(info)

        logger.notice("Generate order info"
                "[user_id=%d][pay_id=%d][order_no=%s][now=%d]"
                "[server_id=%d][product_id=%s][info=%s]" %
                (user_id, order.id, order_number, now, server_id, product_id, info))
        return info


    def check_order_reply(self, user_id, server_id, reply, order_number, now):
        """支付完成后，
        检查 google 的充值响应，检查 Pay Redis
        Args:
            user_id[int]: 玩家 id
            reply[string]: 客户端响应信息
            order_number[string]: 全局唯一订单号
            now[int]: 当前时间戳
        Returns:
            None: 失败
            order: 用户购买的商品信息
        """
        #获取所有完成订单
        infos = PayRedisAgent().get_set(server_id, user_id)
        if len(infos) == 0:
            logger.warning("No pay info[server_id=%d][user_id=%d]" %
                    (server_id, user_id))
            return None

        #通过product id, 映射到商品信息
        orders = []
        for (product_id, pay_order_number) in infos:
            o = PayPool().get_by_product_id(product_id)
            if o is None:
                logger.warning("Order not found[product_id=%s]" % product_id)
                continue

            ADD_GOLD_PRODUCT_ID = "com.anqu.zwsgApp.zwsg99999999"  #特殊的product id
            if product_id == ADD_GOLD_PRODUCT_ID:
                str_list = pay_order_number.split('_')
                vip = str_list[0]
                gold = str_list[1]
                
                o.gold = gold
                if vip == "1":  
                    #vip = 1不加vip经验
                    #vip = 2 加vip经验
                    o.truePrice = 0
                else:
                    gold2price = {}
                    gold2price[60] = 1100
                    gold2price[300] = 5500
                    gold2price[600] = 11000
                    gold2price[1800] = 33000
                    gold2price[3000] = 55000
                    gold2price[6000] = 110000
                    gold2price[300] = 4400
                    gold2price[700] = 12100

                    if gold2price.has_key(int(gold)):
                        o.truePrice = gold2price[int(gold)]
                    else:
                        o.truePrice = int(int(gold) / float(
                            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value)) 

            orders.append((o, pay_order_number))

        #完成购买
        if PayRedisAgent().finish_set(server_id, user_id, infos):
            for (product_id, pay_order_number) in infos:
                logger.notice("Finish order[server_id=%d][user_id=%d]"
                        "[product_id=%s][order_number=%s]" % (
                    server_id, user_id, product_id, pay_order_number))

            return orders

        return None


