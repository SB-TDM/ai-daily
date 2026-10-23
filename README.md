# AI 日报

把 AIHOT 当天日报排成已确认的浅色长条报纸。生成不发群。

```powershell
python -m ai_daily generate
python -m ai_daily generate --force
python -m ai_daily generate --report report.json --offline
```

图片保存在 `data/posters/当天日期.png`。模型、地址和密钥分别放在 `data/image.json` 与 `data/image-secret.json`。

每个非快讯板块只给原始第一条配图。头版复用其所在板块的首条图，不重复。快讯不配图。单张插图失败时，该条只印文字。

接收端：

```powershell
python -m ai_daily serve
```

它听 `127.0.0.1:8787/wecom`。`.env` 还需要 `WECOM_TOKEN` 和 `WECOM_ENCODING_AES_KEY`，缺了就拒绝启动，不打印凭证。`@发送` 才走 webhook。生成只回文字，不发图。

## 正式服

先把 `daily.string.ink` 解析到 `38.147.163.155`。解析未生效时，不加站点、不启容器。

在服务器的单独目录运行 `docker compose up -d --build`。容器只发布 `127.0.0.1:8787`。把 `.env`、`data/image.json`、`data/image-secret.json` 放进 `runtime/`，三份字体放进 `fonts/`。这些文件不进镜像。

用 `certificate_from_dump` 从现有 nginx 配置取出 `string.ink` 的证书路径，把 `nginx_site` 的结果写成新文件 `/etc/nginx/conf.d/daily.string.ink.conf`。不编辑原站点。`nginx -t` 通过后再 reload。

确认 `https://daily.string.ink/wecom` 有响应。没签名时拒绝是正常的。同时确认 `https://string.ink` 仍是原来的网站。然后才把网址填进企微并保存。保存成功后，群里只试 `@生成日报`，先不 `@发送`。
