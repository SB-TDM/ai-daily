# AI 日报

一条命令。它读取 [aihot.news](https://aihot.news) 北京时间当天已经写好的日报，排成一页浅粉报纸，截成一张图，发到企微群。

这不是网站，不是企微应用，也不是新闻采集器。群里只收到那一张图。

## 它做什么

- 只读 `https://aihot.news/api/v1/dailies/YYYY-MM-DD`。
- 排成两栏网格。报头、头条和栏目名跨两栏，每条新闻占一格。头条不在栏目里重复。图片只等比例缩小，不裁切。
- 插画用 `OPENAI_API_KEY` 调用出图接口，默认 `https://www.string.ink/v1`，模型 `grok-imagine-image`。失败会再试两次。密钥不要写进仓库。没有密钥或出图失败，就只印文字。
- 不画快讯，不放角色，不印网址，不写期号，不写「内部传阅」。
- 截图超过 2MB，或截图、发送失败，都不把今天记成已发。
- 同一天已经发过，就停止。

命令不判断周末。工作日由外部时钟决定。

## 环境

- Python 3.11 或更高
- Playwright 的 Chromium

```powershell
python -m pip install httpx playwright tzdata pillow
python -m playwright install chromium
```

企微群机器人的 webhook 只放在环境变量里，不要写进仓库。

```powershell
$env:WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
$env:OPENAI_API_KEY = "sk-..."
```

已发日期默认记在 `data/sent.json`。要换位置：

```powershell
$env:AI_DAILY_STATE_PATH = "D:\ai-daily\sent.json"
```

## 运行

在仓库根目录：

```powershell
$env:PYTHONPATH = "src"
python -m ai_daily
```

输出是 `sent`、`already-sent`、`not-ready` 或 `delivery-failed`。

| 退出码 | 含义 |
| --- | --- |
| 0 | 已发出，或今天已经发过 |
| 1 | 当天日报还没有，或截图、发送失败 |
| 2 | 没有设置 `WECOM_WEBHOOK_URL` |

## 测试

```powershell
$env:PYTHONPATH = "src"
python -m pytest
```
