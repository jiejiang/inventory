# -*- coding: utf-8 -*-
import requests, sys, uuid, json, hashlib, time, base64
from collections import OrderedDict

def fetch_order_number(order_uuid, parameters):
    item_names = []
    item_counts = 0
    for item_name, item_count in parameters['items']:
        item_names.append(item_name)
        item_counts += int(item_count)
    waybill = OrderedDict([
        ('txLogisticID', order_uuid),
        ('nameP', parameters['receiver_name']),
        ('phoneP', parameters['receiver_mobile']),
        ('provP', parameters['province_name']),
        ('cityP', parameters['municipal_name'] if parameters['municipal_name'] else parameters['province_name']),
        ('addressP', parameters['address_header'] + parameters['receiver_address']),
        ('itemName', ';'.join(item_names)),
        ('number', int(item_counts)),
        ('name', parameters['sender_name']),
        ('phone', parameters['sender_phone']),
        ('clientName', u'英国环球'),
        ('yto_emp_code', '99.067;英国环球')
    ])
    json_str = json.dumps([waybill], sort_keys=False, encoding='utf-8')
    data = {
        'method': 'waybill',
        'ztdkey': hashlib.md5(("hyht" + json_str + "hyht").upper()).hexdigest(),
        'data': json_str
    }
    #response = requests.post('http://112.74.102.185:8095/NewWaybillInterface-HYHTTest/waybill.do', data=data)
    response = requests.post('http://112.74.102.185:8100/GetWaybillNumHYHT/waybill.do', data=data)
    #print response.status_code, response.content
    if response.status_code != requests.codes.ok:
        raise Exception(u'圆通API失败：' + response.content)
    r_data = response.json()
    print r_data
    order_number = None
    short_address = None
    for datum in r_data:
        if not 'success' in datum or not datum['success'] or not 'mailNo' in datum or not datum['mailNo']:
            raise Exception(u'圆通API返回无效：' + datum['message'])
        if not order_number:
            order_number = datum['mailNo']
            short_address = datum['shortAddress']
        else:
            if order_number != datum['mailNo']:
                raise Exception(u'圆通API返回多个mailNo:' + r_data)
    print >> sys.stderr, 'gen order number', order_number
    return order_number, short_address


if __name__ == '__main__':
    url, api_account, api_key, transportModeCode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

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
	"Piece": "4",
	"declareType": "2",
	"remark": "基本信息备注",
	"shipper": {
		"name": "发件人姓名",
		"company": "圆通科技有限公司",
		"countryCode": "GB",
		"provinceName": "陕西省",
		"cityName": "西安市",
		"address": "详细地址",
		"postCode": "717200",
		"areaName": "区域名称",
		"phone": "18509251760",
		"mobile": "18509251760"
	},
	"consignee": {
		"name": "收件人姓名",
		"company": "圆通科技有限公司",
		"countryCode": "CN",
		"provinceName": "陕西省",
		"cityName": "西安市",
		"address": "川南奉公路9983号",
		"postCode": "75044",
		"areaName": "雁塔区",
		"phone": "18509251760",
		"mobile": "18509251760",
		"certificateType": "ID",
		"certificateNumber": "610628199105201727"
	},
	"orderInvoices": [{
		"ename": "asdf234",
		"cname": "fda223",
		"quantity": "2",
		"unit": "MTR",
		"unitPrice": "15.5",
		"customsOrdinationNo": "HG1001",
		"remark": "配货备注",
		"saleAddr": "销售地址--申报品1",
		"currencyCode": "USD",
		"currencyName": "澳元"
	}],
	"orderBizServices":{
		"needDistributeCode":true
	}
}""" % transportModeCode
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

