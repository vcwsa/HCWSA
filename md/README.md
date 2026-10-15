# Markdown 版手册

[打开完整手册](index.md)

本目录将 `hcwsa.tex` 引用的五份正文文件按原顺序合并为 `index.md`，包括制作团队、序言、修订、三章正文及后记与致谢，并保留封面和封底。子目录中的 `Bank.tex`、`RWTHApp.tex` 和 `Mensa.tex` 是独立的图片排版源文件，不是额外章节；正文实际使用的图片均已收录。

## 与学联网站的格式对应

已参考 `/config/workspace/vcwsa.de` 的 `_config.yml`、`scaffolds/post.md`、中文文章，以及 `source-zh-CN/freshman-guide/index.md`：

- 网站为 Hexo + Butterfly，中文内容位于 `source-zh-CN`，使用 `hexo-renderer-marked`。
- 手册沿用独立页面的 YAML front matter，设置 `layout: page`，提供 `title`、`subtitle`、`keywords`、`description` 等字段。原稿只注明 2023 年 10 月，因此不编造具体的发布日期。
- 页面标题交给主题展示，正文使用二级至四级标题；保留一份可在本地使用的目录。
- 强调、外链、邮件链接、列表、图片和引用块使用标准 Markdown。原邮件模板改为引用块，列表的续编号保留。
- 文内引用使用显式 HTML 锚点和 Markdown 链接，不依赖主题自动生成的中文标题 ID。原来的章节号和图号改为对应标题或图注链接。
- 脚注使用 HTML 上标链接与文末注释，并提供返回正文链接，避免依赖网站未配置的 Markdown 脚注扩展。
- 唯一的银行比较表使用 HTML 表格保留 `colspan` 合并单元格。图片改为纵向排列，图注保留原文；原稿中“左图”“右图”等印刷版方位描述保留。

## 图片与迁移

`assets/` 收录正文实际引用的 46 张图片，使用相对链接，例如 `assets/34a747eec504.png`。文件名由原始相对路径的 SHA-256 前 12 位生成，避免空格、括号、中文或德文字符影响链接解析；图片内容未修改。`assets-map.json` 记录本地资源路径与原始图片路径的对应关系，方便后续调用图床 API 上传并替换链接。

以后接入网站时，可将 `index.md` 与 `assets/` 一起复制到 `source-zh-CN/freshman-guide/2023/`，对应 `/freshman-guide/2023/`；无需启用 `post_asset_folder`。维护说明和映射文件不必复制到网站。当前未改动网站文件，也未上传图片。

## 内容范围与重新转换

本次仅转换格式，保留源文档现有内容，包括其中不同年份的表述、数据、链接和可能存在的错误，没有进行事实核查或 2026 版修订。页面开头已明确注明版本。版权及致谢保留，沿用仓库原有 LaTeX 项目公共许可证 1.3c 或更高版本。

转换脚本位于 `scripts/convert-to-markdown.py`，需要 Python 3 与 Pandoc。在仓库根目录执行：

```sh
python3 scripts/convert-to-markdown.py
```

该命令会重新生成 `md/index.md`、`md/assets-map.json` 并复制图片。若之后直接在 Markdown 中修订，请勿再次运行覆盖修订稿；应先保存改动，或将 TeX 转换作为一次性迁移。
