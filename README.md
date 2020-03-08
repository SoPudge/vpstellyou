## 原理
微信可以绑定QQ邮箱提醒，和普通消息提醒一模一样，所以如果搬瓦工特定套餐补货的话，通过邮件发送到对应的QQ邮箱，就可以达到微信消息提醒的目的。当然也可以使用其他邮件客户端，比如网易邮件客户端，Gmail提醒都是一样的效果，只是微信用起来比较方便，适合大众。

- 使用Python2写脚本，所有Linux都可以运行，并且Python不import第三方的包
- 使用urllib2进行http请求，使用re正则表达式分析结果，使用smtplib发送邮件
- 使用QQ邮箱作为接收方，同一个QQ邮箱给自己发送，以免不同邮件提供商延迟
- 使用Crontab每隔5分钟运行一次
- 补货则发送邮件通知，没有补货则写入日志，每天早晨8:00发送邮件确认程序存活

>**为什么不使用shell**
因为shell做http请求还需要wget活着curl还得专门安装，同时shell发邮件支持不太好。


![](http://65536.io/wordpress/wp-content/uploads/2020/03/Screenshot_20200308120843_1.png)


![](http://65536.io/wordpress/wp-content/uploads/2020/03/Screenshot_20200308-121015_WeChat.jpg)


![](http://65536.io/wordpress/wp-content/uploads/2020/03/Snipaste_2020-03-08_12-16-15.png)

## 方法

### 下载脚本

下载下列脚本，存储在任意文件夹即可，我一般放在~文件夹方便查找。
>github.com

### 修改对应的收发邮件信息

修改66-69行对应的邮箱信息即可，其中QQ邮箱的smtp功能不能使用原始的QQ邮箱密码，而需要独立申请SMTP的授权码，具体请参加QQ邮箱帮助[SMTP授权码使用帮助](https://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256%27)

```
#邮件发送信息
sender = "发送邮箱xxx@qq.com"
password = "QQ邮箱的smtp授权码"
smtp_server = "smtp.qq.com"
receiver = "接收邮箱，格式带@qq.com"
```

### 测试发送是否成功

测试的时候，**取消**注释脚本最后两行，然后运行即可测试发送邮件

**第一步，把最后两行的注释去掉**

```
……
elif datetime.now().hour == 8 and datetime.now().minute == 0:
    msg['Subject'] = Header('%s 程序存活' % datetime.now().strftime('%m%d'), 'utf-8').encode()
    send_mail(sender, password, smtp_server, receiver, msg.as_string())
else:
    logging.info("没有补货，不发送邮件")
    #msg['Subject'] = Header('%s 程序存活' % datetime.now().strftime('%m%d'), 'utf-8').encode()
    #send_mail(sender, password, smtp_server, receiver, msg.as_string())
```
**第二步，运行该脚本看是否收到邮件**
```
python bwgtellyou.py
```

**第三步，注释掉最后两行**
```
务必注释掉最后两行，否则每五分都会收到邮件。
```

运行完毕之后，应该会收到一封名为“程序存活”标题的邮件，实际上就是每天早晨8:00会收到的确认程序运行良好的邮件，补货的时候，会收到标题为“已经补货”的邮件，并且邮件正文包含对应的购买链接和优惠码，直接点击就可以了。

### 使用Crontab定期执行
Crontab使用的坑还是很多的，比如说默认没有日志，需要使用绝对路径等，在这里也做一个完整的设置，方便debug，**可选的步骤可以不用做，不影响程序的运行，此处仅作记录。**

**（可选）第一步，打开crontab日志**
```
#Debian可用，centos类似
vi /etc/rsyslog.conf
#去掉如下行的注释即可
cron.*    /var/log/cron.log
#保存后如下命令重启日志服务
/etc/init.d/rsyslog restart
#重启crontab服务
/etc/init.d/cron restart
```

**第二步，写入crontab命令**

```
#运行如下命令开启crontab编辑
crontab -e
#最后一行添加下列指令，即5分钟运行一次检查脚本
#该脚本使用自带python2，如果python3无法运行成功的，于法有区别
*/5 * * * * /usr/bin/python ~/bwgtellyou.py
#保存后crontab会自动更新
```

**（可选）第三步，检查运行情况**

```
#方法一，直接等待五分钟，并检查脚本同目录下的bwgtellyou.log日志是否有变化
tail -f bwgtellyou.log
#方法二，等待五分钟，检查crontab的日志查找问题
#每5分钟应该会有执行的提示的
tail -f /var/log/cron.log
```

