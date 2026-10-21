# AI Digest

A weekday poster that tells an internal team what happened in AI.

## Language

**日报**:
The one poster image for one Beijing calendar day. It uses the light-anime look. It has no character. The words change. It is labeled with the date, not an issue number. It is sent as one image. Words on it cannot be tapped.
_Avoid_: Digest, 纯文本, 卡片, briefing, 推送

**版式**:
The light-anime paper of a 日报. 报头 and the footer are part of the paper. There is no character. Filled molds are pasted onto it.
_Avoid_: 七格, 皮肤, theme

**素材板块**:
A reusable visual mold. It holds no news until it is filled. The title, the sentence, and the category name are filled in. A filled mold is then pasted onto the 日报. The library is 大标题板, 短标题板, and 双栏板.
_Avoid_: 便签, 论文格, 开源格, 空格, 板块目录

**大标题板**:
The mold for one important item. It holds a category name, a large title, and one sentence.
_Avoid_: 头版, banner

**短标题板**:
The mold for one lesser item. It holds a category name and a short title, and no sentence.
_Avoid_: 导读, ticker

**双栏板**:
The mold for two lesser items side by side. Each side holds a category name and a short title.
_Avoid_: 底栏, 三栏

**板块**:
A 素材板块 after it has been filled, or the mold itself. Use 素材板块 when the empty mold must be distinct from the filled piece.
_Avoid_: 模块, section, 格子, component

**Upstream**:
A news list that another project already prepared.
_Avoid_: 收集项目, source, feed, crawler

**Run**:
One execution that reads Upstreams and may send one 日报. A Beijing workday stays open until a 日报 is sent.
_Avoid_: job, cron, task, 任务

**兜底**:
Filling a mold by fixed rules when the model fills none. The filled molds are still pasted onto the 日报.
_Avoid_: 硬填, fallback

**Item**:
One news unit that may be filled into a 素材板块.
_Avoid_: article, news, 新闻, entry
