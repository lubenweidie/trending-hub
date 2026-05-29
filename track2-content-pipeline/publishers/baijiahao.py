"""百家号发布器"""
import json
import re
import time
from pathlib import Path
from .base import BasePublisher
from .browser_utils import FIND_EL_JS, REACT_CLICK_JS

BJH_EDIT_URL = "https://baijiahao.baidu.com/builder/rc/edit?type=news"
CONTENT_SEL = 'body.view.news-editor-pc[contenteditable="true"]'

# 百家号 Lexical 编辑器标题定位
FIND_TITLE_JS = (
    "var _ft=function(){"
    "var span=document.querySelector('[data-lexical-text=\"true\"]');"
    "if(!span)return document.querySelector('[contenteditable=\"true\"]');"
    "var el=span;"
    "while(el&&el!==document.body){"
    "if(el.getAttribute('contenteditable')==='true')return el;"
    "el=el.parentElement;"
    "}"
    "return document.querySelector('[contenteditable=\"true\"]');"
    "};"
)


class BaijiahaoPublisher(BasePublisher):
    platform_name = "百家号"
    edit_url = BJH_EDIT_URL

    # ============================================================
    # 编辑器操作
    # ============================================================

    def open_editor(self) -> bool:
        print("\n[1/4] 打开编辑页...")
        self.opencli(f"open {self.edit_url}", check=False)
        time.sleep(4)

        r = self.opencli("state", check=False, noisy=False)
        stdout = (r.stdout or "").lower()
        if "passport.baidu.com" in stdout or "login.baidu.com" in stdout:
            print("[Error] 未登录百家号，请先在 Chrome 中登录 https://baijiahao.baidu.com/")
            return False

        print("  初始化编辑器...")
        self.opencli("eval", check=False,
                     cmd_extra=(
                         '(()=>{var els=document.querySelectorAll("*");'
                         'for(var i=0;i<els.length;i++){var e=els[i];'
                         'if(e.innerText==="图文"&&e.children.length===0){e.click();return"clicked"}}'
                         'return"not found"})()'
                     ))
        print("  等待编辑器加载...")
        for attempt in range(10):
            time.sleep(2)
            r = self.opencli("eval", check=False, noisy=False,
                             cmd_extra=(
                                 f"(()=>{{{FIND_EL_JS}{FIND_TITLE_JS}"
                                 f"var titleEl=_ft();"
                                 f"var contentEl=_f('{CONTENT_SEL}');"
                                 "return (titleEl?'title:ok':'title:missing')+', '+(contentEl?'content:ok':'content:missing');"
                                 "})()"
                             ))
            status = (r.stdout or "").strip()
            if "title:ok" in status and "content:ok" in status:
                print(f"  编辑器就绪 (第{attempt+1}次检查)")
                return True
            if status:
                print(f"  等待中... {status[:60]}")
        print("  [WARN] 编辑器加载超时，仍尝试继续...")
        return True

    def fill_title(self, title: str):
        print(f"\n[2/4] 填写标题: {title[:40]}...")
        self.opencli('fill "[contenteditable=true]" --nth 0', cmd_extra=title, check=False)
        self._article_title = title.strip()  # 供 _verify_published 使用
        time.sleep(0.5)
        print(f"  标题已输入")

    def fill_content(self, content: str, clear_first: bool = True):
        print(f"\n[3/4] 填写正文 ({len(content)}字){' [追加]' if not clear_first else ''}...")
        clean = content.strip()[:5000]
        escaped = json.dumps(clean, ensure_ascii=False)

        if clear_first:
            insert_logic = (
                f"doc.execCommand('selectAll',false,null);"
                f"doc.execCommand('insertText',false,{escaped});"
            )
        else:
            # 追加模式：insertAdjacentHTML（不破坏已有DOM，execCommand在图片粘贴后不可靠）
            insert_logic = (
                f"var preLen=(el.innerText||el.textContent||'').length;"
                f"el.insertAdjacentHTML('beforeend','<br><br>');"
                f"var html='<p>'+{escaped}.replace(/\\\\n\\\\n/g,'</p><p>').replace(/\\\\n/g,'<br>')+'</p>';"
                f"el.insertAdjacentHTML('beforeend',html);"
                f"var postLen=(el.innerText||el.textContent||'').length;"
                f"var added=postLen-preLen;"
            )

        js = (
            f"{FIND_EL_JS}"
            f"(()=>{{"
            f"var el=_f('{CONTENT_SEL}');"
            f"if(!el)return'noel';"
            f"el.focus();"
            f"var doc=el.ownerDocument||document;"
            + insert_logic +
            f"el.dispatchEvent(new Event('input',{{bubbles:true}}));"
            f"el.dispatchEvent(new Event('change',{{bubbles:true}}));"
            f"var txt=(el.innerText||el.textContent||'').substring(0,40);"
            + (f"return'content:'+txt+' postLen:'+postLen+' added:'+added;" if not clear_first else
               f"return'content:'+txt+' len:'+(el.innerText||el.textContent||'').length;") +
            f"}})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=js)
        result = (r.stdout or "").strip()
        print(f"  正文结果: {result[:120]}")

        # 判断是否需要 fallback
        need_fallback = False
        if 'noel' in result:
            need_fallback = True
        elif clear_first:
            m = re.search(r'len:(\d+)', result)
            content_len = int(m.group(1)) if m else -1
            if content_len <= 1:
                need_fallback = True
        else:
            # 追加模式：检测 execCommand 是否真的插入了内容
            added_m = re.search(r'added:(\-?\d+)', result)
            added = int(added_m.group(1)) if added_m else 0
            if added < max(len(clean) * 0.3, 10):  # 插入不到预期的30%
                print(f"  追加未生效 (added={added}/{len(clean)})，尝试 fallback...")
                need_fallback = True

        if need_fallback:
            if clear_first:
                fallback_js = (
                    f"{FIND_EL_JS}"
                    f"(()=>{{"
                    f"var el=_f('{CONTENT_SEL}');"
                    f"if(!el)return'noel_fb';"
                    f"el.focus();"
                    f"el.innerHTML='<p>'+{escaped}.replace(/\\\\n\\\\n/g,'</p><p>').replace(/\\\\n/g,'<br>')+'</p>';"
                    f"el.dispatchEvent(new Event('input',{{bubbles:true}}));"
                    f"el.dispatchEvent(new Event('change',{{bubbles:true}}));"
                    f"var t2=(el.innerText||el.textContent||'').substring(0,40);"
                    f"return'fb_content:'+t2+' len:'+(el.innerText||el.textContent||'').length;"
                    f"}})()"
                )
            else:
                # 追加模式 fallback：在现有 innerHTML 末尾追加，不清空已有内容
                fallback_js = (
                    f"{FIND_EL_JS}"
                    f"(()=>{{"
                    f"var el=_f('{CONTENT_SEL}');"
                    f"if(!el)return'noel_fb';"
                    f"el.focus();"
                    f"var preHtml=el.innerHTML;"
                    f"el.innerHTML=preHtml+'<p>'+{escaped}.replace(/\\\\n\\\\n/g,'</p><p>').replace(/\\\\n/g,'<br>')+'</p>';"
                    f"el.dispatchEvent(new Event('input',{{bubbles:true}}));"
                    f"el.dispatchEvent(new Event('change',{{bubbles:true}}));"
                    f"var t2=(el.innerText||el.textContent||'').substring(0,40);"
                    f"return'fb_append:'+t2+' len:'+(el.innerText||el.textContent||'').length;"
                    f"}})()"
                )
            r2 = self.opencli("eval", check=False, cmd_extra=fallback_js)
            fb_result = (r2.stdout or "").strip()
            print(f"  fallback结果: {fb_result[:120]}")
            if 'noel_fb' in fb_result:
                print(f"  [FAIL] 找不到正文编辑器，内容未写入")
                return False
        time.sleep(0.5)
        print(f"  正文已输入")
        return True

    def insert_images_to_editor(self, image_paths: list):
        """chunk + ClipboardEvent paste — 绕过 HTTP 服务器，适配 HTTPS 页面"""
        import base64 as b64
        from PIL import Image
        import io

        if not image_paths:
            return
        print(f"\n[图片] 插入 {len(image_paths)} 张图片...")

        for idx, img_path in enumerate(image_paths):
            fname = img_path.name
            print(f"  ({idx+1}/{len(image_paths)}) 插入: {fname}")

            # 1. PIL 压缩 + 转 base64 data URI
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

            # 2. 分 chunk 传入浏览器
            chunk_size = 4000
            chunks = [data_uri[i:i+chunk_size] for i in range(0, len(data_uri), chunk_size)]
            print(f"    {len(chunks)} 个 chunk...")

            init_js = f"(function(){{window._imgChunks=[];window._imgName='{fname}';}})()"
            self.opencli("eval", check=False, noisy=False, cmd_extra=init_js)

            for ci, chunk in enumerate(chunks):
                escaped_chunk = json.dumps(chunk, ensure_ascii=False)
                push_js = f"(function(){{window._imgChunks.push({escaped_chunk});}})()"
                r_push = self.opencli("eval", check=False, noisy=False, cmd_extra=push_js)
                if r_push.returncode != 0:
                    print(f"    Chunk{ci} 推送失败: {(r_push.stderr or '')[:80]}")
                    break
                if ci % 4 == 0:
                    print(f"    ... chunk {ci+1}/{len(chunks)}")

            # 3. JS 组装 → File → ClipboardEvent paste 到编辑器
            paste_js = (
                f"{FIND_EL_JS}"
                "(async function(){"
                "try{"
                f"var el=_f('{CONTENT_SEL}');"
                "if(!el)return'no_el';"
                "var dataUri=window._imgChunks.join('');"
                "var arr=dataUri.split(',');var mime=arr[0].match(/:(.*?);/)[1];"
                "var bstr=atob(arr[1]);var n=bstr.length;"
                "var u8arr=new Uint8Array(n);while(n--){u8arr[n]=bstr.charCodeAt(n);}"
                f"var file=new File([u8arr],window._imgName||'{fname}',{{type:mime}});"
                "var dt=new DataTransfer();dt.items.add(file);"
                "el.focus();"
                "try{var sl=window.getSelection();if(sl&&sl.rangeCount>0){sl.selectAllChildren(el);sl.collapseToEnd();}}catch(e){}"
                "var evt;"
                "try{evt=new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:dt});}"
                "catch(e){evt=new Event('paste',{bubbles:true,cancelable:true});evt.clipboardData=dt;}"
                "el.dispatchEvent(evt);"
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

            # 4. 等 CDN 上传（检查 bjh-image-container）
            print(f"    等上传...")
            for up_i in range(10):
                time.sleep(1.5)
                check_js = (
                    f"{FIND_EL_JS}"
                    "(function(){"
                    f"var el=_f('{CONTENT_SEL}');"
                    "if(!el)return'no_el';"
                    "var imgs=el.querySelectorAll('.bjh-image-container');"
                    "var cdnCount=0;"
                    "for(var i=0;i<imgs.length;i++){"
                    "var img=imgs[i].querySelector('img');"
                    "if(img&&img.src&&img.src.indexOf('data:')!==0)cdnCount++;"
                    "}"
                    "return'cdn:'+cdnCount+' total:'+imgs.length;"
                    "})()"
                )
                r_up = self.opencli("eval", check=False, noisy=False, cmd_extra=check_js)
                up_out = (r_up.stdout or "").strip()
                if up_i == 0 or up_i % 3 == 0:
                    print(f"    ... {up_out}")
            print(f"  图片插入完成")

    def click_publish(self, mode: str = "draft"):
        btn_text = "存草稿" if mode == "draft" else "发布"
        print(f"\n[4/4] 点击「{btn_text}」...")

        # Step 1: Click the correct button (all via _rc for reliability)
        if mode == "draft":
            r = self.opencli("eval", check=False,
                            cmd_extra=(
                                f'{REACT_CLICK_JS}'
                                f'(function(){{'
                                f'var btns=document.querySelectorAll("button.cheetah-btn-default");'
                                f'for(var i=0;i<btns.length;i++){{'
                                f'if((btns[i].innerText||"").trim()==="{btn_text}"){{'
                                f'var rcResult=_rc(btns[i]);'
                                f'return"clicked_draft via:"+rcResult;'
                                f'}}'
                                f'}}'
                                f'return"draft_btn_not_found";'
                                f'}})()'
                            ))
        else:
            r = self.opencli("eval", check=False,
                            cmd_extra=(
                                f"{REACT_CLICK_JS}"
                                f"_rc('button.cheetah-btn-primary');"
                            ))
        out = (r.stdout or "").strip()
        print(f"  点击: {out[:80]}")
        time.sleep(3)

        if "btn_not_found" in out:
            print(f"  [WARN] 按钮未找到")
            return False

        # Step 2: check URL
        r2 = self.opencli("eval", check=False, noisy=False,
                         cmd_extra="window.location.href")
        cur_url = (r2.stdout or "").strip()
        print(f"  当前URL: {cur_url[:120]}")
        # Draft success: URL gets article_id param
        if mode == "draft" and "article_id=" in cur_url:
            print(f"  草稿已保存 (article_id)")
            return True
        # Publish success: navigate away from editor
        if mode != "draft" and "edit" not in cur_url:
            print(f"  页面已跳转，后台验证...")
            return self._verify_published()

        # Step 3: handle modals
        for attempt in range(10):
            r3 = self.opencli("eval", check=False, noisy=False,
                             cmd_extra=(
                                 "(function(){"
                                 "var r=[];"
                                 "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                 "if(cm&&cm.offsetParent!==null){"
                                 "var txt=(cm.innerText||'').trim().substring(0,200);"
                                 "r.push('cheetah:'+txt);"
                                 "}"
                                 "var rm=document.querySelector('#resModal');"
                                 "if(rm&&rm.offsetParent!==null)r.push('resModal');"
                                 "var am=document.querySelector('#audio-insert-modal');"
                                 "if(am&&am.offsetParent!==null)r.push('audio');"
                                 "return r.length?JSON.stringify(r):'no_modals';"
                                 "})()"
                             ))
            status = (r3.stdout or "").strip()
            if status == "no_modals":
                print(f"  无弹窗，{'存草稿' if mode == 'draft' else '发布'}完成")
                break
            print(f"  弹窗({attempt+1}): {status[:200]}")

            # Handle cheetah-modal
            if "cheetah" in status:
                # Distinguish: warning (error/failure) vs confirmation (cover review / publish confirm)
                is_error = any(w in status for w in ["不正确", "格式错误", "失败", "不支持", "无法"])
                is_cover_review = any(w in status for w in ["封面", "头图", "预览", "上传"])
                is_publish_confirm = any(w in status for w in ["发布", "提交", "确认发布"])

                if is_error:
                    print(f"    -> 检测到错误弹窗，尝试关闭...")
                    r_close = self.opencli("eval", check=False,
                                cmd_extra=(
                                    f"{REACT_CLICK_JS}"
                                    "(function(){"
                                    "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                    "if(!cm)return'no_modal';"
                                    "var closeBtn=cm.querySelector('.cheetah-modal-close');"
                                    "if(closeBtn){var r=_rc(closeBtn);return r;}"
                                    "var btns=cm.querySelectorAll('button');"
                                    "for(var i=0;i<btns.length;i++){"
                                    "var t=(btns[i].innerText||'').trim();"
                                    "if(t.indexOf('取消')!==-1){return _rc(btns[i]);}"
                                    "}"
                                    "for(var j=0;j<btns.length;j++){"
                                    "var t2=(btns[j].innerText||'').trim();"
                                    "if(t2.indexOf('确定')!==-1){return _rc(btns[j]);}"
                                    "}"
                                    "return'no_close_btn';"
                                    "})()"
                                ))
                    close_result = (r_close.stdout or "").strip()
                    # If React click didn't dismiss, force-remove the modal overlay
                    time.sleep(1)
                    self.opencli("eval", check=False, noisy=False,
                                cmd_extra=(
                                    "(function(){"
                                    "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                    "if(cm){cm.remove();return'removed';}"
                                    "return'gone';"
                                    "})()"
                                ))
                    print(f"    关闭: {close_result[:60]}")
                    time.sleep(3)
                    print(f"    重新点击「{btn_text}」...")
                    if mode == "draft":
                        self.opencli("eval", check=False,
                                    cmd_extra=(
                                        f'{REACT_CLICK_JS}'
                                        f'(function(){{'
                                        f'var btns=document.querySelectorAll("button.cheetah-btn-default");'
                                        f'for(var i=0;i<btns.length;i++){{'
                                        f'if((btns[i].innerText||"").trim()==="{btn_text}"){{'
                                        f'var rcResult=_rc(btns[i]);'
                                        f'return"reclicked_draft via:"+rcResult;'
                                        f'}}'
                                        f'}}'
                                        f'return"draft_btn_not_found";'
                                        f'}})()'
                                    ))
                    else:
                        self.opencli("eval", check=False,
                                    cmd_extra=(
                                        f"{REACT_CLICK_JS}"
                                        f"_rc('button.cheetah-btn-primary');"
                                    ))
                    time.sleep(3)
                    continue

                # Cover review or publish confirmation — click "确定" in the modal
                if is_cover_review:
                    print(f"    -> 封面预览弹窗，点击确定继续...")
                else:
                    print(f"    -> 发布确认弹窗，点击确定...")

                # Click the "确定" button INSIDE the cheetah-modal, NOT the main publish button
                # Try multiple click strategies: _rc → native click → querySelector click
                confirm_js = (
                    f"{REACT_CLICK_JS}"
                    "(function(){"
                    "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                    "if(!cm)return'no_modal';"
                    "var btns=cm.querySelectorAll('button');"
                    "var found=null;"
                    "for(var i=0;i<btns.length;i++){"
                    "var t=(btns[i].innerText||'').trim();"
                    "if(t==='确定'||t==='确认'){found=btns[i];break;}"
                    "}"
                    "if(!found){"
                    "var pb=cm.querySelector('button.cheetah-btn-primary');"
                    "if(pb)found=pb;"
                    "}"
                    "if(!found)return'no_confirm_btn';"
                    # Try _rc first
                    "var rcResult=_rc(found);"
                    # Also try native click as fallback
                    "setTimeout(function(){found.click();found.dispatchEvent(new Event('click',{bubbles:true}));},200);"
                    "return'clicked:'+rcResult+' btnTxt:'+(found.innerText||'').trim();"
                    "})()"
                )
                self.opencli("eval", check=False, cmd_extra=confirm_js)
                time.sleep(5)

                # After clicking, check if modal still there
                r_m2 = self.opencli("eval", check=False, noisy=False,
                                 cmd_extra=(
                                     "(function(){"
                                     "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                     "if(!cm||cm.offsetParent===null)return'modal_gone';"
                                     "var txt=(cm.innerText||'').trim().substring(0,300);"
                                     "var btns=cm.querySelectorAll('button');"
                                     "var btnTxts=[];"
                                     "for(var i=0;i<btns.length;i++){btnTxts.push((btns[i].innerText||'').trim());}"
                                     "return'modal_still:'+txt+' btns:['+btnTxts.join(',')+']';"
                                     "})()"
                                 ))
                modal_state = (r_m2.stdout or "").strip()
                print(f"    点击后弹窗状态: {modal_state[:200]}")

                # If modal gone, check success
                if "modal_gone" in modal_state:
                    r_url = self.opencli("eval", check=False, noisy=False,
                                        cmd_extra="window.location.href")
                    new_url = (r_url.stdout or "").strip()
                    if "edit" not in new_url:
                        print(f"  弹窗关闭+页面跳转，后台验证...")
                        return self._verify_published()
                    if "article_id=" in new_url:
                        print(f"  已发布 (article_id)，后台验证...")
                        return self._verify_published()
                    # Cover modal dismissed but not published — re-click publish
                    if is_cover_review and mode != "draft":
                        print(f"    封面已确认，再次点击发布...")
                        time.sleep(1)
                        self.opencli("eval", check=False,
                                    cmd_extra=(
                                        f"{REACT_CLICK_JS}"
                                        f"_rc('button.cheetah-btn-primary');"
                                    ))
                        time.sleep(3)
                    continue

                # Modal still there after click — try force-dismiss if all else fails
                if "modal_still" in modal_state:
                    self.opencli("eval", check=False, noisy=False,
                                cmd_extra=(
                                    f"{REACT_CLICK_JS}"
                                    "(function(){"
                                    "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                    "if(!cm)return'no_modal';"
                                    # Try close button first
                                    "var cb=cm.querySelector('.cheetah-modal-close,.cheetah-modal-close-btn');"
                                    "if(cb){_rc(cb);setTimeout(function(){cb.click();},100);return 'close_btn';}"
                                    # Then try ANY button with 确定/确认
                                    "var btns=cm.querySelectorAll('button');"
                                    "for(var i=0;i<btns.length;i++){"
                                    "var t=(btns[i].innerText||btns[i].textContent||'');"
                                    "if(t.indexOf('确定')!==-1||t.indexOf('确认')!==-1||t.indexOf('完成')!==-1){"
                                    "btns[i].click();"
                                    "btns[i].dispatchEvent(new Event('click',{bubbles:true}));"
                                    "_rc(btns[i]);"
                                    "return 'clicked_all:'+t;"
                                    "}"
                                    "}"
                                    # Last resort: remove modal overlay
                                    "cm.remove();return'force_removed';"
                                    "})()"
                                ))
                    time.sleep(3)
                    # Re-check after force attempt
                    r_m3 = self.opencli("eval", check=False, noisy=False,
                                     cmd_extra=(
                                         "!!document.querySelector('[role=\"dialog\"].cheetah-modal')"
                                         "&&document.querySelector('[role=\"dialog\"].cheetah-modal')"
                                         ".offsetParent!==null"
                                     ))
                    if "false" in (r_m3.stdout or "").strip():
                        print(f"    弹窗已关闭")
                        # Re-click publish if modal was dismissed
                        if is_cover_review and mode != "draft":
                            time.sleep(1)
                            self.opencli("eval", check=False,
                                        cmd_extra=(
                                            f"{REACT_CLICK_JS}"
                                            f"_rc('button.cheetah-btn-primary');"
                                        ))
                            time.sleep(3)
                    else:
                        print(f"    [WARN] 弹窗仍存在，继续重试...")
                continue

            # Handle resModal
            if "resModal" in status:
                self.opencli("eval", check=False,
                            cmd_extra=(
                                f"{REACT_CLICK_JS}"
                                f"_rc('#resModal .bjh-btn-primary');"
                            ))
                print(f"    点 resModal 确认")
                time.sleep(2)
                continue

            # Handle audio-insert-modal
            if "audio" in status:
                self.opencli("eval", check=False,
                            cmd_extra=(
                                f"{REACT_CLICK_JS}"
                                f"_rc('#audio-insert-modal .bjh-btn-primary');"
                            ))
                print(f"    点 audioModal 确认")
                time.sleep(2)
                continue

        r_final = self.opencli("eval", check=False, noisy=False,
                              cmd_extra="window.location.href")
        final_url = (r_final.stdout or "").strip()
        if mode == "draft" and "article_id=" in final_url:
            print(f"  草稿已保存 (article_id)")
            return True
        elif mode != "draft" and "edit" not in final_url:
            print(f"  最终URL已跳转，后台验证...")
            return self._verify_published()

        # URL 未变，去后台列表做最终验证
        print(f"  已点击「{btn_text}」(URL未变，后台验证...)")
        return self._verify_published()

    def _verify_published(self) -> bool:
        """去后台文章列表搜标题验证是否真的发布了（含审核中状态 + 重试）"""
        title = getattr(self, '_article_title', '')
        if not title:
            print(f"  [验证] 无标题，无法验证")
            return False

        check_key = title[:15]
        print(f"  [验证] 去后台列表搜索「{check_key}」...")

        for verify_attempt in range(3):
            if verify_attempt > 0:
                wait = 4 * verify_attempt
                print(f"  [验证] 第{verify_attempt+1}次尝试，等待{wait}秒...")
                time.sleep(wait)

            self.opencli('open "https://baijiahao.baidu.com/builder/rc/content"', check=False, timeout=30)
            time.sleep(4)

            r = self.opencli("eval", check=False, noisy=False,
                             cmd_extra="(function(){return document.body.innerText;})()", timeout=15)
            if r.returncode != 0 or not r.stdout:
                print(f"  [验证] 无法读取后台页面")
                continue

            text = r.stdout

            # 标题 + 审核中/已发布 同时出现才确认
            if check_key in text:
                # 检查标题附近是否有 审核中 或 已发布
                idx = text.index(check_key)
                nearby = text[max(0, idx-10):idx+80]
                if "审核中" in nearby or "已发布" in nearby:
                    print(f"  [验证] 后台确认：文章已提交 ✓ (状态: {'审核中' if '审核中' in nearby else '已发布'})")
                    return True
                print(f"  [验证] 找到标题但状态未知: {nearby[:60]}...")

            # 短匹配兜底
            if len(check_key) > 10 and check_key[:10] in text:
                idx2 = text.index(check_key[:10])
                nearby2 = text[max(0, idx2-10):idx2+80]
                if "审核中" in nearby2 or "已发布" in nearby2:
                    print(f"  [验证] 后台确认（短匹配）✓")
                    return True

        print(f"  [验证] 后台未找到文章（可能仍在审核队列中，稍后可用 readback 确认）")
        return False

    def set_cover_image(self, cover_path) -> bool:
        """chunk + File injection — 绕过 HTTP 服务器"""
        import base64 as b64
        from PIL import Image
        import io

        if not cover_path or not cover_path.exists():
            return False

        print(f"\n[封面] 上传封面图: {cover_path.name}")
        fname = cover_path.name

        # Step 1: click "选择封面" or "重新选择"
        step1_js = (
            f"{REACT_CLICK_JS}"
            f"(function(){{"
            f"var coverBtn=null;"
            f"var all=document.querySelectorAll('div,span,button');"
            f"for(var i=0;i<all.length;i++){{"
            f"var el=all[i];"
            f"var txt=(el.innerText||'').trim();"
            f"if(el.children.length===0&&(txt==='选择封面'||txt==='重新选择')){{coverBtn=el;break;}}"
            f"}}"
            f"if(!coverBtn){{"
            f"all=document.querySelectorAll('div');"
            f"for(var j=0;j<all.length;j++){{"
            f"var t2=all[j].innerText.trim();"
            f"if((t2.indexOf('选择封面')!==-1||t2.indexOf('重新选择')!==-1)&&all[j].children.length<=2){{"
            f"coverBtn=all[j];break;"
            f"}}"
            f"}}"
            f"}}"
            f"if(!coverBtn)return'cover_btn_not_found';"
            f"coverBtn.click();return'cover_btn_clicked';"
            f"}})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=step1_js)
        print(f"  Step1: {(r.stdout or '').strip()[:80]}")
        time.sleep(2.5)

        # Step 2: PIL 压缩 → base64 → chunk push → JS 组装 → File → inject into input
        pil_img = Image.open(cover_path)
        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
        w, h = pil_img.size
        max_dim = 1200
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            w, h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
        # 百家号封面最小 452×352，目标 ≥ 672×462
        MIN_CW, MIN_CH = 452, 352
        if w < MIN_CW or h < MIN_CH:
            scale = max(MIN_CW / w, MIN_CH / h)
            w, h = int(w * scale), int(h * scale)
            pil_img = pil_img.resize((w, h), Image.LANCZOS)
            print(f"  封面放大至: {w}x{h}（满足最小 {MIN_CW}x{MIN_CH}）")
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=75)
        compressed = buf.getvalue()
        b64_str = b64.b64encode(compressed).decode("ascii")
        data_uri = f"data:image/jpeg;base64,{b64_str}"
        kb = len(compressed) // 1024
        print(f"  Step2: 压缩 {w}x{h} {kb}KB → base64 {len(b64_str)//1024}KB")

        # Chunk push
        chunk_size = 4000
        chunks = [data_uri[i:i+chunk_size] for i in range(0, len(data_uri), chunk_size)]
        print(f"  Step2: {len(chunks)} 个 chunk...")

        init_js = f"(function(){{window._coverChunks=[];}})()"
        self.opencli("eval", check=False, noisy=False, cmd_extra=init_js)
        for ci, chunk in enumerate(chunks):
            escaped_chunk = json.dumps(chunk, ensure_ascii=False)
            push_js = f"(function(){{window._coverChunks.push({escaped_chunk});}})()"
            self.opencli("eval", check=False, noisy=False, cmd_extra=push_js)
            if ci % 5 == 0:
                print(f"    chunk {ci+1}/{len(chunks)}")

        # Assemble → File → inject into file input → trigger React onChange
        step2_js = (
            f"{REACT_CLICK_JS}"
            f"(function(){{"
            f"try{{"
            # Assemble data URI → Blob → File
            f"var dataUri=window._coverChunks.join('');"
            f"delete window._coverChunks;"
            f"var arr=dataUri.split(',');var mime=arr[0].match(/:(.*?);/)[1];"
            f"var bstr=atob(arr[1]);var n=bstr.length;"
            f"var u8arr=new Uint8Array(n);while(n--){{u8arr[n]=bstr.charCodeAt(n);}}"
            f"var file=new File([u8arr],'{fname}',{{type:mime}});"
            f"var dt=new DataTransfer();dt.items.add(file);"
            # Search for file input: cheetah-modal → document
            f"var inputs=document.querySelectorAll('[role=\"dialog\"].cheetah-modal input[type=\"file\"]');"
            f"if(inputs.length===0){{"
            f"inputs=document.querySelectorAll('#audio-insert-modal input[type=\"file\"]');"
            f"}}"
            f"if(inputs.length===0){{"
            f"inputs=document.querySelectorAll('input[type=\"file\"]');"
            f"}}"
            f"var injected=0;"
            f"for(var k=0;k<inputs.length;k++){{"
            f"var inp=inputs[k];"
            f"var accept=(inp.getAttribute('accept')||'').toLowerCase();"
            f"if(accept.indexOf('video')!==-1)continue;"
            f"inp.files=dt.files;"
            f"var evt=new Event('change',{{bubbles:true,cancelable:true}});"
            f"try{{Object.defineProperty(evt,'target',{{value:inp,configurable:true}});}}catch(ed){{}}"
            f"try{{Object.defineProperty(evt,'currentTarget',{{value:inp,configurable:true}});}}catch(ed2){{}}"
            f"var keys=Object.keys(inp);var reacted=false;"
            f"for(var ki=0;ki<keys.length;ki++){{"
            f"var kk=keys[ki];"
            f"if(kk.indexOf('__reactProps')===0){{"
            f"var rp=inp[kk];if(typeof rp.onChange==='function'){{rp.onChange(evt);reacted=true;break;}}"
            f"}}"
            f"if(kk.indexOf('__reactEventHandlers')===0){{"
            f"var rh=inp[kk];if(typeof rh.onChange==='function'){{rh.onChange(evt);reacted=true;break;}}"
            f"}}"
            f"}}"
            f"if(!reacted){{inp.dispatchEvent(evt);inp.dispatchEvent(new Event('input',{{bubbles:true}}));}}"
            f"injected++;"
            f"}}"
            f"return'step2_ok injected:'+injected;"
            f"}}catch(e){{return'step2_err:'+e.message;}}"
            f"}})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=step2_js)
        try:
            print(f"  Step2: {(r.stdout or '').strip()[:120]}")
        except UnicodeEncodeError:
            pass
        time.sleep(1.5)

        # Step 3: click "确认/确定" button
        step3_js = (
            f"{REACT_CLICK_JS}"
            f"(function(){{"
            f"var root=document.querySelector('[role=\"dialog\"].cheetah-modal');"
            f"if(!root){{root=document.querySelector('#audio-insert-modal');}}"
            f"if(!root){{root=document;}}"
            f"var btns=root.querySelectorAll('button');"
            f"for(var i=0;i<btns.length;i++){{"
            f"var t=(btns[i].innerText||btns[i].textContent||'').trim();"
            f"if(t==='确认'||t==='确定'){{return _rc(btns[i]);}}"
            f"}}"
            f"var pb=root.querySelector('button.cheetah-btn-primary');"
            f"if(pb)return _rc(pb);"
            f"for(var j=0;j<btns.length;j++){{"
            f"var t2=(btns[j].innerText||btns[j].textContent||'');"
            f"if(t2.indexOf('确认')!==-1||t2.indexOf('确定')!==-1){{return _rc(btns[j]);}}"
            f"}}"
            f"var allBtns=document.querySelectorAll('button');"
            f"for(var k=0;k<allBtns.length;k++){{"
            f"var at=(allBtns[k].innerText||allBtns[k].textContent||'').trim();"
            f"if(at==='确认'||at==='确定'){{return _rc(allBtns[k]);}}"
            f"}}"
            f"return'confirm_btn_not_found';"
            f"}})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=step3_js)
        try:
            print(f"  Step3: {(r.stdout or '').strip()[:80]}")
        except UnicodeEncodeError:
            pass
        time.sleep(2)
        return True

    def _verify_content(self, article: dict):
        print("\n[验证] 延迟回读标题与正文...")
        r = self.opencli("eval", check=False,
                         cmd_extra=(
                             f"{FIND_TITLE_JS}{FIND_EL_JS}"
                             f"(()=>{{"
                             f"var t=_ft();var c=_f('{CONTENT_SEL}');"
                             f"var tv=t?(t.innerText||t.textContent||'').substring(0,40):'no_title_el';"
                             f"var cv=c?(c.innerText||c.textContent||'').substring(0,40):'no_content_el';"
                             f"return'title:'+tv+'; content:'+cv;"
                             f"}})()"
                         ))
        try:
            print(f"  页面实际值: {(r.stdout or '').strip()[:300]}")
        except UnicodeEncodeError:
            pass
