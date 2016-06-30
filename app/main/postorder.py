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

from ..models import City, Order
from .. import db

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

    u"广东": {'ticket_initial': 9, 'package_type': u"国内标准快递"},

    u"内蒙古": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"甘肃": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"青海": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"宁夏": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"吉林": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"西藏": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
    u"新疆": {'ticket_initial': 1, 'package_type': u"国内标准快递"},
}

ITEM_NAME_RE = re.compile(ur"^.*?((([123一二三])|([4四]))段|(\d+)g)$", flags=re.U | re.I)


# ITEM_NAME_RE = re.compile(ur"^.*?1段$", flags=re.U|re.I)

def generate_pdf(ticket_number, filename, context, tmpdir):
    bot_image = os.path.join(tmpdir, 'bot_barcode_trim.png')
    top_image = os.path.join(tmpdir, 'top_barcode_trim.png')
    if os.path.exists(bot_image):
        os.remove(bot_image)
    if os.path.exists(top_image):
        os.remove(top_image)

    Code128(ticket_number, writer=ImageWriter()).save(os.path.join(tmpdir, 'top_barcode'), options={
        'module_height': 7,
        'text_distance': 0.5,
        'quiet_zone': 1,
        'dpi': 1200,
        'font_size': 20,
    })

    im = Image(filename=os.path.join(tmpdir, 'top_barcode.png'))
    im.trim()
    im.save(filename=top_image)

    Code128(ticket_number, writer=ImageWriter()).save(os.path.join(tmpdir, 'bot_barcode'), options={
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
    province = City.find_province(city_name)
    if not province:
        raise Exception, "Cannot find province: %s at row %d" % (city_name, n_row)
    if not province.name in PROVINCE_INFO_MAP:
        raise Exception, "Post to province %s is not supported: %s at row %d" % (city_name, n_row)
    info = PROVINCE_INFO_MAP[province.name]
    order = Order.pick_first(info['ticket_initial'])
    if order is None:
        raise Exception, u"订单号不足, 订单类型:%s" % Order.Type.types[info['ticket_initial']]
    return info['package_type'], order


def lookup_item_info(item_name):

    return sub_total_price, net_weight, gross_weight, cny_unit_price, item_full_name


def process_row(n_row, in_row, barcode_dir, tmpdir, job=None):
    p_data = []
    c_data = []
    sender_name = in_row[u'发件人名字']
    sender_phone = str(in_row[u'发件人电话号码'])
    sender_address = in_row[u'发件人地址']
    receiver_name = in_row[u'收件人名字（中文）']
    receiver_mobile = str(in_row[u'收件人手机号（11位数）'])
    receiver_address = in_row[u'收件人地址（无需包括省份和城市）']
    receiver_city = in_row[u'收件人城市（中文）']
    receiver_post_code = str(in_row[u'收件人邮编'])
    n_package = int(in_row[u'包裹数量'])
    package_weight = in_row[u'包裹重量（公斤）']
    length = in_row[u'长（厘米）']
    width = in_row[u'宽（厘米）']
    height = in_row[u'高（厘米）']
    id_number = str(in_row[u'身份证号(EMS需要)'])

    package_type, order = fetch_ticket_number(n_row, receiver_city)
    order.used = True
    order.used_time = datetime.datetime.utcnow()
    order.sender_address = ", ".join((sender_name, sender_address, sender_phone))
    order.receiver_address = ", ".join((receiver_address, receiver_city, receiver_post_code, receiver_mobile))
    order.receiver_id_number = id_number
    order.receiver_name = receiver_name
    if job:
        order.job = job
    ticket_number = order.order_number

    total_price = 0
    item_names = []
    for i in xrange(n_package):
        if i > 5:
            break
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        unit_price = in_row[u'物品单价（英镑）%s' % suffix]

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
        sub_total_price, net_weight, gross_weight, cny_unit_price, item_full_name = lookup_item_info(item_name)

        item_names.append(item_full_name)
        total_price += sub_total_price

        p_data.append([
            ticket_number, sender_name, sender_address, sender_phone, receiver_name, receiver_mobile, receiver_city,
            receiver_post_code, receiver_address, item_name, item_count, sub_total_price, gross_weight, item_name,
            item_count, cny_unit_price, u"CNY", id_number
        ])
        c_data.append([
            ticket_number, net_weight, gross_weight, item_count, item_full_name,
            receiver_name, receiver_post_code, receiver_address, receiver_mobile, id_number,
            sender_name, receiver_post_code, sender_address, sender_phone,
            net_weight, sub_total_price, gross_weight
        ])

    total_price = "%.2f" % total_price
    if total_price.endswith(".00") and len(total_price) > 3:
        total_price = total_price[:-3]

    item_names = ", ".join(item_names)

    generate_pdf(ticket_number, os.path.join(barcode_dir, '%s.pdf' % ticket_number), locals(), tmpdir)

    return ticket_number, pd.DataFrame(p_data, columns=[
        u'快件单号', u'发件人', u'发件人地址', u'电话号码', u'收件人', u'电话号码.1', u'城市',
        u'邮编', u'收件人地址', u'内件名称', u'数量', u'总价（元）', u'毛重（KG）', u'物品名称',
        u'数量.1', u'单价', u'币别', u'备注'
    ]), pd.DataFrame(c_data, columns=[
        u'企业运单编号', u'分运单净重', u'分运单毛重', u'箱件数', u'主要商品',
        u'收件人姓名', u'收件人省市区代码', u'收件人地址', u'收件人电话', u'收件人证件号码',
        u'发货人名称', u'发货人省市区代码', u'发货人地址', u'发货人电话',
        u'净重/数量', u'商品总价', u'商品毛重'
    ])


def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)


def xls_to_orders(input, output, tmpdir, percent_callback=None, job=None):
    if percent_callback:
        percent_callback(0)
    in_df = pd.read_excel(input)
    normalize_columns(in_df)

    package_columns = [u"报关单号", u'总运单号', u'袋号', u'快件单号', u'发件人', u'发件人地址',
                       u'电话号码', u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称',
                       u'数量', u'总价（元）', u'毛重（KG）', u'税号', u'物品名称', u'品牌', u'数量.1',
                       u'单位', u'单价', u'币别', u'备注']

    customs_columns = [u'订单编号', u'物流企业备案号', u'电商平台备案号', u'企业运单编号', u'物流状态', u'运费', u'运费币制',
                       u'运输方式', u'运输工具名称', u'包装种类', u'保价费', u'保价费币制', u'分运单净重', u'分运单毛重', u'箱件数', u'主要商品',
                       u'进出口岸代码  商品实际进出我国关境口岸海关的关区代码', u'收件人姓名', u'收件人所在国家(地区）代码',
                       u'收件人省市区代码', u'收件人地址', u'收件人电话', u'收件人证件类型', u'收件人证件号码', u'包裹单号',
                       u'发货人名称', u'发货人所在国家(地区）代码', u'发货人省市区代码', u'发货人地址', u'发货人电话',
                       u'子订单编号', u'电商商户企业备案号', u'商品货号', u'原产国（地区）/最终目的国（地区）代码', u'计量单位',
                       u'净重/数量', u'商品总价', u'载货清单号', u'商品备案号', u'商品单价 货物的单价，RMB金额（元）', u'商品币制',
                       u'子订单备注', u'进出口标识', u'是否退运', u'原运单号', u'退运原因', u'运输工具航次(班)号',
                       u'码头/货场代码（为物流监控备用）', u'商品毛重', u'仓单申报类型N表示新增M修改',
                       u'第一法定数量CD类必填，AB类不填', ]

    package_df = pd.DataFrame([], columns=package_columns)
    package_data = [package_df]
    customs_df = pd.DataFrame([], columns=customs_columns)
    customs_data = [customs_df]

    barcode_dir = os.path.join(output, "barcode")
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    ticket_numbers = []
    for index, in_row in in_df.iterrows():
        ticket_number, p_data, c_data = process_row(index, in_row, barcode_dir, tmpdir, job)
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
    merger.write(os.path.join(output, u"面单_%d页.pdf".encode('utf8') % len(ticket_numbers)))
    shutil.rmtree(barcode_dir)

    package_final_df = pd.concat(package_data, ignore_index=True)
    package_final_df[u'税号'] = '01010700'
    package_final_df[u'单位'] = u'千克'
    package_final_df.to_excel(os.path.join(output, u"机场装箱单.xlsx".encode('utf8')),
                              columns=package_columns)

    customs_final_df = pd.concat(customs_data, ignore_index=True)
    customs_final_df[u'物流企业备案号'] = 'PTE681320150000003'
    customs_final_df[u'电商平台备案号'] = 'PTE681320150000004'
    customs_final_df[u'物流状态'] = '0'
    customs_final_df[u'运费'] = 0
    customs_final_df[u'运费币制'] = '303'
    customs_final_df[u'运输方式'] = '4'
    customs_final_df[u'包装种类'] = '4'
    customs_final_df[u'保价费'] = 0
    customs_final_df[u'保价费币制'] = '303'
    customs_final_df[u'进出口岸代码  商品实际进出我国关境口岸海关的关区代码'] = '6813'
    customs_final_df[u'收件人所在国家(地区）代码'] = '142'
    customs_final_df[u'收件人证件类型'] = '1'
    customs_final_df[u'发货人所在国家(地区）代码'] = '601'
    customs_final_df[u'电商商户企业备案号'] = 'PTE681320150000004'
    customs_final_df[u'商品货号'] = range(1, len(customs_final_df.index) + 1)
    customs_final_df[u'原产国（地区）/最终目的国（地区）代码'] = '303'
    customs_final_df[u'计量单位'] = '035'
    customs_final_df[u'商品备案号'] = '01010700'
    customs_final_df[u'商品单价 货物的单价，RMB金额（元）'] = 90
    customs_final_df[u'商品备案号'] = '01010700'
    customs_final_df[u'商品币制'] = '142'
    customs_final_df[u'进出口标识'] = 'I'
    customs_final_df[u'码头/货场代码（为物流监控备用）'] = '6813'
    customs_final_df[u'仓单申报类型N表示新增M修改'] = 'N'

    customs_final_df.to_excel(os.path.join(output, u"申报表格.xlsx".encode('utf8')),
                              columns=customs_columns, index=False)

    if percent_callback:
        percent_callback(100)


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
