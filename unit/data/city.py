#coding:utf8
"""
Created on 2016-05-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnitCityInfo(object):
    """史实城信息
    """

    __slots__ = [
            "id",
            "slogan",
            "slogan_update_num",
            "tax",
            "tax_update_num",
            "tax_income",
            "income_collect_time",
            ]

    def __init__(self):
        self.id = 0
        self.slogan = ''
        self.slogan_update_num = 0
        self.tax = 0
        self.tax_update_num = 0
        self.tax_income = 0
        self.income_collect_time = 0

    @staticmethod
    def create(city_id):
        """新建一个史实城
        """
        city = UnitCityInfo()
        city.id = city_id
        city.slogan_update_num = 0
        city.tax_update_num = 0
        city.reset_slogan()
        city.reset_tax(False)
        city.reset_income(0)
        return city


    def reset_slogan(self):
        """重置 slogan
        """
        self.change_slogan(
                data_loader.LegendCityBasicInfo_dict[self.id].defaultSlogan.encode("utf-8"),
                force = True)
        self.slogan_update_num = 0


    def reset_tax(self, keep = True):
        """重置 tax
        """
        if not keep:
            self.change_tax(
                    data_loader.LegendCityBasicInfo_dict[self.id].defaultTax,
                    force = True)
        self.tax_update_num = 0


    def change_slogan(self, content, gold = 0, force = False):
        """更换宣言
            content[string]: 宣言
            gold[int]: 消耗元宝数
            force[bool]: 是否强制更新（不消耗元宝）
        """
        if not isinstance(content, str):
            logger.warning("Invalid type")
            return False

        if content == "":
            logger.warning("Slogan is empty")
            return False

        if not force and self.slogan_update_num > 0:
            need = int(float(
                data_loader.MapConfInfo_dict["legendcity_update_slogan_cost"].value))
            if gold != need:
                logger.warning("Change slogan gold error[need=%d][cost=%d]" %
                        (need, gold))
                return False

        #用 base64 编码存储，避免一些非法字符造成的问题
        self.slogan = base64.b64encode(content)
        self.slogan_update_num += 1
        return True


    def get_readable_slogan(self):
        return base64.b64decode(self.slogan)


    def is_change_slogan_free(self):
        return self.slogan_update_num == 0


    def change_tax(self, value, gold = 0, force = False):
        """设置商品税
        Argas:
            value[int]: [0-100], 百分比
            gold[int]: 消耗元宝数
            force[bool]: 是否强制更新（不消耗元宝）
        """
        assert value >= 0 and value <= 100

        if not force and self.tax_update_num > 0:
            need = int(float(
                data_loader.MapConfInfo_dict["legendcity_update_tax_cost"].value))
            if gold != need:
                logger.warning("Change tax gold error[need=%d][cost=%d]" %
                        (need, gold))
                return False

        self.tax = int(value)
        self.tax_update_num += 1
        return True


    def is_change_tax_free(self):
        return self.tax_update_num == 0


    def gain_tax_income(self, value):
        """
        """
        assert value >= 0
        self.tax_income += value
        logger.debug("Gain tax income[add=%d][remain=%d]" % (value, self.tax_income))


    def reset_income(self, now):
        self.tax_income = 0
        self.income_collect_time = now


    def add_income(self, value):
        assert value >= 0
        self.tax_income += value


    def is_able_to_calc_income(self, now):
        return not utils.is_same_day(self.income_collect_time, now)


