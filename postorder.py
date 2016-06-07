#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jie'

import sys, os, shutil, zipfile
from optparse import OptionParser
import pandas as pd

def process_row(in_row, n_column):
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

    for i in xrange(n_package):
        suffix = "" if i == 0 else ".%d" % i
        item_name = in_row[u'申报物品%d(英文）' % (i + 1)]
        item_count = in_row[u'数量%s' % suffix]
        unit_price = in_row[u'物品单价（英镑）%s' % suffix]

        data.append([receiver_name, receiver_mobile, receiver_city, receiver_post_code, receiver_address, item_name,
                item_count, item_count * unit_price, package_weight, item_name, item_count, unit_price, "GBP", id_number])

    return pd.DataFrame(data, columns=[u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称', u'数量',
                                      u'总价（AUD）', u'毛重（KG）', u'物品名称', u'数量.1', u'单价', u'币别', u'备注'])


def normalize_columns(in_df):
    in_df.columns = map(lambda x: "".join(x.strip().split()), in_df.columns)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--input", dest="input", metavar="FILE", help="input file")

    (options, args) = parser.parse_args()

    if not options.input:
        parser.print_help(sys.stderr)
        exit(1)

    in_df = pd.read_excel(options.input)
    normalize_columns(in_df)

    package_columns = [u"报关单号", u'总运单号', u'袋号', u'快件单号', u'发件人', u'发件人地址',
               u'电话号码', u'收件人', u'电话号码.1', u'城市', u'邮编', u'收件人地址', u'内件名称',
               u'数量', u'总价（AUD）', u'毛重（KG）', u'税号', u'物品名称', u'品牌', u'数量.1',
               u'单位', u'单价', u'币别', u'备注']

    package_df = pd.DataFrame([], columns=package_columns)
    package_data = [package_df]
    n_column = 1
    for index, in_row in in_df.iterrows():
        p_data = process_row(in_row, n_column)
        n_column += len(p_data)
        package_data.append(p_data)


    print pd.concat(package_data, ignore_index=True).to_excel("tmp.xlsx", columns=package_columns)
