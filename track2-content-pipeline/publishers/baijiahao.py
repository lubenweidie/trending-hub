"""百家号发布器"""
import json
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
        time.sleep(0.5)
        print(f"  标题已输入")

    def fill_content(self, content: str):
        print(f"\n[3/4] 填写正文 ({len(content)}字)...")
        clean = content.strip()[:5000]
        escaped = json.dumps(clean, ensure_ascii=False)
        # Primary approach: execCommand in contenteditable (works through iframes)
        js = (
            f"{FIND_EL_JS}"
            f"(()=>{{"
            f"var el=_f('{CONTENT_SEL}');"
            f"if(!el)return'noel';"
            f"el.focus();"
            f"var doc=el.ownerDocument||document;"
            f"doc.execCommand('selectAll',false,null);"
            f"doc.execCommand('insertText',false,{escaped});"
            f"el.dispatchEvent(new Event('input',{{bubbles:true}}));"
            f"el.dispatchEvent(new Event('change',{{bubbles:true}}));"
            f"var txt=(el.innerText||el.textContent||'').substring(0,40);"
            f"return'content:'+txt+' len:'+(el.innerText||el.textContent||'').length;"
            f"}})()"
        )
        r = self.opencli("eval", check=False, cmd_extra=js)
        result = (r.stdout or "").strip()
        print(f"  正文结果: {result[:120]}")
        # Fallback: direct innerHTML if execCommand didn't work
        if "len:0" in result or "len:1" in result or "noel" in result:
            print(f"  execCommand 未生效，尝试 fallback...")
            safe = clean.replace('\\', '\\\\').replace("'", "\\'")
            fallback_js = (
                f"{FIND_EL_JS}"
                f"(()=>{{"
                f"var el=_f('{CONTENT_SEL}');"
                f"if(!el)return'noel_fb';"
                f"el.focus();"
                f"var doc=el.ownerDocument||document;"
                f"if(doc.body){{doc.body.innerHTML='<p>'+'{safe}'.replace(/\\\\n\\\\n/g,'</p><p>').replace(/\\\\n/g,'<br>')+'</p>';}}"
                f"else{{el.innerHTML='<p>'+'{safe}'.replace(/\\\\n\\\\n/g,'</p><p>').replace(/\\\\n/g,'<br>')+'</p>';}}"
                f"el.dispatchEvent(new Event('input',{{bubbles:true}}));"
                f"el.dispatchEvent(new Event('change',{{bubbles:true}}));"
                f"var t2=(el.innerText||el.textContent||'').substring(0,40);"
                f"return'fb_content:'+t2+' len:'+(el.innerText||el.textContent||'').length;"
                f"}})()"
            )
            r2 = self.opencli("eval", check=False, cmd_extra=fallback_js)
            print(f"  fallback结果: {(r2.stdout or '').strip()[:120]}")
        time.sleep(0.5)
        print(f"  正文已输入")

    def insert_images_to_editor(self, image_paths: list):
        if not image_paths:
            return
        print(f"\n[图片] 插入 {len(image_paths)} 张图片...")
        img_dir = image_paths[0].parent
        port = self._start_image_server(img_dir)
        print(f"  图片服务: http://127.0.0.1:{port}")

        for i, img_path in enumerate(image_paths):
            fname = img_path.name
            print(f"  ({i+1}/{len(image_paths)}) 插入: {fname}")
            js = (
                f"(async function(){{"
                f"try{{"
                f"if(!window.editor||!window.editor.execCommand)return'no_editor';"
                f"var img=new Image();img.crossOrigin='anonymous';"
                f"await new Promise(function(resolve,reject){{"
                f"img.onload=resolve;img.onerror=function(){{reject(new Error('load_fail'));}};"
                f"img.src='http://127.0.0.1:{port}/{fname}?t='+Date.now();"
                f"}});"
                f"var maxDim=450,w=img.naturalWidth,h=img.naturalHeight;"
                f"if(w>maxDim||h>maxDim){{var s=Math.min(maxDim/w,maxDim/h);w=Math.round(w*s);h=Math.round(h*s);}}"
                f"var c=document.createElement('canvas');c.width=w;c.height=h;"
                f"c.getContext('2d').drawImage(img,0,0,w,h);"
                f"var quality=0.7,dataUri,ok=false;"
                f"for(var retry=0;retry<3&&!ok;retry++){{"
                f"dataUri=c.toDataURL('image/jpeg',quality);"
                f"window.editor.execCommand('insertimage',{{src:dataUri,width:w,height:h,_src:dataUri}});"
                f"await new Promise(function(r){{setTimeout(r,800);}});"
                f"ok=window.editor.getContent().indexOf('bjh-image-container')!==-1;"
                f"if(!ok){{quality-=0.2;}}"
                f"}}"
                f"return'inserted:'+(ok?'ok':'fail')+' size:'+Math.round((dataUri||'').length/1024)+'kb';"
                f"}}catch(e){{return'error:'+e.message;}}"
                f"}})()"
            )
            r = self.opencli("eval", check=False, cmd_extra=js)
            try:
                print(f"    结果: {(r.stdout or '').strip()[:120]}")
            except UnicodeEncodeError:
                pass
            time.sleep(1.5)
        print(f"  图片插入完成")

    def click_publish(self, mode: str = "draft"):
        btn_text = "存草稿" if mode == "draft" else "发布"
        print(f"\n[4/4] 点击「{btn_text}」...")

        # Step 1: Click the correct button
        if mode == "draft":
            # Multiple cheetah-btn-default buttons — find by text via eval
            r = self.opencli("eval", check=False,
                            cmd_extra=(
                                f'(function(){{'
                                f'var btns=document.querySelectorAll("button.cheetah-btn-default");'
                                f'for(var i=0;i<btns.length;i++){{'
                                f'if((btns[i].innerText||"").trim()==="{btn_text}"){{'
                                f'btns[i].click();return"clicked_draft";'
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
            print(f"  页面已跳转，发布成功")
            return True

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
                                        f'(function(){{'
                                        f'var btns=document.querySelectorAll("button.cheetah-btn-default");'
                                        f'for(var i=0;i<btns.length;i++){{'
                                        f'if((btns[i].innerText||"").trim()==="{btn_text}"){{'
                                        f'btns[i].click();return"reclicked_draft";'
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
                self.opencli("eval", check=False,
                            cmd_extra=(
                                f"{REACT_CLICK_JS}"
                                "(function(){"
                                "var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
                                "if(!cm)return'no_modal';"
                                "var btns=cm.querySelectorAll('button');"
                                "for(var i=0;i<btns.length;i++){"
                                "var t=(btns[i].innerText||'').trim();"
                                "if(t==='确定'||t==='确认'){return _rc(btns[i]);}"
                                "}"
                                "var pb=cm.querySelector('button.cheetah-btn-primary');"
                                "if(pb)return _rc(pb);"
                                "return'no_confirm_btn';"
                                "})()"
                            ))
                time.sleep(4)

                # Check if publish succeeded or modal dismissed
                r_url = self.opencli("eval", check=False, noisy=False,
                                    cmd_extra="window.location.href")
                new_url = (r_url.stdout or "").strip()
                if "edit" not in new_url:
                    print(f"  页面已跳转，发布成功: {new_url[:100]}")
                    return True
                r_m = self.opencli("eval", check=False, noisy=False,
                                 cmd_extra=(
                                     "!!document.querySelector('[role=\"dialog\"].cheetah-modal')"
                                     "&&document.querySelector('[role=\"dialog\"].cheetah-modal')"
                                     ".offsetParent!==null"
                                 ))
                if "false" in (r_m.stdout or "").strip():
                    if "article_id=" in new_url:
                        print(f"  已发布 (article_id): {new_url[:120]}")
                        return True
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
        elif mode != "draft" and "edit" not in final_url:
            print(f"  页面已跳转，发布成功")
        else:
            print(f"  已点击「{btn_text}」(URL未变，请手动检查)")
        return True

    def set_cover_image(self, cover_path) -> bool:
        if not cover_path or not cover_path.exists():
            return False

        print(f"\n[封面] 上传封面图: {cover_path.name}")

        img_dir = cover_path.parent
        port = self._start_image_server(img_dir)
        fname = cover_path.name
        img_url = f"http://127.0.0.1:{port}/{fname}"

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

        # Step 2: inject image into file input + trigger React onChange
        step2_js = (
            f"{REACT_CLICK_JS}"
            f"(async function(){{"
            f"try{{"
            f"var resp=await fetch('{img_url}');"
            f"if(!resp.ok)return'fetch_fail:'+resp.status;"
            f"var blob=await resp.blob();"
            f"var file=new File([blob],'{fname}',{{type:blob.type||'image/jpeg'}});"
            f"var dt=new DataTransfer();dt.items.add(file);"
            f""
            # Search order: visible cheetah-modal → #audio-insert-modal → whole document
            f"var inputs=document.querySelectorAll('#audio-insert-modal input[type=\"file\"]');"
            f"if(inputs.length===0){{"
            f"var cm=document.querySelector('[role=\"dialog\"].cheetah-modal');"
            f"if(cm){{inputs=cm.querySelectorAll('input[type=\"file\"]');}}"
            f"}}"
            f"if(inputs.length===0){{"
            f"inputs=document.querySelectorAll('input[type=\"file\"]');"
            f"}}"
            f"var injected=0;"
            f"for(var k=0;k<inputs.length;k++){{"
            f"var inp=inputs[k];"
            f"var accept=(inp.getAttribute('accept')||'').toLowerCase();"
            f"if(accept.indexOf('video')!==-1)continue;"
            # Set files on input, then trigger React onChange (with target set on event)
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
            print(f"  Step2: {(r.stdout or '').strip()[:200]}")
        except UnicodeEncodeError:
            pass
        time.sleep(1)

        # Step 3: click "确认/确定" button using React-aware _rc
        step3_js = (
            f"{REACT_CLICK_JS}"
            f"(function(){{"
            # Search cheetah-modal first, then audio-insert-modal, then document
            f"var root=document.querySelector('[role=\"dialog\"].cheetah-modal');"
            f"if(!root){{root=document.querySelector('#audio-insert-modal');}}"
            f"if(!root){{root=document;}}"
            # Try exact match first
            f"var btns=root.querySelectorAll('button');"
            f"for(var i=0;i<btns.length;i++){{"
            f"var t=(btns[i].innerText||btns[i].textContent||'').trim();"
            f"if(t==='确认'||t==='确定'){{return _rc(btns[i]);}}"
            f"}}"
            # Fallback: primary button
            f"var pb=root.querySelector('button.cheetah-btn-primary');"
            f"if(pb)return _rc(pb);"
            # Broader search: contains 确认/确定
            f"for(var j=0;j<btns.length;j++){{"
            f"var t2=(btns[j].innerText||btns[j].textContent||'');"
            f"if(t2.indexOf('确认')!==-1||t2.indexOf('确定')!==-1){{return _rc(btns[j]);}}"
            f"}}"
            # Global search
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
