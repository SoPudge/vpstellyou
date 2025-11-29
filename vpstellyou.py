# -*- coding: utf-8 -*-

import os
import re
import json
import sys
import time
import urllib.request
from urllib.parse import urlparse
import logging
import smtplib
from datetime import datetime
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.realpath(__file__))
log_file = os.path.join(script_dir, 'log.log')

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s %(message)s'
)

def get_stock(url, pattern, headers=None):
    '''
    请求目标页面并根据给定模式判断是否有货。
    返回值：有货返回 True，无货返回 False
    url：目标页面的 URL
    pattern: 一个用于匹配"缺货"状态的正则表达式字符串，如 "Out of Stock"
    headers: 可选的请求头字典
    '''
    req = urllib.request.Request(url, None, headers)
    respond = urllib.request.urlopen(req).read().decode('utf-8')

    re_stock = re.compile(r"%s" % pattern)

    # pattern 命中表示"缺货"，否则视为"有货"
    if re_stock.search(respond):
        return False
    else:
        return True

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def send_mail(sender, password, smtp_server, receivers, message, smtp_port=25, use_tls=False):
    '''
    获得邮箱smtp的用户名，密码，并发送title，内容同title
    sender: 发件人邮箱
    password: SMTP授权码
    smtp_server: SMTP服务器地址
    receivers: 收件人列表或单个收件人
    message: 邮件内容
    smtp_port: SMTP端口，默认25
    use_tls: 是否使用TLS/SSL加密，默认False
    '''
    if isinstance(receivers, str):
        receivers = [receivers]
    
    try:
        if use_tls:
            smtpObj = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            smtpObj = smtplib.SMTP()
            smtpObj.connect(smtp_server, smtp_port)
        
        state = smtpObj.login(sender, password)
        if state[0] == 235 or state[0] == 250:
            smtpObj.sendmail(sender, receivers, message)
            return True
        smtpObj.quit()
    except smtplib.SMTPException as e:
        logging.warning("%s" % str(e))
        return False
    return False

def test_mail(mail_config):
    '''
    测试邮箱通讯是否正常
    mail_config: 邮件配置
    '''
    print("正在测试邮箱通讯...")
    logging.info("开始测试邮箱通讯")
    
    # 解构赋值获取邮件配置
    sender = mail_config['sender']
    password = mail_config['password']
    smtp_server = mail_config['smtp_server']
    smtp_port = mail_config.get('smtp_port', 25)
    use_tls = mail_config.get('use_tls', False)
    receivers = mail_config.get('receivers', [sender])
    
    # 构造测试邮件
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = "VPS监控系统 - 邮箱测试"
    content = "这是一封测试邮件。<br/><br/>发送时间：%s<br/>发件人：%s<br/>SMTP服务器：%s<br/>端口：%d<br/>使用TLS：%s" % (
        current_time, sender, smtp_server, smtp_port, "是" if use_tls else "否"
    )
    
    msg = MIMEText(content, 'html', 'utf-8')
    msg['From'] = _format_addr(sender)
    msg['To'] = _format_addr(receivers[0] if receivers else sender)
    msg['Subject'] = Header(subject, 'utf-8').encode()
    
    # 发送测试邮件
    success = send_mail(sender, password, smtp_server, receivers, msg.as_string(), smtp_port, use_tls)
    
    if success:
        print("✓ 邮箱通讯测试成功！测试邮件已发送到：%s" % ", ".join(receivers))
        logging.info("邮箱通讯测试成功")
        return True
    else:
        print("✗ 邮箱通讯测试失败，请检查配置和日志文件")
        logging.error("邮箱通讯测试失败")
        return False

def load_config(config_path='config.json'):
    '''
    加载配置文件，如果失败则直接退出程序
    config_path: 配置文件路径
    '''
    config_file = os.path.join(script_dir, config_path)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        error_msg = "错误：配置文件 %s 不存在" % config_file
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    except json.JSONDecodeError as e:
        error_msg = "错误：配置文件格式错误: %s" % str(e)
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    
    # 验证必需的配置项
    if 'mail' not in config:
        error_msg = "错误：配置文件缺少 'mail' 配置项"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    
    if 'monitors' not in config or len(config['monitors']) == 0:
        error_msg = "错误：配置文件缺少 'monitors' 配置项或监控列表为空"
        logging.error(error_msg)
        print(error_msg)
        sys.exit(1)
    
    # 验证邮件配置必需项
    required_mail_fields = ['sender', 'password', 'smtp_server']
    for field in required_mail_fields:
        if field not in config['mail']:
            error_msg = "错误：配置文件 mail 配置缺少必需字段 '%s'" % field
            logging.error(error_msg)
            print(error_msg)
            sys.exit(1)
    
    return config

def process_monitor(monitor, mail_config):
    '''
    处理单个监控任务
    monitor: 监控配置
    mail_config: 邮件配置
    '''
    # 解构赋值获取监控配置
    name = monitor.get('name')
    url = monitor.get('url')
    pattern = monitor.get('pattern')
    
    # 从 URL 提取 host 并组合 headers
    headers = {
        "Host": urlparse(url).netloc,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
    }
    
    # 解构赋值获取邮件配置
    sender = mail_config['sender']
    password = mail_config['password']
    smtp_server = mail_config['smtp_server']
    smtp_port = mail_config.get('smtp_port', 25)
    use_tls = mail_config.get('use_tls', False)
    receivers = mail_config.get('receivers', [sender])
    
    # 获取邮件模板配置
    subject_in_stock = mail_config.get('subject_in_stock', '{name} 已经补货')
    content_in_stock = mail_config.get('content_in_stock', '购买地址是</br><a href="{url}">点击购买 {name}</a>')
    heartbeat_time = mail_config.get('heartbeat_time', '08:00')
    heartbeat_subject = mail_config.get('heartbeat_subject', '{name} 程序存活')
    heartbeat_content = mail_config.get('heartbeat_content', '{time} 心跳：{name} 正常运行')
    
    # 请求方案页面，获取缺货状态
    # status: True = 有货, False = 无货
    try:
        status = get_stock(url, pattern, headers)
    except Exception as e:
        logging.error("[%s] 请求失败: %s" % (name, str(e)))
        return
    
    # 如果已经有货，则发送补货邮件
    if status is True:
        subject = subject_in_stock.format(name=name)
        content = content_in_stock.format(name=name, url=url)
        msg = MIMEText(content, 'html', 'utf-8')
        msg['From'] = _format_addr(sender)
        msg['To'] = _format_addr(receivers[0] if receivers else sender)
        msg['Subject'] = Header(subject, 'utf-8').encode()
        send_mail(sender, password, smtp_server, receivers, msg.as_string(), smtp_port, use_tls)
        logging.info("[%s] 已经补货，发送成功" % name)
    else:
        # 解析心跳时间
        heartbeat_hour, heartbeat_minute = map(int, heartbeat_time.split(':'))
        current_time = datetime.now()
        if current_time.hour == heartbeat_hour and current_time.minute == heartbeat_minute:
            subject = heartbeat_subject.format(name=name, time=current_time.strftime('%m%d'))
            content = heartbeat_content.format(name=name, time=current_time.strftime('%Y-%m-%d %H:%M:%S'))
            heartbeat_msg = MIMEText(content, 'html', 'utf-8')
            heartbeat_msg['From'] = _format_addr(sender)
            heartbeat_msg['To'] = _format_addr(receivers[0] if receivers else sender)
            heartbeat_msg['Subject'] = Header(subject, 'utf-8').encode()
            send_mail(sender, password, smtp_server, receivers, heartbeat_msg.as_string(), smtp_port, use_tls)
        else:
            logging.info("[%s] 没有补货，不发送邮件" % name)

def run_monitor(config):
    '''
    运行监控循环
    config: 配置对象
    '''
    # 解构赋值获取全局配置
    global_config = config.get('global', {})
    check_interval = global_config.get('check_interval', 60)
    log_level = global_config.get('log_level', 'DEBUG')

    # 更新日志级别
    logging.getLogger().setLevel(getattr(logging, log_level, logging.DEBUG))

    logging.info("=" * 50)
    logging.info("程序启动，配置文件加载成功")
    logging.info("日志文件: %s" % log_file)
    logging.info("全局配置 - 检查间隔: %d秒, 日志级别: %s" % (check_interval, log_level))
    logging.info("监控任务数量: %d" % len(config['monitors']))
    logging.info("=" * 50)

    print("VPS监控程序已启动")
    print("检查间隔: %d秒" % check_interval)
    print("监控任务数量: %d" % len(config['monitors']))
    print("日志文件: %s" % log_file)
    print("按 Ctrl+C 停止程序")
    print("-" * 50)

    # 解构赋值获取邮件配置和监控列表
    mail_config = config['mail']
    monitors = config['monitors']

    # 循环检查
    try:
        while True:
            # 处理所有监控任务
            for monitor in monitors:
                try:
                    process_monitor(monitor, mail_config)
                except Exception as e:
                    logging.error("处理监控任务 [%s] 时出错: %s" % (monitor.get('name', 'Unknown'), str(e)))
            
            logging.info("本次检查完成，等待 %d 秒后进行下次检查" % check_interval)
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\n程序已停止")
        logging.info("程序被用户中断")
        sys.exit(0)

def print_usage():
    '''
    打印使用说明
    '''
    print("VPS监控程序")
    print("\n用法:")
    print("  python vpstellyou.py test    - 测试邮箱通讯")
    print("  python vpstellyou.py run     - 开始循环监控")
    print("\n示例:")
    print("  python vpstellyou.py test")
    print("  python vpstellyou.py run")

#######脚本开始#######

if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # 加载配置文件（必需，失败则退出）
    config = load_config('config.json')
    
    if command == 'test':
        # 测试邮箱通讯
        test_mail(config['mail'])
    elif command == 'run':
        # 运行监控
        run_monitor(config)
    else:
        print("错误：未知命令 '%s'" % command)
        print()
        print_usage()
        sys.exit(1)
