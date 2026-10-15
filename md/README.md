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

`assets/` 保留正文使用的 46 张图片原文件作为本地备份。文件名由原始相对路径的 SHA-256 前 12 位生成；图片内容未修改。`assets-map.json` 记录本地资源路径与原始图片路径的对应关系。

正文图片已通过 `VCWSA-posts/Upload Images.md` 指定的 ImgBB API 上传，使用返回的 HTTPS 原图直链。上传名称统一使用“新生手册-2023-序号-图片信息”。`image-uploads.json` 记录每张图片的原始路径、标题、章节、原稿图注（如有）、尺寸、内容哈希、ImgBB ID、直链和查看页面，便于追溯与后台整理。清单不保存 API Key 或删除链接。

**相册归类待后台操作**：ImgBB 公开上传 API 不支持相册和描述字段。经确认，本次通过名称前缀标注“新生手册”，完整信息保存在本地清单；仍需在 ImgBB 后台将这些图片移入“新生手册”相册，不能将名称前缀视为已完成相册分类。

以后接入网站时，可将 `index.md` 复制到 `source-zh-CN/freshman-guide/2023/`，对应 `/freshman-guide/2023/`；远程图片无需复制 `assets/` 或启用 `post_asset_folder`。维护说明和映射文件不必复制到网站。当前未改动网站文件。

## 内容范围与重新转换

本次仅转换格式，保留源文档现有内容，包括其中不同年份的表述、数据、链接和可能存在的错误，没有进行事实核查或 2026 版修订。页面开头已明确注明版本。版权及致谢保留，沿用仓库原有 LaTeX 项目公共许可证 1.3c 或更高版本。

转换脚本位于 `scripts/convert-to-markdown.py`，需要 Python 3 与 Pandoc。在仓库根目录执行：

```sh
python3 scripts/convert-to-markdown.py
```

该命令会重新生成 `md/index.md`、`md/assets-map.json` 并复制图片。若存在上传清单，且本地图片哈希与上传记录一致，会复用已上传的 URL。若之后直接在 Markdown 中修订，请勿再次运行覆盖修订稿；应先保存改动，或将 TeX 转换作为一次性迁移。

上传脚本为 `scripts/upload-handbook-images.py`，优先读取环境变量 `IMGBB_API_KEY`，否则从上述上传说明读取，使用 `curl` 传输。脚本逐张保存成功记录，重新运行时跳过已成功上传的图片；全部成功后才批量替换正文链接。运行前应检查清单，避免在上传结果不明确的网络中断后重复上传。
