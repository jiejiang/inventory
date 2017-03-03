#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cStringIO

__author__ = 'jie'

import re
import sys
import os
import shutil
import zipfile
import codecs
import datetime
import string
import random
from optparse import OptionParser
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from weasyprint import HTML, CSS
from wand.image import Image
from PyPDF2 import PdfFileMerger, PdfFileReader
from sqlalchemy import desc, asc, Index, UniqueConstraint, and_

from ..models import City, Order, ProductInfo
from .. import db
from ..util import time_to_filename

Code128 = barcode.get_barcode_class('code128')

PROVINCE_INFO_MAP = {
    u"湖南": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"广西": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"海南": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"江西": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"福建": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"湖北": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"江苏": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"上海": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"浙江": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"河北": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"安徽": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"河南": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"山东": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"山西": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"陕西": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"贵州": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"云南": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"重庆": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"四川": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"北京": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"天津": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"辽宁": {'ticket_initial': 9, 'package_type': u"快递包裹"},
    u"黑龙江": {'ticket_initial': 9, 'package_type': u"快递包裹"},

    u"广东": {'ticket_initial': 1, 'package_type': u"标准快递"},

    u"内蒙古": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"甘肃": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"青海": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"宁夏": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"吉林": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"西藏": {'ticket_initial': 1, 'package_type': u"标准快递"},
    u"新疆": {'ticket_initial': 1, 'package_type': u"标准快递"},
}

ITEM_NAME_RE = re.compile(
    ur"^.*?((([123一二三])|([4四]))段|(\d+)g)$", flags=re.U | re.I)

ITEM_NAME_MAP_INFO = {
    u"爱他美1段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 89.06,
        "full_name": u"爱他美奶粉1段900g",
    },
    u"爱他美2段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 89.06,
        "full_name": u"爱他美奶粉2段900g",
    },
    u"爱他美3段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 89.06,
        "full_name": u"爱他美奶粉3段900g",
    },
    u"爱他美4段": {
        "net_weight": 0.8,
        "gross_weights": {
            4: 3.90,
            6: 6,
        },
        "price_per_kg": 86.50,
        "full_name": u"爱他美奶粉4段800g",
    },
    u"牛栏1段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 89.06,
        "full_name": u"牛栏奶粉1段900g",
    },
    u"牛栏2段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 86.50,
        "full_name": u"牛栏奶粉2段900g",
    },
    u"牛栏3段": {
        "net_weight": 0.9,
        "gross_weights": {
            4: 4.35,
            6: 7,
        },
        "price_per_kg": 86.50,
        "full_name": u"牛栏奶粉3段900g",
    },
    u"牛栏4段": {
        "net_weight": 0.8,
        "gross_weights": {
            4: 3.90,
            6: 6,
        },
        "price_per_kg": 94.30,
        "full_name": u"牛栏奶粉4段800g",
    },
}


def calculate_item_info(n_row, item_name, item_count):
    item_name = "".join(item_name.strip().split()).decode("utf8")
    if not item_name in ITEM_NAME_MAP_INFO:
        raise Exception, u"第%d行包含未注册商品名称: %s" % (n_row + 1, item_name)
    info = ITEM_NAME_MAP_INFO[item_name]
    if not item_count in info["gross_weights"]:
        raise Exception, u"第%d行商品[%s]包含未注册数量:%d" % (
            n_row + 1, item_name, item_count)
    return info["net_weight"] * item_count * info["price_per_kg"], info["net_weight"] * item_count, \
        info["gross_weights"][item_count], info["price_per_kg"], \
        info["full_name"] if "full_name" in info else item_name


def calculate_item_info_from_db(n_row, item_name, item_count):
    item_name = "".join(item_name.strip().split()).decode("utf8")
    search_result = ProductInfo.find_product_and_weight(item_name, item_count)
    if not search_result:
        raise Exception, u"第%d行包含未注册商品名称和箱件数 %s[%d件]" % (
            n_row + 1, item_name, item_count)
    product_info, gross_weight_per_box = search_result
    return product_info.net_weight * item_count * product_info.price_per_kg, product_info.net_weight * item_count, \
        gross_weight_per_box, product_info.price_per_kg, \
        product_info.full_name if product_info.full_name else item_name


def calculate_item_info_from_db_without_product_info(n_row, item_name, item_count):
    item_name = "".join(item_name.strip().split()).decode("utf8")
    product_info = ProductInfo.query.filter(and_(ProductInfo.name==item_name, ProductInfo.deprecated==False)).first()
    if not product_info:
        raise Exception, u"第%d行包含未注册商品: %s" % (n_row + 1, item_name)

    # from sqlalchemy import inspect
    # for c in inspect(product_info).mapper.column_attrs:
    #     print c.key, getattr(product_info, c.key)
    if product_info.unit_price is None or product_info.gross_weight is None or product_info.unit_per_item is None \
            or product_info.tax_code is None or product_info.billing_unit is None \
            or product_info.billing_unit_code is None or product_info.specification is None:
        raise Exception, u"第%d行商品 [%s] 注册信息不完整" % (n_row + 1, item_name)

    return product_info.unit_price * product_info.unit_per_item * item_count, product_info.net_weight * item_count, \
        product_info.gross_weight * item_count, product_info.unit_price, \
        product_info.full_name if product_info.full_name else item_name, \
        product_info.net_weight, product_info.tax_code, product_info.billing_unit, product_info.billing_unit_code, \
        product_info.unit_per_item, product_info.specification


class NoTextImageWriter(ImageWriter):

    def __init__(self):
        super(NoTextImageWriter, self).__init__()

    def _paint_text(self, xpos, ypos):
        pass


def generate_pdf(ticket_number, filename, context, tmpdir):
    bot_image = os.path.join(tmpdir, 'bot_barcode_trim.png')
    top_image = os.path.join(tmpdir, 'top_barcode_trim.png')
    if os.path.exists(bot_image):
        os.remove(bot_image)
    if os.path.exists(top_image):
        os.remove(top_image)

    Code128(ticket_number, writer=NoTextImageWriter()).save(os.path.join(tmpdir, 'top_barcode'), options={
        'module_height': 5,
        'text_distance': 0.5,
        'quiet_zone': 1,
        'dpi': 1200,
        'font_size': 20,
    })

    im = Image(filename=os.path.join(tmpdir, 'top_barcode.png'))
    im.trim()
    im.save(filename=top_image)

    Code128(ticket_number, writer=NoTextImageWriter()).save(os.path.join(tmpdir, 'bot_barcode'), options={
        'module_height': 5,
        'text_distance': 0.5,
        'quiet_zone': 1,
        'dpi': 1200,
        'font_size': 20,
    })

    im = Image(filename=os.path.join(tmpdir, 'bot_barcode.png'))
    im.trim()
    im.save(filename=bot_image)

    if not os.path.exists(top_image) or not os.path.exists(bot_image):
        raise Exception, "Image failed to create"

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('barcode.html')
    context['time'] = datetime.datetime.now()
    context['bot_image'] = bot_image
    context['top_image'] = top_image
    output_from_parsed_template = template.render(context)
    #
    # with codecs.open(filename + ".html", "wb", encoding='utf8') as fh:
    #     fh.write(output_from_parsed_template)

    HTML(string=output_from_parsed_template, base_url='.').write_pdf(
        filename, stylesheets=["static/css/style.css"])


def fetch_ticket_number(n_row, receiver_city):
    city_name = "".join(receiver_city.strip().split())
    cities = City.find_province_path(city_name)
    if not cities:
        raise Exception, "Cannot find province: %s at row %d" % (
            city_name, n_row)
    if not cities[0].name in PROVINCE_INFO_MAP:
        raise Exception, "Post to province %s is not supported: %s at row %d" % (
            city_name, n_row)
    #info = PROVINCE_INFO_MAP[cities[0].name]
    order = Order.pick_unused()
    if order is None:
        raise Exception, u"订单号不足"
    province_name, municipal_name, address_header = City.normalize_province_path(
        cities)
    return u"国际件", order, province_name, municipal_name, address_header


def process_row(n_row, in_row, barcode_dir, tmpdir, job=None):
    p_data = []
    c_data = []
    sender_name = in_row[u'发件人名字']
    sender_phone = in_row[u'发件人电话号码']
    sender_address = in_row[u'发件人地址']
    receiver_name = in_row[u'收件人名字（中文）']
    receiver_mobile = in_row[u'收件人手机号（11位数）']
    receiver_address = in_row[u'收件人地址（无需包括省份和城市）']
    receiver_city = in_row[u'收件人城市（中文）']
    receiver_post_code = in_row[u'收件人邮编']
    n_package = in_row[u'包裹数量']
    package_weight = in_row[u'包裹重量（公斤）']
    length = in_row[u'长（厘米）']
    width = in_row[u'宽（厘米）']
    height = in_row[u'高（厘米）']
    id_number = in_row[u'身份证号(EMS需要)']

    for check_field in (sender_name, sender_phone, sender_address, receiver_name, receiver_mobile, receiver_address,
                        receiver_city, receiver_post_code, n_package, id_number):
        if pd.isnull(check_field):
            raise Exception, u"第%d行数据不完整,请更正" % n_row

    if not isinstance(sender_name, basestring) or not isinstance(sender_address, basestring):
        raise Exception, u"第%d行发件人信息异常" % n_row
    if not isinstance(n_package, int):
        raise Exception, u"第%d行包裹数量异常" % n_row
    if not isinstance(receiver_city, basestring) or not receiver_city.strip():
        raise Exception, u"第%d行收件人城市名异常" % n_row

    package_type, order, receiver_province, receiver_municipal, receiver_address_header = \
        fetch_ticket_number(n_row, receiver_city)
    receiver_city = receiver_municipal
    receiver_address = receiver_address_header + receiver_address

    pc_text = receiver_province + receiver_municipal
    receiver_province_city_font_size = "3" if len(
        pc_text) <= 10 else "2.5" if len(pc_text) <= 15 else "2"

    order.used = True
    order.used_time = datetime.datetime.utcnow()
    order.sender_address = ", ".join(
        (sender_name, sender_address, sender_phone))
    order.receiver_address = ", ".join(
        (receiver_address, receiver_city, receiver_post_code))
    order.receiver_mobile = receiver_mobile.strip()
    order.receiver_id_number = id_number.strip()
    order.receiver_name = receiver_name.strip()
    if job:
        order.job = job
        job.version = "v2"
    ticket_number = order.order_number
    full_address = "".join(filter(
        lambda x: x.strip(), (receiver_province, receiver_city, receiver_address)))

    p_data_list = []
    c_data_list = []

    item_names = []
    total_price = 0
    total_item_count = 0
    total_net_weight = 0
    total_gross_weight = 0
    for i in xrange(n_package):
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        unit_price = in_row[u'物品单价（英镑）%s' % suffix]

        if item_name is None or pd.isnull(item_name):
            raise Exception, u"第%d行第%d个商品名称为空" % (n_row, i + 1)
        item_name = str(item_name).strip()

        # m = ITEM_NAME_RE.match(item_name)
        # if not m:
        #     raise Exception, "Item name format wrong: %s at row %d" % (item_name, n_row)
        # if m.group(3):
        #     item_weight = '900'
        #     item_name += "%sg" % item_weight
        # elif m.group(4):
        #     item_weight = '800'
        #     item_name += "%sg" % item_weight
        # else:
        #     item_weight = int(m.group(5))
        #
        # item_weight_convert = int(item_weight) * item_count / 1000.0
        # item_price = item_weight_convert * 90

        #sub_total_price, net_weight, gross_weight, price_per_kg, item_full_name \
        #    = calculate_item_info_from_db(n_row, item_name, item_count)
        sub_total_price, net_weight, gross_weight, unit_price, item_full_name, net_weight_per_item, tax_code, \
        billing_unit, billing_unit_code, unit_per_item, specification \
            = calculate_item_info_from_db_without_product_info(n_row, item_name, item_count)

        item_names.append(u"%s (\u00D7%d)" % (item_full_name, item_count))
        total_price += sub_total_price
        total_item_count += item_count
        total_net_weight += net_weight
        total_gross_weight += gross_weight

        p_data_list.append([
            ticket_number, sender_name, sender_address, sender_phone, receiver_name, receiver_mobile, receiver_city if receiver_city else receiver_province,
            receiver_post_code, full_address, item_full_name, item_count, sub_total_price, gross_weight, item_full_name,
            net_weight, unit_price, u"CNY", id_number
        ])
        c_data_list.append([
            ticket_number, item_full_name, tax_code, item_count, net_weight, gross_weight, specification,
            sub_total_price, unit_price, sub_total_price, sub_total_price, unit_per_item * item_count, billing_unit_code,
            receiver_name, full_address, receiver_name, receiver_mobile, sender_name, sender_address, id_number,
            i + 1,
        ])

    assert(len(p_data_list) == len(c_data_list))

    # for p in p_data_list:
    #     p[10] = total_item_count
    #     p[11] = total_price
    #     p[12] = total_gross_weight
    #     p_data.append(p)
    p_data = p_data_list

    # for c in c_data_list:
    #     c[1] = total_net_weight
    #     c[2] = total_gross_weight
    #     c[3] = total_item_count
    #     c_data.append(c)
    c_data = c_data_list

    total_price = "%.2f" % total_price
    if total_price.endswith(".00") and len(total_price) > 3:
        total_price = total_price[:-3]

    item_names = ", ".join(item_names)

    generate_pdf(ticket_number, os.path.join(
        barcode_dir, '%s.pdf' % ticket_number), locals(), tmpdir)

    return ticket_number, pd.DataFrame(p_data, columns=[
        u'快件单号', u'发件人', u'发件人地址', u'电话号码', u'收件人', u'电话号码.1', u'城市',
        u'邮编', u'收件人地址', u'内件名称', u'数量', u'总价（元）', u'毛重（KG）', u'物品名称',
        u'数量.1', u'单价', u'币别', u'备注'
    ]), pd.DataFrame(c_data, columns=[
        u'分运单号', u'货物名称', u'商品编码', u'件数', u'净重(KG)', u'毛重(KG)', u'规格/型号',
        u'成交总价', u'申报单价', u'申报总价', u'价值', u'申报数量', u'申报计量单位',
        u'收件人', u'收件人地址', u'货主单位名称', u'电话号码(固话)', u'发件人', u'发件人地址', u'收发件人证件号',
        u'随附单证编号'
    ])


def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)


def xls_to_orders(input, output, tmpdir, percent_callback=None, job=None):
    if percent_callback:
        percent_callback(0)
    in_df = pd.read_excel(input, converters={
        u'发件人电话号码': lambda x: str(x),
        u'收件人邮编': lambda x: str(x),
        u'收件人手机号\n（11位数）': lambda x: str(x),
        u'身份证号\n(EMS需要)': lambda x: str(x),
        u'收件人手机号（11位数）': lambda x: str(x),
        u'身份证号(EMS需要)': lambda x: str(x),
        u'包裹数量': lambda x: int(x),
    })
    normalize_columns(in_df)

    package_columns = [u"报关单号", u'总运单号', u'袋号', u'快件单号', u'发件人', u'发件人地址',
                       u'电话号码', u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称',
                       u'数量', u'总价（元）', u'毛重（KG）', u'税号', u'物品名称', u'品牌', u'数量.1',
                       u'单位', u'单价', u'币别', u'备注']

    customs_columns = [u'序号', u'经营单位编号', u'经营单位名称', u'分运单号', u'货物名称', u'商品编码', u'件数',
                       u'净重(KG)', u'毛重(KG)', u'规格/型号', u'成交总价', u'申报单价', u'申报总价', u'价值', u'合同号',
                       u'申报数量', u'申报计量单位', u'第一（法定）数量', u'第一（法定）计量单位', u'第二（法定）数量',
                       u'第二（法定）计量单位', u'收件人', u'收件人地址', u'货主单位名称', u'货主单位代码', u'贸易国别',
                       u'产销国', u'电话号码(固话)', u'发件人国别', u'发件人', u'发件人地址', u'货主单位地区代码',
                       u'收发件人证件号', u'收发件人证件类型', u'包装种类', u'用途', u'随附单证类型', u'随附单证编号',
                       u'类别']

    package_df = pd.DataFrame([], columns=package_columns)
    package_data = [package_df]
    customs_df = pd.DataFrame([], columns=customs_columns)
    customs_data = [customs_df]

    barcode_dir = os.path.join(output, "barcode")
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    ticket_numbers = []
    for index, in_row in in_df.iterrows():
        ticket_number, p_data, c_data = process_row(
            index, in_row, barcode_dir, tmpdir, job)
        ticket_numbers.append(ticket_number)
        package_data.append(p_data)
        customs_data.append(c_data)
        if percent_callback:
            percent_callback(int(index * 100.0 / len(in_df.index)))

    merger = PdfFileMerger()
    for ticket_number in ticket_numbers:
        pdf_file = os.path.join(barcode_dir, "%s.pdf" % ticket_number)
        if not os.path.exists(pdf_file):
            raise Exception, "Failed to generate pdf: %s" % ticket_number
        merger.append(PdfFileReader(file(pdf_file, 'rb')))
    merger.write(os.path.join(
        output, u"面单_%d单%d页.pdf".encode('utf8') % (len(ticket_numbers), len(ticket_numbers) * 2)))
    shutil.rmtree(barcode_dir)

    package_final_df = pd.concat(package_data, ignore_index=True)
    package_final_df[u'税号'] = '01010700'
    package_final_df[u'单位'] = u'千克'
    package_final_df.index += 1
    package_final_df.to_excel(os.path.join(output, u"机场报关单.xlsx".encode('utf8')),
                              columns=package_columns, index_label="NO")

    customs_final_df = pd.concat(customs_data, ignore_index=True)
    customs_final_df[u'序号'] = range(1, len(customs_final_df.index) + 1)
    customs_final_df[u'货主单位代码'] = '4407986007'
    customs_final_df[u'贸易国别'] = '303'
    customs_final_df[u'产销国'] = '303'
    customs_final_df[u'发件人国别'] = '303'
    customs_final_df[u'货主单位地区代码'] = '44079'
    customs_final_df[u'收发件人证件类型'] = '1'
    customs_final_df[u'包装种类'] = '2'
    customs_final_df[u'用途'] = '11'
    customs_final_df[u'类别'] = 'B'

    customs_final_df.to_excel(os.path.join(output, u"江门申报单.xlsx".encode('utf8')),
                              columns=customs_columns, index=False)

    if percent_callback:
        percent_callback(100)


def read_order_numbers(inxlsx):
    df = pd.read_excel(inxlsx, converters={
        u"提取单号": lambda x: str(x)
    })
    if not u"提取单号" in df:
        raise Exception, u"输入Excel格式错误"
    order_numbers = df[u"提取单号"]
    return order_numbers


def retract_from_order_numbers(download_folder, order_numbers, output, route_config, retraction=None):
    route_name = route_config['name']
    if not os.path.exists(output):
        os.makedirs(output)

    # find all jobs and job to order number map
    receiver_sig_to_order_numbers = {}
    all_order_numbers = set()
    uuid_to_order_numbers = {}
    job_versions = {}
    for i, order_number in enumerate(order_numbers):
        order_number = str(order_number).strip()
        if order_number in all_order_numbers:
            continue
        else:
            all_order_numbers.add(order_number)
        order = Order.find_by_order_number(order_number)
        if not order:
            raise Exception, u"第%d行包含未上载订单号: %s" % (i + 1, order_number)
        if not order.used:
            raise Exception, u"第%d行包含未使用订单号: %s" % (i + 1, order_number)
        if order.retraction:
            raise Exception, u"第%d行订单号已被提取: %s, 提取信息为: Uuid [%s], 时间 [%s]" % \
                             (i + 1, order_number, order.retraction.uuid,
                              time_to_filename(order.retraction.timestamp))
        receiver_sig = order.receiver_id_number
        if not receiver_sig in receiver_sig_to_order_numbers:
            receiver_sig_to_order_numbers[receiver_sig] = []
        if len(receiver_sig_to_order_numbers[receiver_sig]) >= route_config['max_order_number_per_receiver']:
            raise Exception, u"单个收件人超过最大订单数(%d): 第%d行订单(%s)与[ %s ]包含相同证件号码(%s), 收件人: %s" % \
                             (route_config['max_order_number_per_receiver'], i + 1, order_number,
                              " / ".join(["第%d行订单(%s)" % (x + 1, y)
                                          for x, y in receiver_sig_to_order_numbers[receiver_sig]]),
                              receiver_sig, order.receiver_name)
        receiver_sig_to_order_numbers[receiver_sig].append((i, order_number))
        uuid = str(order.job.uuid)
        if not uuid in uuid_to_order_numbers:
            uuid_to_order_numbers[uuid] = set()
        uuid_to_order_numbers[uuid].add(order_number)
        job_versions[uuid] = order.job.version if order.job.version else "v1"
        if retraction:
            order.retraction = retraction

    version_to_dfs = {}

    for uuid, order_number_set in uuid_to_order_numbers.items():
        version = job_versions[uuid]
        if not version in version_to_dfs:
            version_to_dfs[version] = {'package_dfs': [], 'customs_dfs' : []}
        package_dfs = version_to_dfs[version]['package_dfs']
        customs_dfs = version_to_dfs[version]['customs_dfs']
        job_file = os.path.join(download_folder, uuid, uuid + '.zip')
        if not os.path.exists(job_file):
            raise Exception, u"历史数据丢失:%s" % uuid
        with zipfile.ZipFile(job_file) as z:
            if version == "v1":
                package_df = pd.read_excel(z.open(u"机场报关单.xlsx"), index_col=0, converters={
                    u'快件单号': lambda x: str(x),
                    u'电话号码': lambda x: str(x),
                    u'电话号码.1': lambda x: str(x),
                    u'邮编': lambda x: str(x),
                    u'税号': lambda x: str(x),
                    u'备注': lambda x: str(x),
                })
                customs_df = pd.read_excel(z.open(u"江门申报单.xlsx"), converters={
                    u"企业运单编号": lambda x: str(x),
                    u"收件人省市区代码": lambda x: str(x),
                    u"收件人电话": lambda x: str(x),
                    u"收件人证件号码": lambda x: str(x),
                    u"发货人省市区代码": lambda x: str(x),
                    u"发货人电话": lambda x: str(x),
                    u"商品备案号": lambda x: str(x),
                    u"发货人电话": lambda x: str(x),
                    u'计量单位': lambda x: str(x),
                })
                sub_package_df = package_df[
                    package_df[u"快件单号"].isin(order_number_set)]
                sub_customs_df = customs_df[
                    customs_df[u"企业运单编号"].isin(order_number_set)]

            elif version == "v2":
                package_df = pd.read_excel(z.open(u"机场报关单.xlsx"), index_col=0, converters={
                    u'快件单号': lambda x: str(x),
                    u'电话号码': lambda x: str(x),
                    u'电话号码.1': lambda x: str(x),
                    u'邮编': lambda x: str(x),
                    u'税号': lambda x: str(x),
                    u'备注': lambda x: str(x),
                })
                customs_df = pd.read_excel(z.open(u"江门申报单.xlsx"), converters={
                    u"分运单号": lambda x: str(x),
                    u"商品编码": lambda x: str(x),
                    u'申报计量单位': lambda x: str(x),
                    u'货主单位代码': lambda x: str(x),
                    u"电话号码(固话)": lambda x: str(x),
                    u"货主单位地区代码": lambda x: str(x),
                    u"收发件人证件号": lambda x: str(x),
                    u"贸易国别": lambda x: str(x),
                    u"产销国": lambda x: str(x),
                    u"发件人国别": lambda x: str(x),
                })
                sub_package_df = package_df[
                    package_df[u"快件单号"].isin(order_number_set)]
                sub_customs_df = customs_df[
                    customs_df[u"分运单号"].isin(order_number_set)]
            else:
                raise Exception, "Version not supported %s" % version

            package_dfs.append(sub_package_df)
            customs_dfs.append(sub_customs_df)

    for version, data in version_to_dfs.iteritems():
        package_dfs = data['package_dfs']
        customs_dfs = data['customs_dfs']

        def validate_route(customs_df):
            products_exclude = route_config['products_exclude'] if 'products_exclude' in route_config else []
            if products_exclude:

                if version == "v1":
                    product_col = u"主要商品"
                    order_number_col = u"企业运单编号"
                elif version == "v2":
                    product_col = u"货物名称"
                    order_number_col = u'分运单号'
                else:
                    raise Exception, "Version not supported too %s" % version

                for product_exclude in products_exclude:
                    product_exclude = product_exclude.strip()
                    if product_exclude:
                        excluded = customs_df[product_col].str.contains(product_exclude)
                        if excluded.any():
                            order_numbers_excluded = customs_df[excluded][order_number_col].map(lambda x:str(x)).tolist()
                            raise Exception, u"如下订单号包含违禁产品[%s]: %s" % \
                                             (product_exclude, ", ".join(order_numbers_excluded))

        if version == "v1":
            customs_final_df = pd.concat(customs_dfs, ignore_index=True)
            customs_final_df[u'订单编号'] = None
            customs_final_df[u'商品货号'] = range(1, len(customs_final_df.index) + 1)

            validate_route(customs_final_df)

            customs_final_df.to_excel(os.path.join(
                output, u"江门申报单_%s_%s.xlsx".encode('utf8') % (version, route_name)), index=False)

            package_final_df = pd.concat(package_dfs, ignore_index=True)
            package_final_df.index += 1
            package_final_df.to_excel(os.path.join(
                output, u"机场报关单_%s_%s.xlsx".encode('utf8') % (version, route_name)), index_label="NO")
            receiver_columns = [u'收件人证件号码', u'收件人姓名']
            receiver_df = customs_final_df[receiver_columns].drop_duplicates(receiver_columns)
            receiver_df.to_excel(os.path.join(
                output, u"收件人信息_%s_%s.xlsx".encode('utf8') % (version, route_name)), index=False)

        elif version == "v2":
            customs_final_df = pd.concat(customs_dfs, ignore_index=True)
            customs_final_df[u'序号'] = range(1, len(customs_final_df.index) + 1)

            validate_route(customs_final_df)

            customs_final_df.to_excel(os.path.join(
                output, u"江门申报单_%s_%s.xlsx".encode('utf8') % (version, route_name)), index=False)

            package_final_df = pd.concat(package_dfs, ignore_index=True)
            package_final_df.index += 1
            package_final_df.to_excel(os.path.join(
                output, u"机场报关单_%s_%s.xlsx".encode('utf8') % (version, route_name)), index_label="NO")
            receiver_columns = [u'收发件人证件号', u'收件人']
            receiver_df = customs_final_df[receiver_columns].drop_duplicates(receiver_columns)
            receiver_df.to_excel(os.path.join(
                output, u"收件人信息_%s_%s.xlsx".encode('utf8') % (version, route_name)), index=False)
        else:
            raise Exception, "Version not supported too %s" % version

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="input",
                      metavar="FILE", help="input file")
    parser.add_option("-o", "--output", dest="output",
                      metavar="DIR", help="output dir")
    parser.add_option("-t", "--tmpdir", dest="tmpdir",
                      metavar="DIR", help="tmpdir dir")

    (options, args) = parser.parse_args()

    if not options.input or not options.output or not options.tmpdir:
        parser.print_help(sys.stderr)
        exit(1)

    if not os.path.exists(options.output):
        os.makedirs(options.output)

    try:
        try:
            xls_to_orders(options.input, options.output, options.tmpdir)
            db.session.commit()
        except Exception, inst:
            db.session.rollback()
            raise inst
    except Exception, inst:
        import traceback

        traceback.print_exc(sys.stderr)
        print >> sys.stderr, inst.message.encode('utf-8')
