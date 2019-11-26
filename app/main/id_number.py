# *- coding: utf-8 -*
import pickle, os, sys, datetime

__ID_DATA = None
__ID_DATA_4 = None

def __borderline(str1, ch='*'):
    # 函数目的是为一行或多行字符串加上一个边框，更美观的输出，*为缺省边框字符
    strLen = 0
    for each in str1.splitlines():  # 找出字符串最长一行的字符数
        if strLen < len(each.encode('gb2312')): strLen = len(each.encode('gb2312'))
        # 加上encode('gb2312')是使每个汉字记为2个字符长度
    str2 = ch * (strLen + 6) + '\n'
    str2 = str2 + ch + ' ' * (strLen + 4) + ch + '\n'
    for each in str1.splitlines():
        str2 = str2 + ch + '  ' + each + ' ' * (strLen - len(each.encode('gb2312')) + 2) + ch + '\n'
    str2 = str2 + ch + ' ' * (strLen + 4) + ch + '\n'
    str2 = str2 + ch * (strLen + 6)
    return str2

def __checkDate(str1):
    # 检查日期数据是否合法
    try:
        birthday = datetime.date(int(str1[6:10]), int(str1[10:12]), int(str1[12:14]))
        check = True
    except:
        check = False
    return check

def __checkByte(str1):
    # 计算校验位
    w = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    s = 0
    for i in range(17):
        s = s + int(str1[i]) * w[i]
    check = (1 - s) % 11  # 可以s%11再查表得到校验位，根据规律直接计算得出
    if check == 10: check = 'X'
    check = str(check)
    return check

def __sex(str1):
    # 查看性别
    if int(str1[-2]) % 2 == 0:
        return '女'
    else:
        return '男'

def validate(code):
    """
    # source: https://blog.csdn.net/y1175626605/article/details/79687047
    :param code:
    :return:
    """
    global __ID_DATA, __ID_DATA_4
    if not code or (len(code) != 15 and len(code) != 18):
        return False
    if len(code) == 15:
        code = code[:6] + '19' + code[6:] + 'M'
    if not (code[:17].isdigit() and (code[-1].isdigit() or code[-1] == 'M' or code[-1].upper() == 'X')):
        return False
    if not __ID_DATA:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'iddata.pkl'), 'rb') as f:
            __ID_DATA = pickle.load(f)
            __ID_DATA_4 = set()
            for key, value in __ID_DATA.iteritems():
                __ID_DATA_4.add(key[:4])
    if not code[:4] in __ID_DATA_4:
        return False
    if __checkDate(code) == False:
        return False
    last = __checkByte(code)
    if code[-1] != 'M' and code[-1] != last:
        return False
    return True

if __name__ == '__main__':
    if sys.argv[1] == '--add-region-code' and sys.argv[2] and len(sys.argv[2]) == 6 and sys.argv[2].isdigit() and sys.argv[3]:
        region_code = sys.argv[2]
        region_name = sys.argv[3]
        iddata_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'iddata.pkl')
        with open(iddata_filepath, 'rb') as f:
            iddata = pickle.load(f)
        if not region_code in iddata:
            print "add ", region_code, region_name
            iddata[region_code] = region_name
            with open(iddata_filepath, 'wb') as f:
                pickle.dump(iddata, f)
    else:
        print validate(sys.argv[1].replace(u'\u202c'.encode('utf-8'), ''))
