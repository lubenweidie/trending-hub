"""今日头条发布器（头条号 mp.toutiao.com）"""
import ctypes
import ctypes.wintypes
import json
import re
import time
from .base import BasePublisher
from .browser_utils import FIND_EL_JS, REACT_CLICK_JS, LOAD_IMAGE_JS_TEMPLATE

TOUTIAO_EDIT_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"

# 标题选择器（头条标题是 textarea）
TITLE_SELECTORS = (
    'textarea[placeholder*="文章标题"],'
    'input[placeholder*="文章标题"],'
    '[placeholder*="标题"],'
    '[placeholder*="title"],'
    'input[class*="title"]:not([type="hidden"]):not([type="file"]),'
    'textarea[class*="title"],'
    '[class*="title"][contenteditable="true"]'
)

# 正文编辑器候选选择器
CONTENT_SELECTORS = (
    '[placeholder*="正文"],'
    '[placeholder*="内容"],'
    '[placeholder*="请输入正文"],'
    '[placeholder*="请输入内容"],'
    '[placeholder*="content"],'
    '[class*="editor"][contenteditable="true"],'
    '[class*="content"][contenteditable="true"],'
    '[class*="richtext"][contenteditable="true"],'
    '[class*="ProseMirror"],'
    '[role="textbox"]'
)


class ToutiaoPublisher(BasePublisher):
    platform_name = "今日头条"
    edit_url = TOUTIAO_EDIT_URL

    # ============================================================
    # 编辑器操作
    # ============================================================

    def open_editor(self) -> bool:
        print("\n[1/4] 打开头条号编辑页...")
        self.opencli(f"open {self.edit_url}", check=False)
        time.sleep(5)

        # 检查登录状态
        r = self.opencli("state", check=False, noisy=False)
        stdout = (r.stdout or "").lower()
        if any(kw in stdout for kw in ("passport.toutiao.com", "sso.toutiao.com",
                                         "login.toutiao", "mp.toutiao.com/login")):
            print("[Error] 未登录头条号，请先在 Chrome 中登录 https://mp.toutiao.com/")
            return False

        print("  等待编辑器加载...")
        for attempt in range(12):
            time.sleep(2)
            js = (
                "(function(){"
                f"var sel='{TITLE_SELECTORS}';"
                "var titleEl=document.querySelector(sel);"
                f"var contentSel='{CONTENT_SELECTORS}';"
                "var contentEl=document.querySelector(contentSel);"
                # 回退：找 page 上所有 contenteditable
                "if(!contentEl){"
                "var allCE=document.querySelectorAll('[contenteditable=\"true\"]');"
                "for(var i=0;i<allCE.length;i++){"
                "var r=allCE[i].getBoundingClientRect();"
                "if(r.height>100&&r.width>300){contentEl=allCE[i];break;}"
                "}"
                "}"
                "if(!titleEl){"
                "var allInp=document.querySelectorAll('input:not([type=\"hidden\"]):not([type=\"file\"]),textarea');"
                "for(var j=0;j<allInp.length;j++){"
                "var tr=allInp[j].getBoundingClientRect();"
                "if(tr.top<350&&tr.width>200){titleEl=allInp[j];break;}"
                "}"
                "}"
                "return (titleEl?'title:ok':'title:?')+', '+(contentEl?'content:ok':'content:?');"
                "})()"
            )
            r = self.opencli("eval", check=False, noisy=False, cmd_extra=js)
            status = (r.stdout or "").strip()
            if "title:ok" in status and "content:ok" in status:
                print(f"  编辑器就绪 (第{attempt+1}次检查)")
                return True
            if status:
                print(f"  等待中... {status[:80]}")
        print("  [WARN] 编辑器加载超时，尝试继续...")
        return True

    def fill_title(self, title: str):
        print(f"\n[2/4] 填写标题: {title[:40]}...")
        clean = title.strip()
        self._article_title = clean  # 供 _verify_published 使用
        # 头条标题要求 5-30 字符（不足补全，超出截断）
        if len(clean) > 30:
            # 在自然断点处截断：优先句末标点 → 分句标点 → 空格 → 硬截
            breaks = '。！？；，、：」"'
            best = 30
            for br in breaks:
                pos = clean.rfind(br, 20, 30)
                if pos > best - 3:
                    best = pos + 1
                    break
            if best == 30:
                space_pos = clean.rfind(' ', 20, 30)
                if space_pos > 24:
                    best = space_pos
            clean = clean[:best].rstrip('，,；;、：: ')
            print(f"  标题截断至{len(clean)}字: {clean[:50]}")
        elif len(clean) < 5:
            clean = clean + "：深度解析与观察"
            clean = clean[:30]
            print(f"  标题补全至{len(clean)}字: {clean[:50]}")
        escaped = json.dumps(clean, ensure_ascii=False)

        # Step 0: 模拟点击标题输入框（激活 React 组件）
        self.opencli("eval", check=False, cmd_extra=(
            "(function(){"
            f"var el=document.querySelector('textarea[placeholder*=\"文章标题\"],input[placeholder*=\"文章标题\"]');"
            "if(el){el.focus();el.click();return'clicked';}"
            "return'no_title_el';"
            "})()"
        ))
        time.sleep(0.3)

        # Step 1: opencli fill 命令
        r = self.opencli(
            f'fill "{TITLE_SELECTORS}" --nth 0',
            cmd_extra=clean, check=False)
        time.sleep(0.5)

        # Step 2: 验证标题是否完整填入
        verify_js = (
            "(function(){"
            f"var el=document.querySelector('{TITLE_SELECTORS}');"
            "if(!el)return'no_el';"
            "var v=(el.value||el.innerText||el.textContent||'');"
            "return'len:'+v.length;"
            "})()"
        )
        rv = self.opencli("eval", check=False, noisy=False, cmd_extra=verify_js)
        vout = (rv.stdout or "").strip()
        expected_len = len(clean)
        # 用 eval fallback 重试（直接通过 nativeInputSetter 设置 value + dispatch 事件）
        if f"len:{expected_len}" not in vout:
            print(f"  标题未完整填入 ({vout})，使用 eval 重试...")
            js = (
                "(function(){"
                f"var sel='{TITLE_SELECTORS}';"
                "var el=document.querySelector(sel);"
                "if(!el)return'no_title_el';"
                "el.focus();el.click();"
                "if(el.tagName==='INPUT'||el.tagName==='TEXTAREA'){"
                "var nativeInputSetter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                f"nativeInputSetter.call(el,{escaped});"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "el.dispatchEvent(new Event('change',{bubbles:true}));"
                "}else{"
                "el.innerText=" + escaped + ";"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "}"
                "return'filled:'+(el.value||el.innerText||'').substring(0,30);"
                "})()"
            )
            r = self.opencli("eval", check=False, cmd_extra=js)
            print(f"  eval retry: {(r.stdout or '').strip()[:80]}")
        elif r.returncode != 0:
            # Step 3: fill 失败时也用 eval fallback
            js = (
                "(function(){"
                f"var sel='{TITLE_SELECTORS}';"
                "var el=document.querySelector(sel);"
                "if(!el)return'no_title_el';"
                "el.focus();el.click();"
                "if(el.tagName==='INPUT'||el.tagName==='TEXTAREA'){"
                "var nativeInputSetter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;"
                f"nativeInputSetter.call(el,{escaped});"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "el.dispatchEvent(new Event('change',{bubbles:true}));"
                "}else{"
                "el.innerText=" + escaped + ";"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "}"
                "return'filled:'+(el.value||el.innerText||'').substring(0,30);"
                "})()"
            )
            self.opencli("eval", check=False, cmd_extra=js)

        print(f"  标题已输入")

    def _find_content_el_js(self):
        """返回定位正文 contenteditable 元素的 JS 代码片段"""
        return (
            f"var sel='{CONTENT_SELECTORS}';"
            "var el=document.querySelector(sel);"
            "if(!el){"
            "var allCE=document.querySelectorAll('[contenteditable=\"true\"]');"
            "var best=null,bestH=0;"
            "for(var i=0;i<allCE.length;i++){"
            "var r=allCE[i].getBoundingClientRect();"
            "if(r.height>bestH&&r.width>300){best=allCE[i];bestH=r.height;}"
            "}"
            "el=best;"
            "}"
        )

    def fill_content(self, content: str, max_chars: int = 5000, clear_first: bool = True):
        print(f"\n[3/4] 填写正文 ({len(content)}字){' [追加]' if not clear_first else ''}...")
        clean = content.strip()[:max_chars]

        if clear_first:
            # Step 0: 清空编辑器 + 聚焦
            r_clear = self.opencli("eval", check=False, cmd_extra=(
                "(function(){"
                + self._find_content_el_js() +
                "if(!el)return'no_content_el';"
                "el.focus();"
                "var doc=el.ownerDocument||document;"
                "doc.execCommand('selectAll',false,null);"
                "doc.execCommand('delete',false,null);"
                "return'cleared';"
                "})()"
            ))
            if 'no_content_el' in (r_clear.stdout or ''):
                print(f"  [FAIL] 找不到正文编辑器，无法清空")
                return False
            time.sleep(0.3)

        escaped = json.dumps(clean, ensure_ascii=False)

        if clear_first:
            insert_js = (
                "var r=doc.createRange();r.selectNodeContents(el);r.collapse(false);"
                "sl.removeAllRanges();sl.addRange(r);"
                "doc.execCommand('selectAll',false,null);"
                "doc.execCommand('insertText',false," + escaped + ");"
            )
        else:
            # 追加模式：在编辑器末尾加两个换行后插入文本，不清空已有内容
            insert_js = (
                "var nl=doc.createElement('div');nl.innerHTML='<br><br>';el.appendChild(nl);"
                "var r=doc.createRange();r.setStartAfter(el.lastChild||el);r.collapse(true);"
                "sl.removeAllRanges();sl.addRange(r);"
                "doc.execCommand('insertText',false," + escaped + ");"
            )

        js = (
            f"{FIND_EL_JS}"
            "(function(){"
            + self._find_content_el_js() +
            "if(!el)return'no_content_el';"
            "el.focus();"
            "var doc=el.ownerDocument||document;"
            "var sl=window.getSelection();"
            + insert_js +
            "try{el.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,cancelable:true,inputType:'insertText',data:" + escaped + "}));}catch(e){}"
            "try{el.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:true,inputType:'insertText',data:" + escaped + "}));}catch(e){el.dispatchEvent(new Event('input',{bubbles:true}));}"
            "el.dispatchEvent(new Event('change',{bubbles:true}));"
            "var txt=doc.createTextNode('X');"
            "var r2=doc.createRange();r2.setStartAfter(el.lastChild||el);r2.collapse(true);"
            "sl.removeAllRanges();sl.addRange(r2);"
            "doc.execCommand('insertText',false,'X');"
            "doc.execCommand('delete',false,null);"
            "var t=(el.innerText||el.textContent||'');"
            "return'content:'+t.substring(0,40)+' len:'+t.length;"
            "})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=js)
        result = (r.stdout or "").strip()
        print(f"  execCommand: {result[:120]}")
        if 'no_content_el' in result:
            print(f"  [FAIL] 找不到正文编辑器，内容未写入")
            return False
        time.sleep(0.5)

        # Step 3: 等待自动保存（头条 auto-save 通常 3-5 秒完成）
        print(f"  等待自动保存...")
        saved = False
        for wait_i in range(12):
            time.sleep(1)
            check_js = (
                "(function(){"
                "var body=document.body.innerText||'';"
                "var m=body.match(/共\\s*(\\d+)\\s*字/);"
                "if(m&&parseInt(m[1])>10)return'saved:'+m[0];"
                # 兜底：检查编辑器内是否真的有内容
                + self._find_content_el_js() +
                "var t=(el?el.innerText||el.textContent||'':'');"
                "if(t.length>100)return'has_content:'+t.length+'chars';"
                "return'waiting';"
                "})()"
            )
            r_save = self.opencli("eval", check=False, noisy=False, cmd_extra=check_js)
            save_status = (r_save.stdout or "").strip()
            if "saved:" in save_status:
                print(f"  自动保存完成: {save_status}")
                saved = True
                break
            if "has_content:" in save_status:
                print(f"  内容已存在但未显示字数: {save_status}")
                saved = True
                break
            if wait_i % 4 == 0:
                print(f"  ... {save_status[:60]}")
        if not saved:
            print(f"  [WARN] 自动保存未检测到，继续流程（内容可能已存在于编辑器中）")

        print(f"  正文已输入")
        return True

    def insert_images_to_editor(self, image_paths: list):
        """粘贴图片上传 — 压缩 + 分 chunk 传参（每 chunk < 4000 字符，适配 cmd.exe 限制）"""
        import base64 as b64
        from PIL import Image
        import io

        if not image_paths:
            return
        print(f"\n[图片] 插入 {len(image_paths)} 张图片...")

        for idx, img_path in enumerate(image_paths):
            fname = img_path.name
            print(f"  ({idx+1}/{len(image_paths)}) 插入: {fname}")

            # 1. 预处理：缩放 + 压缩
            pil_img = Image.open(img_path)
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            w, h = pil_img.size
            max_dim = 1200
            if w > max_dim or h > max_dim:
                scale = min(max_dim / w, max_dim / h)
                w, h = int(w * scale), int(h * scale)
                pil_img = pil_img.resize((w, h), Image.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=75)
            compressed = buf.getvalue()
            b64_str = b64.b64encode(compressed).decode("ascii")
            data_uri = f"data:image/jpeg;base64,{b64_str}"
            kb = len(compressed) // 1024
            print(f"    压缩: {w}x{h} {kb}KB, base64 {len(b64_str)//1024}KB")

            # 2. 分 chunk 传入浏览器（每次 < 4000 字符，确保总命令 < 8191）
            chunk_size = 4000
            chunks = [data_uri[i:i+chunk_size] for i in range(0, len(data_uri), chunk_size)]
            print(f"    {len(chunks)} 个 chunk...")

            # 初始化
            init_js = f"(function(){{window._imgChunks=[];window._imgName='{fname}';}})()"
            self.opencli("eval", check=False, noisy=False, cmd_extra=init_js)

            # 逐 chunk push
            for ci, chunk in enumerate(chunks):
                escaped_chunk = json.dumps(chunk, ensure_ascii=False)
                push_js = f"(function(){{window._imgChunks.push({escaped_chunk});}})()"
                r_push = self.opencli("eval", check=False, noisy=False, cmd_extra=push_js)
                if r_push.returncode != 0:
                    print(f"    Chunk{ci} 推送失败: {(r_push.stderr or '')[:80]}")
                    break
                if ci % 4 == 0:
                    print(f"    ... chunk {ci+1}/{len(chunks)}")

            # 3. 浏览器中组装 → File → 粘贴事件
            paste_js = (
                f"{FIND_EL_JS}"
                "(async function(){"
                "try{"
                f"var sel='{CONTENT_SELECTORS}';"
                "var body=_f(sel);"
                "if(!body){"
                "var allCE=document.querySelectorAll('[contenteditable=\"true\"]');"
                "var best=null,bestH=0;"
                "for(var i=0;i<allCE.length;i++){"
                "var r=allCE[i].getBoundingClientRect();"
                "if(r.height>bestH&&r.width>300){best=allCE[i];bestH=r.height;}"
                "}"
                "body=best;"
                "}"
                "if(!body)return'no_el';"
                "var dataUri=window._imgChunks.join('');"
                "var arr=dataUri.split(',');var mime=arr[0].match(/:(.*?);/)[1];"
                "var bstr=atob(arr[1]);var n=bstr.length;"
                "var u8arr=new Uint8Array(n);while(n--){u8arr[n]=bstr.charCodeAt(n);}"
                f"var file=new File([u8arr],window._imgName||'{fname}',{{type:mime}});"
                "var dt=new DataTransfer();dt.items.add(file);"
                "body.focus();"
                "var sl=window.getSelection();if(sl){sl.selectAllChildren(body);sl.collapseToEnd();}"
                "var evt;"
                "try{evt=new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:dt});}"
                "catch(e){evt=new Event('paste',{bubbles:true,cancelable:true});evt.clipboardData=dt;}"
                "body.dispatchEvent(evt);"
                "delete window._imgChunks;delete window._imgName;"
                "return'pasted:'+Math.round(file.size/1024)+'kb';"
                "}catch(e){return'err:'+e.message;}"
                "})()"
            )
            r = self.opencli("eval", check=False, cmd_extra=paste_js)
            try:
                print(f"    粘贴: {(r.stdout or '').strip()[:100]}")
            except UnicodeEncodeError:
                pass

            # 4. 等 CDN 上传
            print(f"    等上传...")
            for up_i in range(10):
                time.sleep(1.5)
                check_js = (
                    "(function(){"
                    "var ce=document.querySelector('[contenteditable=\"true\"]');"
                    "if(!ce)return'no_ce';var imgs=ce.querySelectorAll('img');"
                    "var cdn=0;var dataUri=0;"
                    "for(var i=0;i<imgs.length;i++){"
                    "var src=imgs[i].src;"
                    "if(src.indexOf('toutiao.com')!==-1||src.indexOf('pstatp.com')!==-1||src.indexOf('byteimg.com')!==-1)cdn++;"
                    "else if(src.indexOf('data:')===0)dataUri++;"
                    "}"
                    "return'cdn:'+cdn+' dataUri:'+dataUri+' total:'+imgs.length;"
                    "})()"
                )
                r_up = self.opencli("eval", check=False, noisy=False, cmd_extra=check_js)
                up_out = (r_up.stdout or "").strip()
                if "cdn:1" in up_out or "cdn:2" in up_out:
                    print(f"    上传完成: {up_out}")
                    break
                if up_i == 0 or up_i % 3 == 0:
                    print(f"    ... {up_out}")
        print(f"  图片插入完成")

    def set_cover_image(self, cover_path) -> bool:
        """chunk + File injection — 确保封面尺寸 ≥ 672×462"""
        import base64 as b64
        from PIL import Image
        import io

        if not cover_path or not cover_path.exists():
            return False

        print(f"\n[封面] 上传封面图: {cover_path.name}")
        fname = cover_path.name

        # Step 0: 检查是否已有封面
        check_cover_js = (
            "(function(){"
            "var coverImg=document.querySelector('.article-cover-add img,.cover-image img,.article-cover img,.cover-preview img');"
            "if(coverImg&&coverImg.src&&coverImg.src.indexOf('toutiao.com')!==-1)return'has_cover';"
            "var all=document.querySelectorAll('div,span,button');"
            "for(var i=0;i<all.length;i++){"
            "var t=(all[i].innerText||'').trim();"
            "if(t==='编辑替换'&&all[i].offsetParent!==null)return'has_cover';"
            "}"
            "var radios=document.querySelectorAll('.article-cover-radio-group input[type=radio]');"
            "for(var j=0;j<radios.length;j++){"
            "if(radios[j].checked&&radios[j].value!=='0')return'has_cover_radio';"
            "}"
            "return'no_cover';"
            "})()"
        )
        r_check = self.opencli("eval", check=False, noisy=False, cmd_extra=check_cover_js)
        check_result = (r_check.stdout or "").strip()
        if check_result == "has_cover" or check_result == "has_cover_radio":
            print(f"  封面已存在 ({check_result})，跳过上传")
            return True

        # PIL 压缩：max 1200px，min 672×462（头条推荐尺寸）
        MIN_COVER_W, MIN_COVER_H = 672, 462
        pil_img = Image.open(cover_path)
        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
        w, h = pil_img.size
        max_dim = 1200
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            w, h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
        if w < MIN_COVER_W or h < MIN_COVER_H:
            scale = max(MIN_COVER_W / w, MIN_COVER_H / h)
            w, h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
            print(f"  封面放大至: {w}x{h}（满足最小 {MIN_COVER_W}x{MIN_COVER_H}）")
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=80)
        compressed = buf.getvalue()
        b64_str = b64.b64encode(compressed).decode("ascii")
        data_uri = f"data:image/jpeg;base64,{b64_str}"
        kb = len(compressed) // 1024
        print(f"  压缩: {w}x{h} {kb}KB → base64 {len(b64_str)//1024}KB")

        # Chunk push
        chunk_size = 4000
        chunks = [data_uri[i:i+chunk_size] for i in range(0, len(data_uri), chunk_size)]
        print(f"  {len(chunks)} 个 chunk...")
        init_js = f"(function(){{window._coverChunks=[];window._coverName='{fname}';}})()"
        self.opencli("eval", check=False, noisy=False, cmd_extra=init_js)
        for ci, chunk in enumerate(chunks):
            escaped_chunk = json.dumps(chunk, ensure_ascii=False)
            push_js = f"(function(){{window._coverChunks.push({escaped_chunk});}})()"
            self.opencli("eval", check=False, noisy=False, cmd_extra=push_js)
            if ci % 5 == 0:
                print(f"    chunk {ci+1}/{len(chunks)}")

        # Step 1: 触发封面上传弹窗
        step1_js = (
            f"{REACT_CLICK_JS}"
            "(function(){try{"
            "var ca=document.querySelector('.article-cover-add');"
            "if(ca&&ca.offsetParent!==null){ca.click();return'clicked:add';}"
            "var all=document.querySelectorAll('div,span,button,label');"
            "for(var i=0;i<all.length;i++){"
            "var el=all[i];"
            "if(el.offsetParent===null)continue;"
            "var t=(el.innerText||el.textContent||'').trim();"
            "if(t==='编辑替换'||t.indexOf('编辑替换')!==-1){return _rc(el);}"
            "if(t.indexOf('上传封面')!==-1||t.indexOf('添加封面')!==-1){el.click();return'clicked_kw:'+t;}"
            "}"
            "var radios=document.querySelectorAll('.article-cover-radio-group input[type=radio]');"
            "for(var j=0;j<radios.length;j++){"
            "if(radios[j].value==='2'&&!radios[j].checked){radios[j].click();return'clicked:radio2';}"
            "}"
            "return'no_trigger ca:'+(ca?'exists':'null');"
            "}catch(e){return'err:'+e.message;}})()"
        )
        r1 = self.opencli("eval", check=False, cmd_extra=step1_js)
        print(f"  Step1: {(r1.stdout or '').strip()[:120]}")
        time.sleep(2.5)

        # Step 1.5: 等弹窗 → 注入 chunk 组装的 File → fiber onFileChange
        step15_js = (
            f"{REACT_CLICK_JS}"
            f"(async function(){{"
            f"var R=[];function L(s){{R.push(s);}}"
            f"try{{"
            # Wait for panel (多选择器，防 class 名变化)
            f"var PANEL_SELS=['.upload-image-panel','.cover-upload-panel','.image-upload-modal',"
            f"'[class*=upload-image]','[class*=cover-upload]','[class*=image-upload]',"
            f"'.upload-handler','.btn-upload-handle'];"
            f"var panel=null;"
            f"for(var w=0;w<20;w++){{"
            f"for(var si=0;si<PANEL_SELS.length;si++){{"
            f"try{{var p=document.querySelector(PANEL_SELS[si]);if(p&&p.offsetParent!==null){{panel=p;break;}}}}catch(e){{}}"
            f"}}"
            f"if(panel)break;"
            f"await new Promise(function(rr){{setTimeout(rr,500);}});"
            f"}}"
            f"if(!panel||panel.offsetParent===null){{"
            # 面板未出现，重试触发（可能 Step1 的点击没生效）
            f"  L('retry_trigger');"
            f"  var ca=document.querySelector('.article-cover-add');"
            f"  if(ca&&ca.offsetParent!==null){{ca.click();}}"
            f"  var all=document.querySelectorAll('div,span,button');"
            f"  for(var j=0;j<all.length;j++){{"
            f"    var t2=(all[j].innerText||'').trim();"
            f"    if((t2.indexOf('上传封面')!==-1||t2.indexOf('编辑替换')!==-1)&&all[j].offsetParent!==null){{all[j].click();break;}}"
            f"  }}"
            f"  await new Promise(function(rr){{setTimeout(rr,2000);}});"
            f"  for(var w2=0;w2<10;w2++){{"
            f"    for(var si2=0;si2<PANEL_SELS.length;si2++){{"
            f"      try{{var p2=document.querySelector(PANEL_SELS[si2]);if(p2&&p2.offsetParent!==null){{panel=p2;break;}}}}catch(e){{}}"
            f"    }}"
            f"    if(panel)break;"
            f"    await new Promise(function(rr){{setTimeout(rr,500);}});"
            f"  }}"
            f"}}"
            f"if(!panel||panel.offsetParent===null)return'ERR:no_panel waited_10s+retry|'+R.join('|')+'|DOM:'+(document.body.innerText||'').substring(0,100);"
            f"L('1.panel_open');"
            # Assemble data URI → blob → File
            f"var dataUri=window._coverChunks.join('');delete window._coverChunks;"
            f"var arr=dataUri.split(',');var mime=arr[0].match(/:(.*?);/)[1];"
            f"var bstr=atob(arr[1]);var n=bstr.length;"
            f"var u8arr=new Uint8Array(n);while(n--){{u8arr[n]=bstr.charCodeAt(n);}}"
            f"var imgFile=new File([u8arr],window._coverName||'{fname}',{{type:mime}});"
            f"delete window._coverName;"
            f"var dt=new DataTransfer();dt.items.add(imgFile);"
            f"L('2.assembled');"
            # Find file input in panel
            f"var inp=panel.querySelector('input[type=file]');"
            f"if(!inp)inp=document.querySelector('.upload-handler input[type=file],.btn-upload-handle input[type=file]');"
            f"if(!inp)inp=document.querySelector('.upload-image-panel input[type=file]');"
            f"if(!inp)return'ERR:no_inp_in_panel|'+R.join('|');"
            f"L('3.inp_ok');"
            # Fiber → onFileChange
            f"var fk=Object.keys(inp).find(function(k){{return /__react/.test(k)&&typeof inp[k]==='object';}});"
            f"if(!fk)return'ERR:no_fiber|'+R.join('|');"
            f"var fiber=inp[fk];var node=fiber;var depth=0;var handler=null;"
            f"while(node&&depth<15){{"
            f"try{{"
            f"var mp=node.memoizedProps;"
            f"if(mp){{"
            f"var ks=Object.keys(mp);"
            f"for(var j=0;j<ks.length;j++){{"
            f"var kk=ks[j];"
            f"if(typeof mp[kk]==='function'&&/onFileChange|onChange|handleFile/i.test(kk)){{"
            f"handler={{fn:mp[kk],name:kk,d:depth}};break;"
            f"}}"
            f"}}"
            f"}}"
            f"}}catch(x){{}}"
            f"if(handler)break;"
            f"node=node.return;depth++;"
            f"}}"
            f"if(!handler)return'ERR:no_handler|'+R.join('|');"
            f"L('4.handler:'+handler.name+'@'+handler.d);"
            f"inp.files=dt.files;"
            f"try{{handler.fn([imgFile]);L('5.ok');}}catch(e1){{L('5.err:'+e1.message);}}"
            f"await new Promise(function(rr){{setTimeout(rr,800);}});"
            f"return R.join('|');"
            f"}}catch(e){{return'ERR:'+e.message+'|'+R.join('|');}}"
            f"}})()"
        )
        r15 = self.opencli("eval", check=False, cmd_extra=step15_js)
        print(f"  Step1.5: {(r15.stdout or '').strip()[:300]}")
        time.sleep(2)

        # Step 2: 弹窗内确认
        step2_js = (
            f"{REACT_CLICK_JS}"
            "(function(){"
            "var panel=document.querySelector('.upload-image-panel');"
            "var scope=panel||document;"
            "var all=scope.querySelectorAll('button');"
            "for(var i=0;i<all.length;i++){"
            "var b=all[i];"
            "if(b.offsetParent===null)continue;"
            "var t=(b.innerText||'').trim();"
            "if(t==='确认'||t==='确定'||t==='完成'||t==='保存'){return _rc(b);}"
            "}"
            "return'no_confirm_needed';"
            "})()"
        )
        r2 = self.opencli("eval", check=False, cmd_extra=step2_js)
        try:
            print(f"  Step2: {(r2.stdout or '').strip()[:80]}")
        except UnicodeEncodeError:
            pass
        time.sleep(1.5)
        return True

    def _check_content_declaration(self):
        """勾选内容声明复选框（AI生成、个人观点等），草稿和发布模式都执行"""
        print(f"  勾选内容声明...")
        declare_js = (
            "(function(){"
            "var keywords=['引用AI','AI生成','人工智能','个人观点','仅供参考','取材网络','内容声明'];"
            "var all=document.querySelectorAll('label');"
            "var results=[];"
            "for(var d=0;d<keywords.length;d++){"
            "for(var i=0;i<all.length;i++){"
            "var t=(all[i].innerText||'').trim();"
            "if(t.indexOf(keywords[d])!==-1){"
            "var cb=all[i].querySelector('input[type=checkbox]');"
            "if(cb&&!cb.checked){all[i].click();results.push('checked:'+t);}"
            "else if(cb&&cb.checked){results.push('already:'+t);}"
            "}"
            "}"
            "}"
            "return results.length>0?results.join('|'):'no_decl_label';"
            "})()"
        )
        r = self.opencli("eval", check=False, noisy=False, cmd_extra=declare_js)
        out = (r.stdout or "").strip()
        if out and out != 'no_decl_label':
            print(f"  声明: {out[:200]}")
        elif out == 'no_decl_label':
            print(f"  声明: 未找到复选框（页面结构可能已变化）")
        time.sleep(0.5)

    @staticmethod
    def _set_dpi_aware():
        """确保进程 DPI 感知，否则 SetCursorPos 坐标与 Chrome 物理像素不匹配"""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _real_click(self, button_text: str, retries: int = 3) -> str:
        """获取按钮屏幕坐标 → Windows API 真实鼠标点击 → isTrusted:true
        返回: 'clicked' / 'not_found' / 'pos_error'"""
        self._set_dpi_aware()
        text_escaped = json.dumps(button_text, ensure_ascii=False)

        for attempt in range(retries):
            if attempt > 0:
                print(f"    真实点击重试 {attempt+1}/{retries}...")
                time.sleep(1)

            # 1. 获取按钮在屏幕上的中心坐标
            pos_js = (
                "(function(){"
                "var all=document.querySelectorAll('button');"
                "for(var i=0;i<all.length;i++){"
                "var b=all[i];"
                "if(!b.offsetParent||b.disabled)continue;"
                "var t=(b.innerText||'').trim();"
                f"if(t.indexOf({text_escaped})!==-1){{"
                "var r=b.getBoundingClientRect();"
                "var dpr=window.devicePixelRatio||1;"
                "var chromeH=(window.outerHeight-window.innerHeight)*dpr;"
                "return JSON.stringify({"
                "sx:Math.round(window.screenX+r.x*dpr+r.width*dpr/2),"
                "sy:Math.round(window.screenY+chromeH+r.y*dpr+r.height*dpr/2)"
                "});"
                "}"
                "}"
                "return'not_found';"
                "})()"
            )
            r = self.opencli("eval", check=False, noisy=False, cmd_extra=pos_js)
            out = (r.stdout or "").strip()
            if out == 'not_found':
                return 'not_found'

            try:
                pos = json.loads(out)
            except json.JSONDecodeError:
                print(f"    坐标解析失败: {out[:80]}")
                continue

            sx, sy = pos['sx'], pos['sy']
            print(f"    真实点击屏幕 ({sx}, {sy})...")

            # 2. Windows API: SendInput（替代弃用的 mouse_event）
            user32 = ctypes.windll.user32

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            old = POINT()
            user32.GetCursorPos(ctypes.byref(old))

            # SendInput 结构（绝对坐标映射至 0-65535 虚拟屏幕）
            SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79
            sw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            sh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            nx = int(sx * 65535 / sw) if sw > 0 else sx
            ny = int(sy * 65535 / sh) if sh > 0 else sy

            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                            ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                            ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
            class INPUT(ctypes.Structure):
                _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

            # 移动鼠标到目标位置（绝对坐标）
            move = INPUT(0, MOUSEINPUT(nx, ny, 0, 0x8000 | 0x0001, 0, None))  # ABSOLUTE | MOVE
            user32.SendInput(1, ctypes.byref(move), ctypes.sizeof(INPUT))
            time.sleep(0.05)

            # 按下 + 释放
            down = INPUT(0, MOUSEINPUT(0, 0, 0, 0x0002, 0, None))  # LEFTDOWN
            up = INPUT(0, MOUSEINPUT(0, 0, 0, 0x0004, 0, None))    # LEFTUP
            user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
            time.sleep(0.03)
            user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))

            # 恢复光标
            time.sleep(0.02)
            user32.SetCursorPos(old.x, old.y)

            return 'clicked'

        return 'pos_error'

    def click_publish(self, mode: str = "draft"):
        print(f"\n[4/4] 发布操作 (模式: {mode})...")

        # 内容声明复选框 — 无论草稿还是发布都勾选
        self._check_content_declaration()

        if mode == "draft":
            # 等待自动保存完成，并尝试点击「保存草稿」按钮
            print(f"  等待自动保存草稿...")
            saved = False
            for wait_i in range(10):
                time.sleep(1.5)
                check_js = (
                    "(function(){"
                    "var body=document.body.innerText||'';"
                    "var m=body.match(/共\\s*(\\d+)\\s*字/);"
                    "if(m&&parseInt(m[1])>10)return'saved:'+m[0];"
                    + self._find_content_el_js() +
                    "var t=(el?el.innerText||el.textContent||'':'');"
                    "if(t.length>100)return'has_content:'+t.length+'chars';"
                    "return'waiting';"
                    "})()"
                )
                r_save = self.opencli("eval", check=False, noisy=False, cmd_extra=check_js)
                save_status = (r_save.stdout or "").strip()
                if "saved:" in save_status or "has_content:" in save_status:
                    print(f"  草稿已保存: {save_status}")
                    saved = True
                    break
                if wait_i % 3 == 0:
                    print(f"  ... {save_status[:60]}")

            # 尝试找「保存草稿」/「存草稿」按钮
            draft_btn_js = (
                "(function(){"
                "var all=document.querySelectorAll('button');"
                "for(var i=0;i<all.length;i++){"
                "var b=all[i];"
                "if(b.offsetParent===null||b.disabled)continue;"
                "var t=(b.innerText||'').trim();"
                "if(t.indexOf('保存草稿')!==-1||t.indexOf('存草稿')!==-1||t.indexOf('暂存')!==-1){"
                "b.focus();"
                "b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,view:window}));"
                "b.click();"
                "return'clicked:'+t;"
                "}"
                "}"
                "return'no_draft_btn';"
                "})()"
            )
            r_draft = self.opencli("eval", check=False, noisy=False, cmd_extra=draft_btn_js)
            draft_out = (r_draft.stdout or "").strip()
            if "clicked" in draft_out:
                print(f"  已点击: {draft_out[:80]}")
                time.sleep(2)
                saved = True

            if saved:
                return True
            print(f"  [WARN] 草稿保存未确认，内容可能未存入编辑器")
            return False

        # Step 0.1: 等待自动保存完成
        print(f"  等待自动保存...")
        for check_i in range(8):
            check_js = (
                "(function(){"
                "var body=document.body.innerText||'';"
                "var m=body.match(/共\\s*(\\d+)\\s*字/);"
                "if(m&&parseInt(m[1])>10)return'ok:'+m[0];"
                "return'waiting';"
                "})()"
            )
            r_ck = self.opencli("eval", check=False, noisy=False, cmd_extra=check_js)
            ck = (r_ck.stdout or "").strip()
            if "ok:" in ck:
                print(f"  自动保存就绪: {ck}")
                break
            if check_i % 2 == 0:
                print(f"  ... {ck}")
            time.sleep(1.5)

        # Step 0.2: 诊断当前按钮状态
        diag_js = (
            "Array.from(document.querySelectorAll('button')).filter(function(b){"
            "return b.offsetParent!==null;}).map(function(b){"
            "var t=(b.innerText||'').trim().substring(0,40);"
            "var cs=b.className.toString().substring(0,30);"
            "return t+(b.disabled?'[DISABLED]':'')+':'+cs;}).join('|')"
        )
        r_diag = self.opencli("eval", check=False, noisy=False, cmd_extra=diag_js)
        print(f"  当前可见按钮: {(r_diag.stdout or '').strip()[:250]}")
        time.sleep(0.5)

        # 通用按钮查找+点击（通过 _rc 走 React fiber 事件系统）
        find_and_click = (
            f"{REACT_CLICK_JS}"
            "(function(patterns){"
            "var all=document.querySelectorAll('button');"
            "for(var i=0;i<all.length;i++){"
            "var b=all[i];"
            "if(b.offsetParent===null)continue;"
            "if(b.disabled)continue;"
            "var t=(b.innerText||'').trim();"
            "for(var j=0;j<patterns.length;j++){"
            "if(t.indexOf(patterns[j])!==-1){"
            "b.focus();"
            "var rcResult=_rc(b);"
            "return'clicked:'+t+' via:'+rcResult;"
            "}"
            "}"
            "}"
            "return'not_found';"
            "})"
        )

        # Step 1: 点击「预览并发布」/「预览与发布」
        step1_js = find_and_click + "(['预览与发布','预览并发布'])"
        r1 = self.opencli("eval", check=False, cmd_extra=step1_js)
        out1 = (r1.stdout or "").strip()
        print(f"  Step1 点击预览发布: {out1[:120]}")
        time.sleep(5)

        if "not_found" in out1:
            print(f"  [WARN] 未找到预览发布按钮")
            return False

        # Step 1.5: 如果有「预览并定时发布」，先点它
        step1_5_js = (
            f"{REACT_CLICK_JS}"
            "(function(){"
            "var all=document.querySelectorAll('button');"
            "for(var i=0;i<all.length;i++){"
            "var b=all[i];"
            "if(b.offsetParent===null||b.disabled)continue;"
            "var t=(b.innerText||'').trim();"
            "if(t.indexOf('预览并定时发布')!==-1||t.indexOf('预览与定时发布')!==-1){"
            "b.focus();"
            "var rcResult=_rc(b);"
            "return'clicked:'+t+' via:'+rcResult;"
            "}"
            "}"
            "return'no_step1_5';"
            "})()"
        )
        time.sleep(2)
        r1_5 = self.opencli("eval", check=False, noisy=False, cmd_extra=step1_5_js)
        out1_5 = (r1_5.stdout or "").strip()
        if "clicked" in out1_5:
            print(f"  Step1.5 点击预览并定时发布: {out1_5[:80]}")
            time.sleep(2)

        # Step 2: 等待「确认发布」按钮出现 → 点击
        print(f"  等待「确认发布」按钮出现...")
        confirm_found = False
        for retry in range(8):
            time.sleep(1.5)
            check_btn_js = (
                "(function(){"
                "var all=document.querySelectorAll('button');"
                "for(var i=0;i<all.length;i++){"
                "var b=all[i];"
                "if(b.offsetParent===null||b.disabled)continue;"
                "var t=(b.innerText||'').trim();"
                "if(t.indexOf('确认发布')!==-1||t==='确认发布'){"
                "return'found_confirm';"
                "}"
                "}"
                "return'btns:'+Array.from(document.querySelectorAll('button')).filter(function(b){"
                "return b.offsetParent!==null;}).map(function(b){return (b.innerText||'').trim().substring(0,30);}).join('|');"
                "})()"
            )
            r_cb = self.opencli("eval", check=False, noisy=False, cmd_extra=check_btn_js)
            cb_out = (r_cb.stdout or "").strip()
            if "found_confirm" in cb_out:
                print(f"  确认发布按钮已出现 (第{retry+1}次检查)")
                confirm_found = True
                break
            if retry % 2 == 0:
                print(f"  ... {cb_out[:120]}")

        if confirm_found:
            step2_js = find_and_click + "(['确认发布'])"
            r2 = self.opencli("eval", check=False, cmd_extra=step2_js)
            out2 = (r2.stdout or "").strip()
            print(f"  Step2 点击确认发布: {out2[:120]}")
            time.sleep(4)
        else:
            print(f"  [WARN] 未检测到确认发布按钮，尝试直接查找...")
            step2_js = find_and_click + "(['确认发布'])"
            r2 = self.opencli("eval", check=False, cmd_extra=step2_js)
            out2 = (r2.stdout or "").strip()
            print(f"  Step2 直接点击: {out2[:120]}")
            time.sleep(4)

        # Step 3: 检查是否有确认弹窗
        confirm_js = (
            f"{REACT_CLICK_JS}"
            "(function(){"
            "var modals=document.querySelectorAll('[role=dialog],.byte-modal-wrapper');"
            "for(var i=0;i<modals.length;i++){"
            "var m=modals[i];"
            "if(m.offsetParent===null)continue;"
            "var btns=m.querySelectorAll('button');"
            "for(var j=0;j<btns.length;j++){"
            "var bt=(btns[j].innerText||'').trim();"
            "if(bt==='确定'||bt==='确认'||bt==='发布'||bt==='确认发布'){"
            "btns[j].focus();"
            "var rcResult=_rc(btns[j]);"
            "return'confirmed:'+bt+' via:'+rcResult;"
            "}"
            "}"
            "var primaryBtns=m.querySelectorAll('.primary,.confirm,.btn-primary');"
            "for(var k=0;k<primaryBtns.length;k++){"
            "if(primaryBtns[k].offsetParent!==null){"
            "_rc(primaryBtns[k]);return'primary_btn';"
            "}"
            "}"
            "}"
            "return'no_visible_modal';"
            "})()"
        )
        r3 = self.opencli("eval", check=False, cmd_extra=confirm_js)
        out3 = (r3.stdout or "").strip()
        print(f"  Step3 确认弹窗: {out3[:120]}")
        time.sleep(3)

        # Step 4: 验证发布结果 — 优先看编辑器是否清空，否则去后台列表确认
        time.sleep(2)
        check_cleared_js = (
            "(function(){"
            + self._find_content_el_js() +
            "if(!el)return'no_el';"
            "var t=(el.innerText||el.textContent||'');"
            "var words=document.body.innerText.match(/共\\s*(\\d+)\\s*字/);"
            "return'content:'+t.length+' words:'+(words?words[1]:'?');"
            "})()"
        )
        r_cleared = self.opencli("eval", check=False, noisy=False, cmd_extra=check_cleared_js)
        cleared_out = (r_cleared.stdout or "").strip()
        print(f"  发布后编辑器: {cleared_out[:80]}")

        cm = re.search(r'content:(\d+)', cleared_out)
        post_content_len = int(cm.group(1)) if cm else -1
        wm = re.search(r'words:(\d+)', cleared_out)
        post_words = int(wm.group(1)) if wm else -1

        if post_content_len < 20 and post_words < 20:
            print(f"  发布成功！编辑器已清空")
            return True

        # 编辑器未清空，去后台列表做最终验证
        return self._verify_published()

    def _verify_published(self) -> bool:
        """去后台文章列表搜标题验证是否真的发布了"""
        title = getattr(self, '_article_title', '')
        if not title:
            print(f"  [验证] 无标题，无法验证")
            return False

        check_key = title[:15]
        print(f"  [验证] 去后台列表搜索「{check_key}」...")

        self.opencli('open "https://mp.toutiao.com/profile_v4/manage/content/all"', check=False, timeout=30)
        time.sleep(4)

        r = self.opencli("eval", check=False, noisy=False,
                         cmd_extra="(function(){return document.body.innerText;})()", timeout=15)
        if r.returncode != 0 or not r.stdout:
            print(f"  [验证] 无法读取后台页面")
            return False

        if check_key in r.stdout:
            print(f"  [验证] 后台确认：文章已发布 ✓")
            return True

        print(f"  [验证] 后台未找到文章，发布可能失败")
        return False

    def _verify_content(self, article: dict):
        print("\n[验证] 回读标题与正文...")
        js = (
            "(function(){"
            # 读标题
            f"var titleSel='{TITLE_SELECTORS}';"
            "var titleEl=document.querySelector(titleSel);"
            "var tv=titleEl?(titleEl.value||titleEl.innerText||titleEl.textContent||'').substring(0,40):'no_title_el';"
            # 读正文
            f"var contentSel='{CONTENT_SELECTORS}';"
            "var contentEl=document.querySelector(contentSel);"
            "if(!contentEl){"
            "var allCE=document.querySelectorAll('[contenteditable=\"true\"]');"
            "for(var i=0;i<allCE.length;i++){"
            "var r=allCE[i].getBoundingClientRect();"
            "if(r.height>100&&r.width>300){contentEl=allCE[i];break;}"
            "}"
            "}"
            "var cv=contentEl?(contentEl.innerText||contentEl.textContent||'').substring(0,40):'no_content_el';"
            "return'title:'+tv+'; content:'+cv;"
            "})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=js)
        try:
            print(f"  页面实际值: {(r.stdout or '').strip()[:300]}")
        except UnicodeEncodeError:
            pass
