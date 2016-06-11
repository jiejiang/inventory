#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cStringIO

__author__ = 'jie'

import sys
import os
import shutil
import zipfile
import codecs
import datetime
from optparse import OptionParser
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from weasyprint import HTML, CSS
from wand.image import Image

Code128 = barcode.get_barcode_class('code128')


def generate_pdf(filename, context, tmpdir):
    bot_image = os.path.join(tmpdir, 'bot_barcode_trim.png')
    top_image = os.path.join(tmpdir, 'top_barcode_trim.png')
    if os.path.exists(bot_image):
        os.remove(bot_image)
    if os.path.exists(top_image):
        os.remove(top_image)

    Code128(u'5111554333299', writer=ImageWriter()).save(os.path.join(tmpdir, 'top_barcode'), options={
        'module_height': 7,
        'text_distance': 0.5,
        'quiet_zone': 1,
        'dpi': 1200,
        'font_size': 20,
    })

    im = Image(filename=os.path.join(tmpdir, 'top_barcode.png'))
    im.trim()
    im.save(filename=top_image)

    Code128(u'5111554333299', writer=ImageWriter()).save(os.path.join(tmpdir, 'bot_barcode'), options={
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
    output_from_parsed_template = template.render(context)
    #
    # with codecs.open(filename + ".html", "wb", encoding='utf8') as fh:
    #     fh.write(output_from_parsed_template)

    HTML(string=output_from_parsed_template, base_url='.').write_pdf(
        filename, stylesheets=["static/css/style.css"])


def process_row(n_row, in_row, barcode_dir, tmpdir):
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
    n_package = int(in_row[u'包裹数量'])
    package_weight = in_row[u'包裹重量（公斤）']
    length = in_row[u'长（厘米）']
    width = in_row[u'宽（厘米）']
    height = in_row[u'高（厘米）']
    id_number = in_row[u'身份证号(EMS需要)']

    total_price = 0
    item_names = []
    for i in xrange(n_package):
        if i > 5:
            break
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        unit_price = in_row[u'物品单价（英镑）%s' % suffix]

        item_price = item_count * unit_price
        item_names.append(item_name)
        total_price += item_price

        p_data.append([
            sender_name, sender_address, sender_phone, receiver_name, receiver_mobile, receiver_city,
            receiver_post_code, receiver_address, item_name, item_count, item_price, package_weight, item_name,
            item_count, unit_price, "GBP", id_number
        ])
        c_data.append([
            'xxxx', package_weight, package_weight, item_count, item_name,
            receiver_name, 'XXX', receiver_address, receiver_mobile, id_number,
            sender_name, 'ZZZ', sender_address, sender_phone,
            item_count, item_price, id_number
        ])

    item_names = ", ".join(item_names)

    generate_pdf(os.path.join(barcode_dir, '%d.pdf' % n_row), locals(), tmpdir)

    return pd.DataFrame(p_data, columns=[
        u'发件人', u'发件人地址', u'电话号码', u'收件人', u'电话号码.1', u'城市',
        u'邮编', u'收件人地址', u'内件名称', u'数量', u'总价（AUD）', u'毛重（KG）', u'物品名称',
        u'数量.1', u'单价', u'币别', u'备注'
    ]), pd.DataFrame(c_data, columns=[
        u'企业运单编号', u'净重', u'毛重', u'件数', u'主要商品',
        u'收件人姓名', u'收件人省市区代码', u'收件人地址', u'收件人电话', u'收件人证件号码',
        u'发货人名称', u'发货人省市区代码', u'发货人地址', u'发货人电话',
        u'商品数量', u'商品总价', u'备注',
    ])


def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)


def xls_to_orders(input, output, tmpdir, percent_callback=None):
    if percent_callback:
        percent_callback(0)
    in_df = pd.read_excel(input)
    normalize_columns(in_df)

    package_columns = [u"报关单号", u'总运单号', u'袋号', u'快件单号', u'发件人', u'发件人地址',
                       u'电话号码', u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称',
                       u'数量', u'总价（AUD）', u'毛重（KG）', u'税号', u'物品名称', u'品牌', u'数量.1',
                       u'单位', u'单价', u'币别', u'备注']

    customs_columns = [u'订单编号', u'物流企业备案号', u'电商平台备案号', u'企业运单编号', u'物流状态', u'运费', u'运费币制',
                       u'运输方式', u'包装种类', u'运输工具', u'保价费', u'保价费币制', u'净重', u'毛重', u'件数', u'主要商品',
                       u'进出口岸代码  商品实际进出我国关境口岸海关的关区代码', u'收件人姓名', u'收件人所在国家(地区）代码',
                       u'收件人省市区代码', u'收件人地址', u'收件人电话', u'收件人证件类型', u'收件人证件号码', u'包裹单号',
                       u'发货人名称', u'发货人所在国家(地区）代码', u'发货人省市区代码', u'发货人地址', u'发货人电话',
                       u'子订单编号', u'电商商户企业备案号', u'商品货号', u'原产国（地区）/最终目的国（地区）代码', u'计量单位',
                       u'商品数量', u'商品总价', u'备注', u'商品备案号', u'商品单价 货物的单价，RMB金额（元）', u'商品币制',
                       u'子订单备注', u'进出口标识']

    package_df = pd.DataFrame([], columns=package_columns)
    package_data = [package_df]
    customs_df = pd.DataFrame([], columns=customs_columns)
    customs_data = [customs_df]

    barcode_dir = os.path.join(output, "barcode")
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    for index, in_row in in_df.iterrows():
        p_data, c_data = process_row(index, in_row, barcode_dir, tmpdir)
        package_data.append(p_data)
        customs_data.append(c_data)
        if percent_callback:
            percent_callback(int(index * 100.0 / len(in_df.index)))

    package_final_df = pd.concat(package_data, ignore_index=True)
    package_final_df.to_excel(os.path.join(output, "zhuang_xiang.xlsx"),
                              columns=package_columns)

    customs_final_df = pd.concat(customs_data, ignore_index=True)
    customs_final_df[u'物流企业备案号'] = 'PTE681320150000001'
    customs_final_df[u'电商平台备案号'] = 'PTE681320150000002'
    customs_final_df[u'物流状态'] = '0'
    customs_final_df[u'运费'] = 0
    customs_final_df[u'运费币制'] = '303'
    customs_final_df[u'运输方式'] = '4'
    customs_final_df[u'包装种类'] = '5'
    customs_final_df[u'运输工具'] = '4'
    customs_final_df[u'保价费'] = 0
    customs_final_df[u'保价费币制'] = '303'
    customs_final_df[u'进出口岸代码  商品实际进出我国关境口岸海关的关区代码'] = '6813'
    customs_final_df[u'收件人所在国家(地区）代码'] = '142'
    customs_final_df[u'收件人证件类型'] = '0'
    customs_final_df[u'发货人所在国家(地区）代码'] = '303'
    customs_final_df[u'电商商户企业备案号'] = 'PTE681320150000002'
    customs_final_df[u'商品货号'] = range(1, len(customs_final_df.index) + 1)
    customs_final_df[u'原产国（地区）/最终目的国（地区）代码'] = '303'
    customs_final_df[u'计量单位'] = '303'
    customs_final_df[u'商品备案号'] = '01010700'
    customs_final_df[u'商品单价 货物的单价，RMB金额（元）'] = 80
    customs_final_df[u'商品备案号'] = '01010700'
    customs_final_df[u'商品币制'] = '142'
    customs_final_df[u'进出口标识'] = 'I'
    customs_final_df[u'商品备案号'] = '01010700'

    customs_final_df.to_excel(os.path.join(output, "sheng_bao.xlsx"),
                              columns=customs_columns)

    if percent_callback:
        percent_callback(100)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--input", dest="input",
                      metavar="FILE", help="input file")
    parser.add_option("--output", dest="output",
                      metavar="DIR", help="output dir")
    parser.add_option("--tmpdir", dest="tmpdir",
                      metavar="DIR", help="tmpdir dir")

    (options, args) = parser.parse_args()

    if not options.input or not options.output or not options.tmpdir:
        parser.print_help(sys.stderr)
        exit(1)

    if not os.path.exists(options.output):
        os.makedirs(options.output)

    xls_to_orders(options.input, options.output, options.tmpdir)
