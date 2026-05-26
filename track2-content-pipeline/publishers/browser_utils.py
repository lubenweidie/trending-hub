"""浏览器操作共享常量 — JS 代码片段，供各平台发布器复用"""

# 从任意页面提取图片 URL（过滤 UI 元素、头像、图标等）
IMG_EXTRACT_JS = (
    "(function(){"
    "var imgs=document.querySelectorAll('img,video[poster]');"
    "var r=[];"
    "var skipPaths=['activity-plat/static','avatar','icon','logo','btn','qr_code','qrcode'];"
    "for(var i=0;i<imgs.length;i++){"
    "var el=imgs[i];var src=el.src||el.getAttribute('poster')||'';"
    "var w=el.naturalWidth||el.width||el.videoWidth||0;"
    "var h=el.naturalHeight||el.height||el.videoHeight||0;"
    "var alt=(el.alt||'').toLowerCase();"
    "var isUI=/权限|示意|控制|提示|说明|扫码|二维码|logo|图标|头像/.test(alt);"
    "var isSkipPath=skipPaths.some(function(p){return src.indexOf(p)!==-1;});"
    "if(!isUI&&!isSkipPath&&w>=400&&h>=300&&src&&src.indexOf('data:')!==0&&src.indexOf('.svg')===-1){"
    "r.push({src:src,w:w,h:h,alt:(el.alt||'').substring(0,60)});"
    "}"
    "}"
    "r.sort(function(a,b){return(b.w*b.h)-(a.w*a.h);});"
    "return JSON.stringify(r.slice(0,10));"
    "})()"
)

# 在文档及 iframe 中查找元素
FIND_EL_JS = (
    "var _f=function(s){"
    "var el=document.querySelector(s);if(el)return el;"
    "var ifs=document.querySelectorAll('iframe');"
    "for(var i=0;i<ifs.length;i++){try{"
    "var d=ifs[i].contentDocument;if(d){el=d.querySelector(s);if(el)return el;}"
    "}catch(e){}}"
    "return null;};"
)

# React 17+ 合成事件系统多策略点击
REACT_CLICK_JS = (
    "var _rc=function(el){"
    "if(typeof el==='string')el=document.querySelector(el);"
    "if(!el)return'no_el';"
    "var evt=new MouseEvent('click',{bubbles:true,cancelable:true,view:window});"
    "evt._reactName='onClick';"
    "var keys=Object.keys(el);"
    "for(var i=0;i<keys.length;i++){"
    "var k=keys[i];"
    "if(k.indexOf('__reactEventHandlers')===0){"
    "var h=el[k];if(h.onClick){h.onClick(evt);return'react_handlers';}"
    "}"
    "if(k.indexOf('__reactProps')===0){"
    "var p=el[k];if(p.onClick){p.onClick(evt);return'react_props';}"
    "}"
    "}"
    # React 16/17 fiber keys: __reactFiber$xxx (React 17), __reactInternalInstance$xxx (React 16)
    "for(var j=0;j<keys.length;j++){"
    "var fk=keys[j];"
    "if(fk.indexOf('__reactFiber')===0||fk.indexOf('__reactInternalInstance')===0){"
    "var fiber=el[fk];var node=fiber;"
    "while(node){"
    "var mp=node.memoizedProps;"
    "if(mp&&typeof mp.onClick==='function'){mp.onClick(evt);return'fiber_onClick';}"
    "if(mp&&typeof mp.onTouchTap==='function'){mp.onTouchTap(evt);return'fiber_onTouchTap';}"
    "node=node.return;"
    "}"
    "break;"
    "}"
    "}"
    "el.dispatchEvent(evt);el.click();return'native';"
    "};"
)

# 图片加载 + canvas 缩放 → dataURI（供各平台插入编辑器前预处理）
# 使用方式: 在 async IIFE 中调用，返回 {{dataUri, w, h}}
LOAD_IMAGE_JS_TEMPLATE = (
    "var img=new Image();img.crossOrigin='anonymous';"
    "await new Promise(function(resolve,reject){{"
    "img.onload=resolve;img.onerror=function(){{reject(new Error('load_fail'));}};"
    "img.src='{img_url}?t='+Date.now();"
    "}});"
    "var maxDim=450,w=img.naturalWidth,h=img.naturalHeight;"
    "if(w>maxDim||h>maxDim){{var s=Math.min(maxDim/w,maxDim/h);w=Math.round(w*s);h=Math.round(h*s);}}"
    "var c=document.createElement('canvas');c.width=w;c.height=h;"
    "c.getContext('2d').drawImage(img,0,0,w,h);"
    "var dataUri=c.toDataURL('image/jpeg',0.7);"
)
