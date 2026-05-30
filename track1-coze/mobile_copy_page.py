"""手机端一键复制页面生成器

为每个产品生成一个 HTML，手机浏览器打开后：
  - 标题 → 点一下复制
  - 描述 → 点一下复制
  - 价格 → 点一下复制
  - 标签 → 点一下复制
  - 自动回复 → 点一下复制
  - 全部复制 → 一键全部打包

使用: python mobile_copy_page.py generate <product_id>
      python mobile_copy_page.py generate-all
"""
import json
import sys
import shutil
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent


def load_products():
    with open(HERE / "products.json", "r", encoding="utf-8") as f:
        return json.load(f)


CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:16px;-webkit-tap-highlight-color:transparent}
.header{text-align:center;padding:20px 0;margin-bottom:20px}
.header h1{font-size:22px;margin-bottom:6px}
.header .price{font-size:32px;font-weight:700;color:#f59e0b}
.header .premium{font-size:14px;color:#94a3b8}
.card{background:#1e293b;border-radius:16px;padding:16px;margin-bottom:14px;border:1px solid #334155}
.card-label{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.card-content{font-size:15px;line-height:1.6;word-break:break-all;color:#cbd5e1;max-height:120px;overflow-y:auto;margin-bottom:10px;white-space:pre-wrap}
.card-content.short{max-height:none}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 20px;border-radius:10px;border:none;font-size:14px;font-weight:600;cursor:pointer;transition:all .15s;user-select:none;-webkit-user-select:none}
.btn:active{transform:scale(.96)}
.btn-primary{background:#3b82f6;color:#fff;width:100%}
.btn-copy{background:#334155;color:#94a3b8;font-size:13px;padding:8px 16px}
.btn-copy.copied{background:#16a34a!important;color:#fff!important}
.btn-row{display:flex;gap:8px;margin-top:8px}
.btn-row .btn{flex:1}
.toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:10px 24px;border-radius:12px;font-size:14px;font-weight:600;z-index:999;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.show{opacity:1}
.section-title{font-size:16px;font-weight:700;margin:20px 0 12px;color:#f1f5f9}
.images-guide{background:#1e293b;border-radius:16px;padding:16px;margin-bottom:14px}
.images-guide ol{padding-left:20px;line-height:2}
.images-guide li{color:#94a3b8;font-size:14px}
.footer{text-align:center;padding:20px;color:#475569;font-size:12px}
"""

JS = """function copy(id,btn){
    var el=document.getElementById(id);
    var text=el.textContent||el.innerText;
    navigator.clipboard.writeText(text.trim()).then(function(){
        if(btn){
            var orig=btn.innerHTML;
            btn.innerHTML='[已复制]';
            btn.classList.add('copied');
            setTimeout(function(){btn.innerHTML=orig;btn.classList.remove('copied');},1500);
        }
    });
}
function copyAll(){
    var sections=['title','price','tags','desc','reply'];
    var all='';
    for(var i=0;i<sections.length;i++){
        var el=document.getElementById(sections[i]);
        if(el){
            var t=(el.textContent||el.innerText).trim();
            if(sections[i]==='price')t='价格: ¥'+t;
            if(sections[i]==='tags')t='标签: '+t;
            if(t)all+=t+'\\n';
        }
    }
    navigator.clipboard.writeText(all.trim()).then(function(){
        var toast=document.getElementById('toast');
        toast.textContent='全部复制完成! 去闲鱼粘贴吧';
        toast.classList.add('show');
        setTimeout(function(){toast.classList.remove('show');},2000);
    });
}
"""


def build_html(product_id: str) -> str:
    """生成单个产品的移动端 HTML"""
    products = load_products()
    product = next((p for p in products["products"] if p["id"] == product_id), None)
    if not product:
        return ""

    from xianyu_publisher import extract_listing_info
    info = extract_listing_info(product)

    title = info["title"]
    price = info["price"]
    prem_price = info["premium_price"]
    prem_name = info["premium_name"]
    desc = info["description"]
    tags = " ".join(f"#{t}" for t in info.get("tags", [])[:5])
    reply = f"你好！这个是Coze AI智能体模板，购买后发你导入文件，在你的Coze账号里用，永久有效～标准版¥{price}，{prem_name}¥{prem_price}。拍下秒发！"

    # Escape for HTML
    title_esc = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    desc_esc = desc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    tags_esc = tags.replace("&", "&amp;")
    reply_esc = reply.replace("&", "&amp;")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{product['name']} · 闲鱼上架</title>
<style>{CSS}</style>
</head>
<body>

<div class="header">
  <h1>{product['name']} · 上架助手</h1>
  <div class="price">¥{price}<span style="font-size:16px;font-weight:400;color:#94a3b8"> 起</span></div>
  <div class="premium">{prem_name} ¥{prem_price}</div>
</div>

<div id="toast" class="toast">已复制到剪贴板</div>

<!-- 标题 -->
<div class="card">
  <div class="card-label">商品标题 · 点下方复制</div>
  <div class="card-content short" id="title">{title_esc}</div>
  <button class="btn btn-copy" onclick="copy('title',this)">[复制标题]</button>
</div>

<!-- 价格 -->
<div class="card">
  <div class="card-label">价格</div>
  <div class="card-content short" id="price">{price}</div>
  <div class="btn-row">
    <button class="btn btn-copy" onclick="copy('price',this)">[复制价格]</button>
  </div>
</div>

<!-- 标签 -->
<div class="card">
  <div class="card-label">标签 · 最多5个</div>
  <div class="card-content short" id="tags">{tags_esc}</div>
  <button class="btn btn-copy" onclick="copy('tags',this)">[复制标签]</button>
</div>

<!-- 描述 -->
<div class="section-title">商品描述</div>
<div class="card">
  <div class="card-content" id="desc">{desc_esc}</div>
  <button class="btn btn-copy" onclick="copy('desc',this)">[复制描述]</button>
</div>

<!-- 自动回复 -->
<div class="section-title">自动回复</div>
<div class="card">
  <div class="card-content short" id="reply">{reply_esc}</div>
  <button class="btn btn-copy" onclick="copy('reply',this)">[复制自动回复]</button>
</div>

<!-- 全部复制 -->
<button class="btn btn-primary" onclick="copyAll()" style="margin-top:12px">
  一键复制全部 · 去闲鱼粘贴
</button>

<!-- 图片清单 -->
<div class="section-title">需要准备的图片</div>
<div class="images-guide">
  <ol>
    <li>封面图：大字标题 + 价格</li>
    <li>功能截图：Coze Bot 对话界面</li>
    <li>功能展示：核心能力 list</li>
    <li>使用步骤：1-2-3 图解</li>
    <li>版本对比：标准版 vs {prem_name}</li>
  </ol>
  <div style="margin-top:12px;font-size:13px;color:#64748b">
    📁 图片位置: exports/{product_id}/images/<br>
    🖼️ 运行 python image_generator.py generate {product_id} 自动生成
  </div>
</div>

<div class="footer">
  轨道1 · Coze模板上架系统<br>
  安全模式 · 零风控风险
</div>

<script>{JS}</script>
</body>
</html>"""
    return html


def generate_page(product_id: str):
    """生成单个产品的 HTML 页面"""
    html = build_html(product_id)
    if not html:
        print(f"产品不存在: {product_id}")
        return

    out_path = HERE / "exports" / product_id / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"已生成: {out_path}")
    print(f"  手机打开 → 点字段复制 → 去闲鱼粘贴")
    return out_path


def generate_all():
    """生成所有产品页面"""
    for p in load_products()["products"]:
        generate_page(p["id"])
    generate_index_page()


def generate_index_page():
    """生成产品列表首页"""
    products = load_products()
    items_html = ""
    for p in products["products"]:
        items_html += f"""    <a href="{p['id']}/index.html" class="product-card">
      <div class="product-name">{p['name']}</div>
      <div class="product-price">¥{p['pricing']['standard']} 起</div>
      <div class="product-status">{p.get('闲鱼上架状态','待上架')}</div>
    </a>
"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>轨道1 · 上架助手</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:16px}}
h1{{font-size:22px;text-align:center;padding:20px 0}}
.subtitle{{text-align:center;color:#64748b;font-size:13px;margin-bottom:20px}}
.product-card{{display:block;background:#1e293b;border-radius:14px;padding:16px 20px;margin-bottom:10px;text-decoration:none;color:#e2e8f0;border:1px solid #334155;transition:all .15s}}
.product-card:active{{background:#334155}}
.product-name{{font-size:16px;font-weight:600;margin-bottom:4px}}
.product-price{{color:#f59e0b;font-size:18px;font-weight:700}}
.product-status{{font-size:12px;color:#64748b;margin-top:4px}}
.footer{{text-align:center;padding:20px;color:#475569;font-size:12px}}
</style>
</head>
<body>
<h1>轨道1 · 上架助手</h1>
<div class="subtitle">点产品进入 → 一键复制 → 去闲鱼粘贴</div>
{items_html}
<div class="footer">安全模式 · 零风控风险</div>
</body>
</html>"""

    index_path = HERE / "exports" / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"首页已生成: {index_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "generate":
        pid = sys.argv[2] if len(sys.argv) > 2 else None
        if pid:
            generate_page(pid)
        else:
            print("用法: python mobile_copy_page.py generate <product_id>")
    elif cmd == "generate-all":
        generate_all()
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
