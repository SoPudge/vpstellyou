# -*- coding: utf-8 -*-

import os
import re
import urllib2
import logging import smtplib
from datetime import datetime
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

logging.basicConfig(filename='%s/bwgtellyou.log' % os.path.split(os.path.realpath(__file__))[0],level=logging.DEBUG, format='%(asctime)s %(message)s')

def get_stock(url, pattern):

    '''
    请求搬瓦工方案并返回是否有货，有货yes，无货no
    url：请求的搬瓦工方案url
    pattern: 一个正则表达式双冒号字符串，如"Out of Stock"
    '''

    header = {"host": "bwh88.net","User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:73.0) Gecko/20100101 Firefox/73.0"}
    req = urllib2.Request(url, None, header)
    respond = urllib2.urlopen(req).read()

    re_stock = re.compile(r"%s" % pattern)

    if re_stock.search(respond):
        return "no"
    else:
        return "yes"

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def send_mail(sender, password, smtp_server, receiver, message):
    '''
    获得邮箱smtp的用户名，密码，并发送title，内容同title
    '''

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(smtp_server, 25)
        state = smtpObj.login(sender,password) 
        if state[0] == 235:
            smtpObj.sendmail(sender, receiver, message)
            logging.info("发送成功")
        smtpObj.quit()
    except smtplib.SMTPException, e:
        logging.warning("%s" % str(e))

#######脚本开始#######

#定义需要监控的URL，仅一个，默认DC6-512M-500G-49.9美元的
dc6_url = "https://bwh88.net/cart.php?a=add&pid=94&aff=58257"

#定义缺货页面验证的正则表达式，缺货会有Out of Stock字样
stock_pattern = "Out of Stock"

#定义发送的消息，HTML格式
content = "购买地址是</br><a href=%s>点击购买DC6-49.99</a></br>BWH3HYATVBJW" % dc6_url

#邮件发送信息
sender = "xxx@qq.com"
password = "smtp授权码"
smtp_server = "smtp.qq.com"
receiver = "xxx@qq.com"
msg = MIMEText(content, 'html', 'utf-8')
msg['From'] = _format_addr(sender)
msg['To'] = _format_addr(receiver)

#请求方案页面，获取缺货状态
status = get_stock(dc6_url, stock_pattern)

#如果已经补货，则标题是补货成功
#如果没有补货，则每天早上八点整发消息通知程序运行正常
if status == "yes":
    msg['Subject'] = Header('已经补货', 'utf-8').encode()
    send_mail(sender, password, smtp_server, receiver, msg.as_string())
elif datetime.now().hour == 8 and datetime.now().minute == 0:
    msg['Subject'] = Header('%s 程序存活' % datetime.now().strftime('%m%d'), 'utf-8').encode()
    send_mail(sender, password, smtp_server, receiver, msg.as_string())
else:
    logging.info("没有补货，不发送邮件")
    #msg['Subject'] = Header('%s 程序存活' % datetime.now().strftime('%m%d'), 'utf-8').encode()
    #send_mail(sender, password, smtp_server, receiver, msg.as_string())
