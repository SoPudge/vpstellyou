## 原理
微信可以绑定QQ邮箱提醒，和普通消息提醒一模一样，所以如果VPS特定套餐补货的话，通过邮件发送到对应的QQ邮箱，就可以达到微信消息提醒的目的。当然也可以使用其他邮件客户端，比如网易邮件客户端，Gmail提醒都是一样的效果，只是微信用起来比较方便，适合大众。

- 使用 Python3 编写脚本，兼容所有 Linux 系统，仅使用标准库，无需安装第三方包
- 使用 urllib.request 进行 HTTP 请求，使用 re 正则表达式分析结果，使用 smtplib 发送邮件
- 支持多个监控目标，支持多收件人，支持自定义邮件模板
- 使用 JSON 配置文件管理所有设置，配置灵活方便
- 补货则发送邮件通知，没有补货则写入日志，每天指定时间发送心跳邮件确认程序存活
- 支持命令行方式运行，可测试邮箱或启动监控
- 内置循环检查机制，无需 Crontab

![](http://65536.io/wordpress/wp-content/uploads/2020/03/Screenshot_20200308120843_1.png)

![](http://65536.io/wordpress/wp-content/uploads/2020/03/Screenshot_20200308-121015_WeChat.jpg)

![](http://65536.io/wordpress/wp-content/uploads/2020/03/Snipaste_2020-03-08_12-16-15.png)

## 快速开始

### 1. 下载脚本

克隆或下载本仓库到任意文件夹，建议放在 `~` 目录方便管理。

```bash
git clone https://github.com/SoPudge/vpstellyou.git
cd vpstellyou
```

### 2. 准备配置文件

**第一步：复制配置模板**

配置模板文件为 `config.json.template`，使用时需要去掉 `.template` 后缀：

```bash
cp config.json.template config.json
```

**第二步：获取 QQ 邮箱 SMTP 授权码**

QQ 邮箱的 SMTP 功能不能使用原始的 QQ 邮箱密码，需要独立申请 SMTP 的授权码。

具体步骤请参考 QQ 邮箱帮助：[SMTP 授权码使用帮助](https://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256)

**第三步：编辑配置文件**

编辑 `config.json`，修改以下关键配置项：

```json
{
  "mail": {
    "sender": "你的QQ邮箱@qq.com",
    "password": "你的SMTP授权码",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "use_tls": true,
    "receivers": ["接收邮箱1@qq.com", "接收邮箱2@qq.com"],
    "subject_in_stock": "{name} 已经补货",
    "content_in_stock": "购买地址是</br><a href=\"{url}\">点击购买 {name}</a>",
    "heartbeat_time": "08:00",
    "heartbeat_subject": "{name} 程序存活",
    "heartbeat_content": "{time} 心跳：{name} 正常运行"
  },
  "global": {
    "check_interval": 60,
    "log_level": "DEBUG"
  },
  "monitors": [
    {
      "name": "DC6-512M-500G-49.9",
      "url": "https://bwh88.net/cart.php?a=add&pid=94&aff=58257",
      "pattern": "Out of Stock"
    }
  ]
}
```

### 3. 测试邮箱通讯

在启动监控之前，先测试邮箱配置是否正确：

```bash
python vpstellyou.py test
```

如果配置正确，会看到如下提示，并且收件人会收到一封测试邮件：

```
正在测试邮箱通讯...
✓ 邮箱通讯测试成功！测试邮件已发送到：xxx@qq.com
```

如果测试失败，请检查：
- SMTP 授权码是否正确
- `smtp_port` 和 `use_tls` 设置是否匹配（QQ 邮箱通常使用 465 端口 + `true`）
- 查看脚本目录下的 `log.log` 文件获取详细错误信息

### 4. 开始监控

测试成功后，启动监控程序：

```bash
python vpstellyou.py run
```

程序会显示如下信息并开始循环监控：

```
VPS监控程序已启动
检查间隔: 60秒
监控任务数量: 1
日志文件: /path/to/log.log
按 Ctrl+C 停止程序
--------------------------------------------------
```

按 `Ctrl+C` 可以随时停止程序。

### 5. 后台运行（可选）

如果希望程序在后台持续运行，可以使用 `nohup` 或 `screen`：

```bash
# 使用 nohup 后台运行
nohup python vpstellyou.py run > /dev/null 2>&1 &

# 或使用 screen
screen -S vpstellyou
python vpstellyou.py run
# 按 Ctrl+A，然后按 D 离开 screen
```

## 配置说明

### 邮件配置 (mail)

| 字段 | 说明 | 示例 |
|------|------|------|
| `sender` | 发件人邮箱（必填） | `xxx@qq.com` |
| `password` | SMTP 授权码（必填） | `abcdefghijklmnop` |
| `smtp_server` | SMTP 服务器（必填） | `smtp.qq.com` |
| `smtp_port` | SMTP 端口 | `465` (QQ 邮箱) |
| `use_tls` | 是否使用 SSL/TLS | `true` (QQ 邮箱) |
| `receivers` | 收件人列表 | `["xxx@qq.com", "yyy@qq.com"]` |
| `subject_in_stock` | 补货邮件标题模板 | `{name} 已经补货` |
| `content_in_stock` | 补货邮件内容模板 | 支持 `{name}` 和 `{url}` 变量 |
| `heartbeat_time` | 心跳邮件发送时间 | `08:00` (24小时格式) |
| `heartbeat_subject` | 心跳邮件标题模板 | 支持 `{name}` 和 `{time}` 变量 |
| `heartbeat_content` | 心跳邮件内容模板 | 支持 `{name}` 和 `{time}` 变量 |

### 全局配置 (global)

| 字段 | 说明 | 示例 |
|------|------|------|
| `check_interval` | 检查间隔（秒） | `60` |
| `log_level` | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 监控配置 (monitors)

每个监控项包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 套餐名称 | `DC6-512M-500G-49.9` |
| `url` | 监控页面 URL | `https://bwh88.net/cart.php?a=add&pid=94` |
| `pattern` | 缺货匹配正则表达式 | `Out of Stock` |

**关于 `pattern` 的说明**：

`pattern` 是用于识别"缺货"状态的正则表达式字符串。程序通过检查页面内容是否包含该字符串来判断商品状态：

- **页面包含** `pattern` → 视为**缺货**，仅记录日志
- **页面不包含** `pattern` → 视为**有货**，立即发送补货邮件

常见的缺货字样示例：
- 搬瓦工（BWH）：`Out of Stock`
- NetCup（德国）：`Produkt ist ausverkauft`
- RackNerd：`Out of Stock`
- 其他商家：`Sold Out`、`Not Available`、`缺货`、`售罄` 等

**如何获取正确的 `pattern`**：

1. 手动访问目标 URL，查看缺货时的页面内容
2. 在页面中找到明确表示"缺货"的文字
3. 将该文字复制到 `pattern` 字段（支持正则表达式）
4. 注意大小写和空格，建议使用页面中的原始文本

## 运行机制

### 补货检测

程序会定期访问 `monitors` 中配置的 URL，检查页面内容：

- 如果页面**不包含** `pattern`（如 "Out of Stock"），则视为**有货**，立即发送补货邮件
- 如果页面**包含** `pattern`，则视为**缺货**，仅记录日志

### 心跳邮件

当检测到缺货时，程序会在每天的 `heartbeat_time` 时间点发送心跳邮件，确认程序正常运行。

例如，设置 `heartbeat_time` 为 `08:00`，则每天早上 8:00 会收到心跳邮件（前提是所有监控项都缺货）。

### 日志记录

所有运行信息都会记录到脚本同目录的 `log.log` 文件中，包括：
- 程序启动信息
- 每次检查结果
- 邮件发送状态
- 错误信息

查看日志：

```bash
tail -f log.log
```

## 常见问题

### 1. 无法发送邮件

**症状**：运行 `python vpstellyou.py test` 提示发送失败

**解决方法**：
- 确认 QQ 邮箱已开启 SMTP 服务并获取了授权码
- 确认 `smtp_port` 为 `465`，`use_tls` 为 `true`
- 检查网络连接，确保可以访问 `smtp.qq.com`
- 查看 `log.log` 获取详细错误信息

### 2. 未触发补货通知

**症状**：页面已有货但未收到邮件

**解决方法**：
- 手动访问 `monitors.url`，查看页面内容
- 确认页面中是否包含或不包含 `pattern` 字符串
- 调整 `pattern` 使其精确匹配缺货状态
- 查看 `log.log` 确认请求是否成功

### 3. 未触发心跳邮件

**症状**：到了设定时间但没收到心跳邮件

**解决方法**：
- 确认 `heartbeat_time` 格式为 `HH:MM`（如 `08:00`）
- 心跳邮件只在所有监控项都缺货时才发送
- 心跳时间精确到分钟，检查间隔要小于 1 分钟才能保证触发
- 建议 `check_interval` 设置为 60 秒或更小

### 4. 其他邮箱配置

**Gmail**：
```json
"smtp_server": "smtp.gmail.com",
"smtp_port": 587,
"use_tls": true
```

**163 邮箱**：
```json
"smtp_server": "smtp.163.com",
"smtp_port": 465,
"use_tls": true
```

**注意**：不同邮箱提供商可能需要不同的授权方式，请查阅相应帮助文档。

## 命令说明

```bash
# 测试邮箱通讯
python vpstellyou.py test

# 开始循环监控
python vpstellyou.py run

# 查看帮助
python vpstellyou.py
```

## 配置文件示例

完整的配置文件示例请参考 `config.json.template`，支持多个监控目标：

```json
{
  "mail": {
    "sender": "xxx@qq.com",
    "password": "smtp授权码",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "use_tls": true,
    "receivers": ["xxx@qq.com", "yyy@qq.com"],
    "subject_in_stock": "{name} 已经补货",
    "content_in_stock": "购买地址是</br><a href=\"{url}\">点击购买 {name}</a>",
    "heartbeat_time": "08:00",
    "heartbeat_subject": "{name} 程序存活",
    "heartbeat_content": "{time} 心跳：{name} 正常运行"
  },
  "global": {
    "check_interval": 60,
    "log_level": "DEBUG"
  },
  "monitors": [
    {
      "name": "DC6-512M-500G-49.9",
      "url": "https://bwh88.net/cart.php?a=add&pid=94&aff=58257",
      "pattern": "Out of Stock"
    },
    {
      "name": "NetCup-1o",
      "url": "https://www.netcup.com/de/server/vps/vps-piko-g11s-12m",
      "pattern": "Produkt ist ausverkauft"
    }
  ]
}
```

## License

MIT
