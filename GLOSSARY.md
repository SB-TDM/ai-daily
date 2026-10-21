# AI Digest

A weekday poster that tells an internal team what happened in AI.

## Language

**日报**:
The one screenshot for one Beijing calendar day. The words come from that day's aihot.news daily. It has no character. It is labeled with the date, not an issue number. It is sent as one image. Words on it cannot be tapped.
_Avoid_: Digest, 纯文本, 卡片, briefing, 推送

**版式**:
The HTML page that is screenshotted into a 日报. 报头 and the footer are part of the page. There is no character. aihot's lead and sections are placed in their order.
_Avoid_: 七格, 皮肤, theme, 模具

**Upstream**:
The aihot.news daily for one Beijing date, read from `https://aihot.news/api/v1/dailies/YYYY-MM-DD`.
_Avoid_: 收集项目, source, feed, crawler, agents-radar

**Run**:
One execution that reads today's aihot daily and may send one 日报. A Beijing workday stays open until a 日报 is sent.
_Avoid_: job, cron, task, 任务

**快讯**:
The `flashes` list on an aihot daily, or a section labeled 快讯. A 日报 does not draw it.
_Avoid_: 短讯, ticker

**素材板块**:
Do not use. The mold library was rejected. The page follows aihot's own sections.
_Avoid_: 大标题板, 短标题板, 双栏板, 便签, 模具

**兜底**:
Do not use. There is no model fill, and no second fill rule.
_Avoid_: 硬填, fallback

**Item**:
Do not use. A line on the page is an aihot section item: title, summary, and source name.
_Avoid_: article, news, 新闻, entry
