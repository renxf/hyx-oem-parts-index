#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HYX OEM Parts Index — 生成脚本
================================
从 data/products.json 生成:
  README.md              仓库首页(概览 + 用法 + 示例 + 指向全量索引)
  docs/<cat>.md          每条产品线的完整 OE 对照表(Markdown)
  data/oe-index.csv      机器可读对照表
  data/oe-index.json     机器可读对照表(JSON)
  index.html             GitHub Pages 首页(全量表 + 实时筛选)
  category/<cat>.html    GitHub Pages 分类页(全量表 + 实时筛选)

用法:
  python3 tools/build_index.py

数据来源: https://hyxautoparts.com/data/products.json
所有 OE 件号与适配信息均来自工厂质检单 / 出货装箱单,不做任何编造或猜测。
"""
import csv
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://hyxautoparts.com"
REPO = "https://github.com/renxf/hyx-oem-parts-index"
PAGES = "https://renxf.github.io/hyx-oem-parts-index"
EMAIL = "sales@hyxautoparts.com"

CATS = {
    "handle-cam": {
        "zh": "尾门拉手摄像头",
        "en": "Tailgate Handle Camera",
        "slug": "tailgate-handle-camera",
        "kw_zh": "尾门拉手摄像头、尾门拉手总成、拉门摄像头、后备箱拉手带摄像头",
        "kw_en": "tailgate handle camera, tailgate handle assembly, liftgate camera, trunk handle camera",
    },
    "parking-cam": {
        "zh": "倒车摄像头",
        "en": "Parking / Reverse Camera",
        "slug": "parking-camera",
        "kw_zh": "倒车摄像头、后视摄像头、泊车摄像头、驻车摄像头",
        "kw_en": "parking camera, reverse camera, backup camera, rear view camera, reversing camera",
    },
    "turbo-actuator": {
        "zh": "涡轮增压器执行器",
        "en": "Turbocharger Actuator",
        "slug": "turbocharger-actuator",
        "kw_zh": "涡轮增压器执行器、涡轮执行器、废气旁通阀执行器、涡轮增压器调节器",
        "kw_en": "turbocharger actuator, turbo actuator, wastegate actuator, turbocharger control valve",
    },
}

CJK = re.compile(r"[\u4e00-\u9fff]")


def clean_oe(v):
    """件号清洗(与站点 tools/gen_seo.py 同一套规则):
    去首尾空白 + 去首尾逗号(源 PDF 一格里用逗号分隔多个件号,切分后残留尾逗号)"""
    return str(v or "").strip().strip(",").strip()


def is_real_oe(v):
    """真实件号 = 非空 + 不含中文(源 PDF 有一格填的是描述文字,不是件号)"""
    v = clean_oe(v)
    return bool(v) and not CJK.search(v)


def nat_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s or "")]


def load():
    with open(os.path.join(ROOT, "data", "products.json"), encoding="utf-8") as f:
        return json.load(f)


def build_rows(products):
    rows = []
    for p in products:
        cat = p.get("category") or ""
        if cat not in CATS:
            continue
        url = f"{SITE}/{p.get('page') or ''}"
        fit = "、".join(p.get("fitment_models") or [])
        for oe in (p.get("oe_list") or []):
            if not is_real_oe(oe):
                continue
            rows.append({
                "oe": clean_oe(oe),
                "factory": p.get("factory") or "",
                "cat": cat,
                "cat_slug": CATS[cat]["slug"],
                "brand": p.get("brand") or "",
                "model_zh": p.get("name_zh") or p.get("name") or "",
                "model_en": p.get("name_en") or "",
                "fitment": fit,
                "moq": p.get("moq") or 10,
                "price_ref": p.get("price_ref") or "",
                "url": url,
                "sn": p.get("sn"),
            })
    rows.sort(key=lambda r: (nat_key(r["oe"]), r["factory"]))
    return rows


def md_cell(v):
    return str(v or "").replace("|", "\\|").replace("\n", " ").strip() or "—"


# ------------------------------------------------------------------ README
def build_readme(products, rows):
    uniq = len({r["oe"] for r in rows})
    per_cat = {}
    for c in CATS:
        rs = [r for r in rows if r["cat"] == c]
        per_cat[c] = {
            "sku": len({r["sn"] for r in rs}),
            "oe": len({r["oe"] for r in rs}),
            "rows": len(rs),
        }
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    L = []
    a = L.append
    a("# HYX OEM Parts Index · 皓盈轩原厂件号公开索引")
    a("")
    a("[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) "
      "[![Part numbers](https://img.shields.io/badge/OE%20part%20numbers-1157-blue.svg)]() "
      "[![SKUs](https://img.shields.io/badge/SKUs-503-blue.svg)]()")
    a("")
    a(f"> **{uniq}** 个原厂 OE 件号 · **{len(products)}** 个在售 SKU · **3** 条产品线 · MIT 协议开放数据  ")
    a(f"> 官方站点: <{SITE}> · 在线筛选: <{PAGES}> · 询价: <{EMAIL}>")
    a("")
    a("本仓库是 [hyxautoparts.com](https://hyxautoparts.com) 的**公开件号索引**。"
      "每个 OE 号都直接对应官网上的一个产品页(带 OE 对照表、适配车型、尺寸重量、常见问题与询价入口),"
      "方便采购、汽配店和贸易商按原厂件号反查型号。")
    a("")
    a("所有件号与适配信息均来自工厂质检单与出货装箱单,**不编造件号、不猜测品牌与车型**;"
      "源数据缺失的条目在索引里如实留空。")
    a("")
    a("---")
    a("")
    a("## English summary")
    a("")
    a(f"Open, machine-readable index of **{uniq} unique OEM/OE part numbers** across **{len(products)} SKUs** "
      "in three product lines: **tailgate handle cameras**, **parking / reverse cameras** and "
      "**turbocharger actuators**.")
    a("")
    a("Every part number links to its own product page on [hyxautoparts.com](https://hyxautoparts.com), "
      "where you can check the full OE cross-reference table, fitment list, dimensions, weight, MOQ and request a quote. "
      "Part numbers and fitment data come from our factory QC sheets and packing lists — nothing is guessed.")
    a("")
    a("Use it to: look up an OE number → confirm the matching SKU and factory code → send a quote request.")
    a("")
    a("---")
    a("")
    a("## 数据概览 / At a glance")
    a("")
    a("| 项目 / Item | 数值 / Value |")
    a("| --- | --- |")
    a(f"| 唯一 OE 件号 / Unique OEM part numbers | {uniq} |")
    a(f"| 在售 SKU / Listed SKUs | {len(products)} |")
    a(f"| OE ↔ SKU 对照关系 / OE-to-SKU rows | {len(rows)} |")
    a(f"| 产品线 / Product lines | {len(CATS)} |")
    a(f"| 最低起订量 / MOQ | {min((r['moq'] for r in rows), default=10)} pcs (可混批 / mixed SKU allowed) |")
    a(f"| 出口 / Export | 30+ countries · DDP / FOB / EXW · 海运 / 空运 / 快递 |")
    a(f"| 响应 / Response | 询盘 2 小时内回复报价单 / quote within 2 hours |")
    a(f"| 数据更新 / Data updated | {stamp} |")
    a("")
    a("## 怎么用 / How to use")
    a("")
    a("1. **按 OE 号查** — 在下面的索引或 [在线筛选页](%s) 搜件号,得到 SKU 与工厂号。" % PAGES)
    a("2. **核对适配** — 点进产品页,对照 OE 对照表、适配车型与尺寸重量。")
    a("3. **询价** — 产品页底部填数量与收货信息,或直接邮件 %s。" % EMAIL)
    a("")
    a("1. **Look up by OE number** — search the index below or on the [live filter page](%s)." % PAGES)
    a("2. **Verify fitment** — open the product page for the OE cross-reference table, fitment list and dimensions.")
    a("3. **Request a quote** — use the form on the product page, or email %s." % EMAIL)
    a("")
    a("## 产品线 / Product lines")
    a("")
    a("| 产品线 / Line | SKU | 唯一 OE / Unique OE | 官网分类页 / Category page | 完整索引 / Full index |")
    a("| --- | --- | --- | --- | --- |")
    for c, v in CATS.items():
        p = per_cat[c]
        a(f"| {v['zh']} / {v['en']} | {p['sku']} | {p['oe']} | "
          f"[{SITE}/category/{v['slug']}]({SITE}/category/{v['slug']}) | "
          f"[docs/{v['slug']}.md](docs/{v['slug']}.md) · [网页版]({PAGES}/category/{v['slug']}.html) |")
    a("")
    for c, v in CATS.items():
        a(f"- **{v['zh']} / {v['en']}** — 关键词: {v['kw_zh']} / {v['kw_en']}")
    a("")
    a("## 完整索引 / Full index")
    a("")
    a("| 形式 / Format | 位置 / Where | 说明 / Notes |")
    a("| --- | --- | --- |")
    a(f"| 在线可筛选 / Live filter | [{PAGES}]({PAGES}) | 全量 %d 行,输入 OE / 品牌 / 车型实时过滤 |" % len(rows))
    a(f"| Markdown 表 / Markdown | [docs/](docs/) | 每条产品线一个文件,GitHub 直接渲染 |")
    a(f"| CSV | [data/oe-index.csv](data/oe-index.csv) | %d 行 × %d 列,适合 Excel / 导入 ERP |" % (len(rows), 11))
    a(f"| CSV(在线) | [{PAGES}/data/oe-index.csv]({PAGES}/data/oe-index.csv) | 同一份 CSV,可直接 wget |")
    a(f"| JSON | [data/oe-index.json](data/oe-index.json) | 结构化数组,适合程序调用 |")
    a(f"| JSON(在线) | [{PAGES}/data/oe-index.json]({PAGES}/data/oe-index.json) | 同一份 JSON,可直接调接口 |")
    a(f"| 全量产品数据 / Full product data | [data/products.json](data/products.json) | 含图片、尺寸、重量、参考价、MOQ |")
    a(f"| 全站 URL 清单 / Sitemap | [{SITE}/sitemap.xml]({SITE}/sitemap.xml) | %d 个页面 URL |" % (len(products) + 6))
    a("")
    a("### 索引示例 / Sample rows")
    a("")
    a("| OE 号 | 品类 | 工厂号 | 品牌 | 车型 | 产品页 |")
    a("| --- | --- | --- | --- | --- | --- |")
    for r in rows[:25]:
        a(f"| `{md_cell(r['oe'])}` | {CATS[r['cat']]['zh']} | {md_cell(r['factory'])} | "
          f"{md_cell(r['brand'])} | {md_cell(r['model_zh'])} | [产品页]({r['url']}) |")
    a("")
    a("## 数据字段 / Schema")
    a("")
    a("`data/oe-index.csv` 列定义:")
    a("")
    a("| 列 / Column | 说明 / Meaning |")
    a("| --- | --- |")
    a("| `oe` | 原厂 OE 件号 / OEM part number |")
    a("| `factory` | 工厂目录编号(询价报这个最快) / factory code |")
    a("| `category` | 产品线 / product line |")
    a("| `category_en` | 产品线(英文) / product line (EN) |")
    a("| `brand` | 适用品牌 / vehicle brand |")
    a("| `model_zh` | 车型(中文) / fitment model (zh) |")
    a("| `model_en` | 车型(英文) / fitment model (en) |")
    a("| `fitment` | 适配车型列表 / fitment list |")
    a("| `moq` | 最低起订量 / minimum order quantity |")
    a("| `price_ref_cny` | 批发参考价(CNY,仅部分 SKU 公开) / reference price |")
    a("| `product_url` | 官网产品页 / product page URL |")
    a("")
    a("## 商务联系 / Business")
    a("")
    a("- 公司 / Company: HYX 皓盈轩 / HYX Auto Parts(中国汽配出口供应商,工厂直供)")
    a(f"- 站点 / Site: {SITE}")
    a(f"- 邮箱 / Email: {EMAIL}")
    a("- 支持 / Support: OEM / ODM 贴牌、混批、跨境物流(DDP / FOB / EXW)")
    a("")
    a("## 来源与许可 / Source & License")
    a("")
    a(f"- 数据源 / Source: [{SITE}/data/products.json]({SITE}/data/products.json) — 本站公开产品数据,随站点更新同步")
    a(f"- 官方站点 / Official site: {SITE}")
    a("- 许可 / License: [MIT](LICENSE) — 可自由使用、修改与再分发;引用时请链接到具体产品页,不要整站镜像")
    a("")
    a("---")
    a("")
    a(f"<sub>本仓库由 [hyxautoparts.com]({SITE}) 自动生成 · {stamp}</sub>")
    a("")
    return "\n".join(L)


# ------------------------------------------------------------------ docs
def build_docs(products, rows):
    out = {}
    for c, v in CATS.items():
        rs = [r for r in rows if r["cat"] == c]
        L = []
        a = L.append
        a(f"# {v['zh']} / {v['en']} — OE 件号索引")
        a("")
        a(f"{len({r['oe'] for r in rs})} 个唯一 OE 件号 · {len({r['sn'] for r in rs})} 个 SKU · {len(rs)} 条对照关系")
        a("")
        a(f"- 官网分类页 / Category page: {SITE}/category/{v['slug']}")
        a(f"- 关键词 / Keywords: {v['kw_zh']} / {v['kw_en']}")
        a(f"- 在线筛选 / Live filter: {PAGES}/category/{v['slug']}.html")
        a("")
        a("| OE 号 | 工厂号 | 品牌 | 车型 | MOQ | 参考价 CNY | 产品页 |")
        a("| --- | --- | --- | --- | --- | --- | --- |")
        for r in rs:
            a(f"| `{md_cell(r['oe'])}` | {md_cell(r['factory'])} | {md_cell(r['brand'])} | "
              f"{md_cell(r['model_zh'])} | {r['moq']} | {r['price_ref'] or '—'} | [{r['factory']}]({r['url']}) |")
        a("")
        out[v["slug"]] = "\n".join(L)
    return out


# ------------------------------------------------------------------ HTML
HTML_CSS = """
:root{--navy:#0d1b2a;--navy-d:#081420;--amber:#f0a500;--line:#e5e9ef;--ink:#16202c;--mut:#5b6876}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:#f7f9fc}
header{background:linear-gradient(135deg,var(--navy),#16324a);color:#fff;padding:34px 0 26px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
h1{margin:0 0 6px;font-size:27px}
.sub{opacity:.82;margin:0;font-size:14px;line-height:1.7}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.stat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:8px;padding:8px 14px;font-size:13px}
.stat b{color:var(--amber);font-size:17px;margin-right:6px}
nav.top{padding:14px 0 0}
nav.top a{display:inline-block;margin:0 14px 8px 0;color:#dbe6f0;font-size:14px;text-decoration:none}
nav.top a:hover{color:var(--amber)}
.toolbar{position:sticky;top:0;z-index:9;background:#fff;border-bottom:1px solid var(--line);padding:12px 0}
.toolbar .wrap{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
input[type=search]{flex:1;min-width:260px;padding:10px 14px;border:1px solid var(--line);border-radius:8px;font-size:14px}
.count{font-size:13px;color:var(--mut)}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13.5px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef2f7;position:sticky;top:56px;font-size:12.5px;color:#41505f}
td.mono,th.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
tr:hover td{background:#fbfcfe}
.pill{display:inline-block;background:#eef2f7;border-radius:20px;padding:1px 9px;font-size:12px}
section.blk{padding:26px 0}
footer{background:var(--navy-d);color:rgba(255,255,255,.7);padding:22px 0;font-size:13px;margin-top:30px}
footer a{color:#9fc6e8}
"""

HTML_JS = """
function filt(){
  var q=(document.getElementById('q').value||'').toLowerCase().trim();
  var rows=document.querySelectorAll('tbody tr');
  var n=0;
  for(var i=0;i<rows.length;i++){
    var t=rows[i].textContent.toLowerCase();
    var show=!q||t.indexOf(q)>-1;
    rows[i].style.display=show?'':'none';
    if(show)n++;
  }
  document.getElementById('cnt').textContent=n+' / '+rows.length+' 行 / rows';
}
document.getElementById('q').addEventListener('input',filt);
filt();
"""


def html_page(title, desc, rows, products, c=None):
    v = CATS[c] if c else None
    n_oe = len({r["oe"] for r in rows})
    n_sku = len({r["sn"] for r in rows})
    L = []
    a = L.append
    a("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
    a(f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    a(f"<title>{title}</title>")
    a(f"<meta name=\"description\" content=\"{desc}\">")
    a(f"<link rel=\"canonical\" href=\"{PAGES}/{'category/' + v['slug'] + '.html' if c else ''}\">")
    a(f"<style>{HTML_CSS}</style></head><body>")
    a("<header><div class=\"wrap\">")
    a(f"<h1>{title}</h1>")
    a(f"<p class=\"sub\">{desc}</p>")
    a("<div class=\"stats\">")
    a(f"<span class=\"stat\"><b>{n_oe}</b> 个唯一 OE 件号 / unique OE numbers</span>")
    a(f"<span class=\"stat\"><b>{n_sku}</b> 个 SKU</span>")
    a(f"<span class=\"stat\"><b>{len(rows)}</b> 条对照关系 / rows</span>")
    a("<span class=\"stat\">官方站点 / Official site: hyxautoparts.com</span>")
    a("</div>")
    a("<nav class=\"top\">")
    a(f"<a href=\"{PAGES}/\">← 全部分类 / All categories</a>")
    for cc, vv in CATS.items():
        a(f"<a href=\"{PAGES}/category/{vv['slug']}.html\">{vv['zh']} / {vv['en']}</a>")
    a(f"<a href=\"{SITE}/catalog\">官网总表 / Official catalog</a>")
    a(f"<a href=\"{REPO}\">GitHub 仓库 / Source repo</a>")
    a("</nav></div></header>")
    a("<div class=\"toolbar\"><div class=\"wrap\">")
    a("<input type=\"search\" id=\"q\" placeholder=\"输入 OE 号 / 工厂号 / 品牌 / 车型 — e.g. 06L145612, 2AD001, Audi\">")
    a("<span class=\"count\" id=\"cnt\"></span>")
    a("</div></div>")
    a("<section class=\"blk\"><div class=\"wrap\"><table><thead><tr>")
    a("<th class=\"mono\">OE 号 / OE number</th><th>工厂号 / Factory</th><th>品牌 / Brand</th>")
    a("<th>车型 / Model</th><th>适配 / Fitment</th><th>MOQ</th><th>参考价 / Ref price</th><th>产品页 / Product page</th>")
    a("</tr></thead><tbody>")
    for r in rows:
        fit = r["fitment"] or "—"
        a("<tr>"
          f"<td class=\"mono\">{md_cell(r['oe'])}</td>"
          f"<td class=\"mono\">{md_cell(r['factory'])}</td>"
          f"<td>{md_cell(r['brand'])}</td>"
          f"<td>{md_cell(r['model_zh'])}</td>"
          f"<td>{md_cell(fit)}</td>"
          f"<td>{r['moq']}</td>"
          f"<td>{r['price_ref'] or '—'}</td>"
          f"<td><a href=\"{r['url']}\">产品页 / page →</a></td>"
          "</tr>")
    a("</tbody></table></div></section>")
    a(f"<footer><div class=\"wrap\">")
    a(f"© 2026 HYX 皓盈轩 HYX Auto Parts · 官方站点 <a href=\"{SITE}\">{SITE}</a> · "
      f"询价 <a href=\"mailto:{EMAIL}\">{EMAIL}</a> · "
      f"数据 <a href=\"{REPO}\">GitHub</a> · MIT License")
    a("</div></footer>")
    a(f"<script>{HTML_JS}</script></body></html>")
    return "\n".join(L)


# ------------------------------------------------------------------ data
def write_csv(rows):
    p = os.path.join(ROOT, "data", "oe-index.csv")
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["oe", "factory", "category", "category_en", "brand", "model_zh",
                    "model_en", "fitment", "moq", "price_ref_cny", "product_url"])
        for r in rows:
            w.writerow([r["oe"], r["factory"], CATS[r["cat"]]["zh"], CATS[r["cat"]]["en"],
                        r["brand"], r["model_zh"], r["model_en"], r["fitment"],
                        r["moq"], r["price_ref"], r["url"]])
    return p


def write_json(rows):
    p = os.path.join(ROOT, "data", "oe-index.json")
    out = []
    for r in rows:
        out.append({
            "oe": r["oe"], "factory": r["factory"],
            "category": CATS[r["cat"]]["zh"], "category_en": CATS[r["cat"]]["en"],
            "brand": r["brand"], "model_zh": r["model_zh"], "model_en": r["model_en"],
            "fitment": r["fitment"], "moq": r["moq"],
            "price_ref_cny": r["price_ref"] or None,
            "product_url": r["url"],
        })
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return p


LICENSE = """MIT License

Copyright (c) 2026 HYX Auto Parts (hyxautoparts.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

Data note: Part numbers and fitment data are published by HYX Auto Parts under
the same terms. When quoting this dataset, please link to the specific product
page on https://hyxautoparts.com rather than mirroring the whole site.
"""


def main():
    products = load()
    rows = build_rows(products)

    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(build_readme(products, rows))
    print("✅ README.md")

    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    for slug, txt in build_docs(products, rows).items():
        with open(os.path.join(ROOT, "docs", slug + ".md"), "w", encoding="utf-8") as f:
            f.write(txt)
    print("✅ docs/*.md")

    print("✅", write_csv(rows))
    print("✅", write_json(rows))

    with open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8") as f:
        f.write(LICENSE)
    print("✅ LICENSE")

    os.makedirs(os.path.join(ROOT, "category"), exist_ok=True)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_page(
            "HYX OEM Parts Index · 皓盈轩原厂件号公开索引",
            f"{len({r['oe'] for r in rows})} 个原厂 OE 件号 · {len(products)} 个 SKU · 尾门拉手摄像头 / 倒车摄像头 / 涡轮增压器执行器 · "
            "Open index of OEM part numbers for tailgate handle cameras, parking cameras and turbocharger actuators.",
            rows, products))
    print("✅ index.html")
    for c, v in CATS.items():
        rs = [r for r in rows if r["cat"] == c]
        with open(os.path.join(ROOT, "category", v["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(html_page(
                f"{v['zh']} / {v['en']} — OE 件号索引",
                f"{len({r['oe'] for r in rs})} 个原厂 OE 件号 · {len({r['sn'] for r in rs})} 个 SKU · 关键词: {v['kw_zh']} / {v['kw_en']}",
                rs, products, c))
    print("✅ category/*.html")

    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    print("✅ .nojekyll")

    print(f"\n📊 唯一 OE: {len({r['oe'] for r in rows})} | SKU: {len(products)} | 对照行: {len(rows)}")


if __name__ == "__main__":
    main()
