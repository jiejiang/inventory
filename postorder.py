#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cStringIO

__author__ = 'jie'

import sys, os, shutil, zipfile, codecs, datetime
from optparse import OptionParser
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from weasyprint import HTML, CSS
from wand.image import Image

Code128 = barcode.get_barcode_class('code128')

def trim(filepath):
    im = Image.open(filepath)
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        im.crop(bbox)
        im.save(filepath)

def generate_pdf(filename, context, tmpdir):
    bot_image = os.path.join(tmpdir, 'bot_barcode_trim.png')
    top_image = os.path.join(tmpdir, 'top_barcode_trim.png')
    if os.path.exists(bot_image):
        os.remove(bot_image)
    if os.path.exists(top_image):
        os.remove(top_image)

    Code128(u'5111554333299', writer=ImageWriter()).save(os.path.join(tmpdir, 'top_barcode'), options={
        'module_height' : 7,
        'text_distance' : 0.5,
        'quiet_zone': 1,
        'dpi': 1200,
        'font_size' : 20,
    })

    im = Image(filename=os.path.join(tmpdir, 'top_barcode.png'))
    im.trim()
    im.save(filename=top_image)

    Code128(u'5111554333299', writer=ImageWriter()).save(os.path.join(tmpdir, 'bot_barcode'), options={
        'module_height' : 5,
        'text_distance' : 0.5,
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
    context['time'] =  datetime.datetime.now()
    output_from_parsed_template = template.render(context)

    with codecs.open(filename + ".html", "wb", encoding='utf8') as fh:
        fh.write(output_from_parsed_template)

    HTML(string=output_from_parsed_template, base_url='.').write_pdf(filename, stylesheets=["static/css/style.css"])

def process_row(n_row, in_row, barcode_dir, tmpdir):
    data = []
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
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        unit_price = in_row[u'物品单价（英镑）%s' % suffix]

        item_price = item_count * unit_price
        data.append([receiver_name, receiver_mobile, receiver_city, receiver_post_code, receiver_address, item_name,
                item_count, item_price, package_weight, item_name, item_count, unit_price, "GBP", id_number])
        item_names.append(item_name)

        total_price += item_price
    item_names = ", ".join(item_names)

    generate_pdf(os.path.join(barcode_dir, '%d.pdf' % n_row), locals(), tmpdir)

    return pd.DataFrame(data, columns=[u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称', u'数量',
                                      u'总价（AUD）', u'毛重（KG）', u'物品名称', u'数量.1', u'单价', u'币别', u'备注'])

def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--input", dest="input", metavar="FILE", help="input file")
    parser.add_option("--output", dest="output", metavar="DIR", help="output dir")
    parser.add_option("--tmpdir", dest="tmpdir", metavar="DIR", help="tmpdir dir")

    (options, args) = parser.parse_args()

    if not options.input or not options.output or not options.tmpdir:
        parser.print_help(sys.stderr)
        exit(1)

    if not os.path.exists(options.output):
        os.makedirs(options.output)

    in_df = pd.read_excel(options.input)
    normalize_columns(in_df)

    package_columns = [u"报关单号", u'总运单号', u'袋号', u'快件单号', u'发件人', u'发件人地址',
               u'电话号码', u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称',
               u'数量', u'总价（AUD）', u'毛重（KG）', u'税号', u'物品名称', u'品牌', u'数量.1',
               u'单位', u'单价', u'币别', u'备注']

    package_df = pd.DataFrame([], columns=package_columns)
    package_data = [package_df]

    barcode_dir = os.path.join(options.output, "barcode")
    if not os.path.exists(barcode_dir):
        os.makedirs(barcode_dir)

    for index, in_row in in_df.iterrows():
        p_data = process_row(index, in_row, barcode_dir, options.tmpdir)
        package_data.append(p_data)

    pd.concat(package_data, ignore_index=True).to_excel(os.path.join(options.output, "1.xlsx"), columns=package_columns)


