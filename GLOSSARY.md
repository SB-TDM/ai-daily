# AI 日报

A poster for one Beijing calendar day that tells an internal group what AIHOT already selected.

## Language

**日报**:
The one poster image for one Beijing calendar day. It has no separate link message. The look is a light newspaper. It is labeled with the date, not an issue number.
_Avoid_: Digest, 纯文本, 卡片, briefing, 链接

**版式**:
The light, narrow, long newspaper look: a masthead, one lead, news sections, optional flashes, and a footer. Its length follows the day's content.
_Avoid_: 七格, 皮肤, theme, 动画

**板块**:
A named part of a 日报, such as the masthead, lead, a news section or flashes.
_Avoid_: 模块, section, 格子, component

**固定板块**:
The masthead and footer, which frame every 日报 without holding a separate news item.
_Avoid_: chrome, 角色

**新闻板块**:
A named group of news from the upstream daily, retaining its label and all items except the one already shown in the lead. 栏目 refers to the same grouping.
_Avoid_: 格子, 空格, 次条

**头版**:
The day's lead title and full introductory paragraph, shown once above the news sections. When it is an illustrated section's original first story, that illustration sits beside the paragraph; the source name belongs below the text.
_Avoid_: 头条, banner

**首条配图**:
The wordless illustration for a non-flash news section's original first story. If that story becomes the lead, its illustration moves with it rather than being assigned to the next story.
_Avoid_: 全报一张插图, 每条配图

**快讯**:
The brief news items following the other news sections, presented as text without generated illustrations.
_Avoid_: 底栏, ticker

**插图**:
A wordless editorial scene expressing a story's subject in the newspaper's muted palette. It is not a branded graphic or a chart of the story's statistics.
_Avoid_: 主图位, 数据图表, 品牌海报

**Upstream**:
AIHOT's published daily. A Run reads it. A Run does not collect.
_Avoid_: 收集项目, source, feed, crawler

**Run**:
One execution that reads the Upstream and may save one 日报. It does not send.
_Avoid_: job, cron, task, 任务

**召唤**:
One @ in the WeCom chat. The robot is already connected, so the message arrives without a public callback URL.
_Avoid_: 回调网址, webhook

**接收端**:
The part that stays connected to WeCom, answers one 召唤, and is not the image tool.
_Avoid_: 回调网址, 一次性进程

**指令**:
Text after an @ to the robot: 生成日报, 重新生成, 发送, 时间 HH:mm, 参数, or 帮助.
_Avoid_: command, 命令, 重发

**Item**:
One news unit the Run may assign to a 新闻板块.
_Avoid_: article, news, 新闻, entry
