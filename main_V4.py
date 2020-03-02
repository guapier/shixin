# -*- coding: utf-8 -*-
# @Time    : 
# @Author  : 
# @Email   : 
# @File    : main.py
# @Software: PyCharm
# @Function:
import datetime
import json
import time
import os
import requests
import re
import random
from io import BytesIO
from lxml import etree

session = requests.session()


def get_captche_id():
    url = "http://zxgk.court.gov.cn/zhzxgk/index_form.do"
    response = requests.request("GET", url, headers=headers)
    response.encoding = response.apparent_encoding
    result = re.search(r'var captchaId = \'(.*)\';', response.text)
    print(result)
    if result:
        print(result.group(1))
        return result.group(1)


def recognize_image():
    url = "http://zxgk.court.gov.cn/zhzxgk/captcha.do"
    querystring = {"captchaId": captchaId, "random": random.uniform(0, 1)}
    while True:
        try:
            response = session.request("GET", url, headers=headers, timeout=6, params=querystring)
            if response.text:
                break
            else:
                print("retry, response.text is empty")
        except Exception as ee:
            print(ee)

        # 识别
    s = time.time()
    url = "http://10.18.81.102:6666/b"
    files = {'image_file': ('captcha.jpg', BytesIO(response.content), 'application')}
    r = session.post(url=url, files=files)
    e = time.time()

    # 识别结果
    print("接口响应: {}".format(r.text))
    predict_text = json.loads(r.text)["value"]
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("【{}】  耗时：{}ms 预测结果：{}".format(now_time, int((e - s) * 1000), predict_text))
    # # 保存文件
    # img_name = "{}_{}.{}".format(predict_text, str(time.time()).replace(".", ""), 'jpg')
    # path = os.path.join('./online/', img_name)
    # with open(path, "wb") as f:
    #     f.write(response.content)
    # print("============== end ==============")

    result = {
        'j_captcha': predict_text,
        'captchaId': captchaId
    }
    return result


def get_zhixing_list(pname, current_page=1):
    result = recognize_image()
    url = "http://zxgk.court.gov.cn/zhzxgk/newsearch"
    payload = {
        'currentPage': current_page,
        'searchCourtName': '全国法院（包含地方各级法院）',
        'selectCourtId': '0',
        'selectCourtArrange': '1',
        'pname': pname,
        'cardNum': '',
        'j_captcha': result.get('j_captcha'),
        'countNameSelect': '',
        'captchaId': result.get('captchaId')
    }

    response = session.request("POST", url, data=payload, headers=headers)
    while "验证码错误" in response.text:
        result = recognize_image()
        payload['j_captcha'] = result.get('j_captcha')
        response = session.request("POST", url, data=payload, headers=headers)
    else:
        temps = re.search('1/\d{1,4}', response.text).group()
        max_page = int(temps.replace('1/', ''))
        print("共{}页数据".format(max_page))

        for page in range(1, max_page + 1):
            print("*" * 100)
            print("正在爬取关键词{}第{}页数".format(pname, page))
            print("*" * 100)
            payload['currentPage'] = page
            response = session.request("POST", url, data=payload, headers=headers)
            while "验证码错误" in response.text:
                result = recognize_image()
                payload['j_captcha'] = result.get('j_captcha')
                response = session.request("POST", url, data=payload, headers=headers)
            else:
                html = etree.HTML(response.text)
                trs = html.xpath('//table/tbody/tr')
                for tr in trs[1:]:
                    tds = tr.xpath('.//td/text()')
                    print(tds)
                    name = tds[1]
                    case_no = tds[3]
                    print(name, result.get('j_captcha'), case_no, captchaId)
                    get_zhixing_detail(name, result.get('j_captcha'), case_no, captchaId)


def get_zhixing_detail(pnameNewDel, j_captchaNewDel, caseCodeNewDel, captchaIdNewDel):
    url = "http://zxgk.court.gov.cn/zhzxgk/newdetail?pnameNewDel={}&cardNumNewDel=&j_captchaNewDel={" \
          "}&caseCodeNewDel={}&captchaIdNewDel" \
          "={}".format(pnameNewDel, j_captchaNewDel, caseCodeNewDel, captchaIdNewDel)
    print(url)
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    # try:
    #     print(response.text.replace(u'\xaf', u' ').replace(u'\xe5', u' '))
    # except Exception as e:
    #     print(e)
    html = etree.HTML(response.text.encode('utf-8', 'ignore'))
    while "验证码错误" in response.text:
        print("验证码错误，正在重试")
        result = recognize_image()
        get_zhixing_detail(pnameNewDel, result.get('j_captcha'), caseCodeNewDel, captchaIdNewDel)
    else:
        # 被执行人
        trs = html.xpath('//table[@id="bzxr"]/tr')
        if trs:
            print("被执行人")
            for tr in trs:
                tds = tr.xpath('.//td//strong/text()')
                tds_value = tr.xpath('.//td/text()')
                print(tds, tds_value)
        else:
            pass

        trs = html.xpath('//table[@id="zb"]/tr')
        if trs:
            print("终本案件")
            for tr in trs:
                tds = tr.xpath('.//td//strong/text()')
                tds_value = tr.xpath('.//td/text()')
                print(tds, tds_value)
        else:
            pass

        trs = html.xpath('//table[@id="xgl"]/tr')
        if trs:
            print("限制消费人员")
            for tr in trs:
                tds = tr.xpath('.//td//strong/text()')
                tds_value = tr.xpath('.//td/text()')
                print(tds, tds_value)
        else:
            pass

        if trs:
            print("失信被执行人")
            for tr in trs:
                tds = tr.xpath('.//td//strong/text()')
                tds_value = tr.xpath('.//td/text()')
                print(tds, tds_value)
        else:
            pass


if __name__ == '__main__':
    headers = {
        'Connection': "keep-alive",
        'Pragma': "no-cache",
        'Cache-Control': "no-cache",
        'Origin': "http://zxgk.court.gov.cn",
        'Upgrade-Insecure-Requests': "1",
        'DNT': "1",
        'Content-Type': "application/x-www-form-urlencoded",
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/70.0.3538.102 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'Referer': "http://zxgk.court.gov.cn/zhzxgk/index_form.do",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
        'cache-control': "no-cache",
    }
    captchaId = get_captche_id()
    # captchaId = "nncjoEH6u00YX6M6r0MdOGSAbLwBVFuw"
    get_zhixing_list('王科')
