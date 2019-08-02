# -*- coding: utf-8 -*-
import requests, sys, uuid, json, hashlib, time, base64
from collections import OrderedDict

def fetch_order_number(config, parameters):
    url = config.get('url', None)
    api_account = config.get('api_account', None)
    api_key = config.get('api_key', None)
    transport_mode_code = config.get('transport_mode_code', None)
    if not url or not api_account or not api_key or not transport_mode_code:
        raise Exception, u"无效圆通配置"

    waybill = OrderedDict([
        ('transportModeCode', transport_mode_code),
        ('weight', parameters['package_weight']),
        ('declareType', '2'),
        ('shipper', OrderedDict([
            ('name', parameters['sender_name']),
            ('countryCode', 'GB'),
            ('address', parameters['sender_address']),
            ('mobile', parameters['sender_phone']),
        ])),
        ('consignee', OrderedDict([
            ('name', parameters['receiver_name']),
            ('countryCode', 'CN'),
            ('provinceName', parameters['province_name']),
            ('cityName', parameters['municipal_name'] if parameters['municipal_name'] else parameters['province_name']),
            ('address', parameters['receiver_address']),
            ('mobile', parameters['receiver_mobile']),
        ])),
        ('orderBizServices', OrderedDict([
            ('needDistributeCode', True),
        ])),
    ])

    payload = json.dumps(waybill, sort_keys=False, encoding='utf-8')
    headers = {
        'Content-Type': 'application/json',
        'msg_id': str(time.time()),
        'partner_code': api_account,
        'msg_type': 'PLACE_ORDER',
        'data_digest': base64.b64encode(hashlib.md5(payload + api_key).digest()),
    }

    response = requests.post(url, data=payload, headers=headers)
    if response.status_code != requests.codes.ok:
        raise Exception(u'圆通API失败：' + response.content)
    data = response.json().get('data', {})
    order_number = data.get('orderId', None)
    distribute_code = data.get('distributeCode', None)
    if not order_number or not distribute_code:
        raise Exception(u'圆通API返回无效:' + response.content)
    print >> sys.stderr, 'gen order number', order_number, distribute_code
    return order_number, distribute_code


if __name__ == '__main__':
    url, api_account, api_key, transport_mode_code = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    payload = json.dumps(OrderedDict())
    headers = {
        'Content-Type': 'application/json',
        'msg_id': str(time.time()),
        'partner_code' : api_account,
        'msg_type' : 'GET_BASEDATA_TRANSPORT',
        'data_digest' : base64.b64encode(hashlib.md5(payload + api_key).digest()),
    }

    resp = requests.post(url, data=payload, headers=headers)
    # print resp.status_code
    print resp.content

    # payload = json.dumps(OrderedDict([
    #     ('productCode', '1234')
    # ]))
    # headers = {
    #     'Content-Type': 'application/json',
    #     'msg_id': str(time.time()),
    #     'partner_code': api_account,
    #     'msg_type': 'GET_EXTRA_SERVICE',
    #     'data_digest': base64.b64encode(hashlib.md5(payload + api_key).digest()),
    # }
    #
    # resp = requests.post(url, data=payload, headers=headers)

    # GB-GZ N
    payload = """{
	"transportModeCode": "%s",
	"weight": "1",
	"declareType": "2",
	"shipper": {
		"name": "发件人姓名",
		"countryCode": "GB",
		"address": "详细地址",
		"mobile": "18509251760"
	},
	"consignee": {
		"name": "收件人姓名",
		"countryCode": "CN",
		"provinceName": "陕西",
		"cityName": "西安",
		"address": "陕西西安川南奉公路9983号",
		"mobile": "18509251760"
	},
	"orderBizServices":{
		"needDistributeCode":true
	}
}""" % transport_mode_code
    payload = json.dumps(json.loads(payload))
    headers = {
        'Content-Type': 'application/json',
        'msg_id': str(time.time()),
        'partner_code': api_account,
        'msg_type': 'PLACE_ORDER',
        'data_digest': base64.b64encode(hashlib.md5(payload + api_key).digest()),
    }

    resp = requests.post(url, data=payload, headers=headers)
    print resp.status_code
    print resp.content

    # from lxml import etree as ET
    # from lxml.builder import E
    #
    # content = E.Message()
    # body = ET.tostring(content)
    # print body + api_key
    #
    # headers = {
    #     'Content-Type': 'application/xml',
    #     'msg_id': str(time.time()),
    #     'partner_code': api_account,
    #     'msg_type': 'GET_BASEDATA_TRANSPORT',
    #     'data_digest': base64.b64encode(hashlib.md5(body + api_key).digest()),
    # }
    # resp = requests.post(url, data=body, headers=headers)
    # print resp.status_code
    # print resp.content

