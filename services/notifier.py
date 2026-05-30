"""发布结果通知 — 本地摘要 + 邮件 + Webhook 推送"""
import json
import os
import smtplib
import urllib.request
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "logs" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class RunResult:
    """单次发布运行的结果收集器（线程安全）"""
    def __init__(self):
        import threading
        self.start_time = datetime.now()
        self.platforms: dict[str, dict] = {}
        self.articles_generated = 0
        self.articles_leftover = 0
        self._lock = threading.Lock()

    def set_articles(self, generated: int, leftover: int = 0):
        self.articles_generated = generated
        self.articles_leftover = leftover

    def add_platform(self, name: str, title: str, ok: bool, url: str = "", error: str = ""):
        with self._lock:
            # 同一平台多账号用 name/account_name 做区分 key
            key = name if name not in self.platforms else f"{name}({len(self.platforms)})"
            self.platforms[key] = {
                "title": title,
                "status": "ok" if ok else "fail",
                "url": url,
                "error": error,
            }

    def to_dict(self) -> dict:
        total = len(self.platforms)
        ok_count = sum(1 for p in self.platforms.values() if p["status"] == "ok")
        return {
            "time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "generated": self.articles_generated,
            "leftover": self.articles_leftover,
            "summary": f"{ok_count}/{total} 成功",
            "platforms": self.platforms,
        }

    def save_and_notify(self):
        """保存结果摘要 + 推送通知"""
        data = self.to_dict()
        ts = self.start_time.strftime("%Y%m%d_%H%M%S")
        result_file = RESULTS_DIR / f"result_{ts}.json"
        result_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[结果] 已保存: {result_file.name}")

        # 邮件通知
        self._push_email(data)

        # Webhook 推送
        webhook_url = os.environ.get("NOTIFY_WEBHOOK", "")
        if webhook_url:
            self._push_webhook(webhook_url, data)

    def _build_body(self, data: dict) -> str:
        lines = [f"{data['summary']} | {data['time']}", ""]
        for name, p in data["platforms"].items():
            icon = "✓" if p["status"] == "ok" else "✗"
            title = p["title"]
            detail = f" ({p['error']})" if p.get("error") else ""
            lines.append(f"  {icon} {name}: {title}{detail}")
        lines.append("")
        lines.append(f"生成 {data['generated']} 篇，剩余 {data['leftover']} 篇")
        return "\n".join(lines)

    def _push_email(self, data: dict):
        smtp_host = os.environ.get("SMTP_HOST", "")
        if not smtp_host:
            return
        try:
            msg = MIMEText(self._build_body(data), "plain", "utf-8")
            titles = [p["title"] for p in data["platforms"].values()]
            title_part = " | ".join(titles)
            msg["Subject"] = f"[发布] {title_part} | {data['summary']}"
            msg["From"] = os.environ.get("SMTP_FROM", "")
            msg["To"] = os.environ.get("SMTP_TO", "")

            port = int(os.environ.get("SMTP_PORT", "587"))
            user = os.environ.get("SMTP_USER", "")
            password = os.environ.get("SMTP_PASS", "")

            # 先试 SSL(465)，再试 STARTTLS(587)
            for use_ssl in ([True] if port == 465 else [True, False]):
                try:
                    if use_ssl:
                        server = smtplib.SMTP_SSL(smtp_host, port, timeout=15)
                    else:
                        server = smtplib.SMTP(smtp_host, port, timeout=15)
                        server.starttls()
                    server.login(user, password)
                    server.send_message(msg)
                    server.quit()
                    print(f"[通知] 邮件已发送 → {msg['To']}")
                    return
                except Exception:
                    pass
            raise Exception("all SMTP attempts failed")
        except Exception as e:
            print(f"[通知] 邮件发送失败: {e}")

    def _fix_serverchan_url(self, url: str) -> str:
        """自动修正 Server酱 旧版 URL 到新版"""
        if "sct.ftqq.com" in url and "sctapi.ftqq.com" not in url:
            url = url.replace("sct.ftqq.com", "sctapi.ftqq.com")
            if not url.endswith(".send"):
                url += ".send"
        return url

    def _push_webhook(self, url: str, data: dict):
        try:
            url = self._fix_serverchan_url(url)
            msg = self._build_body(data)
            req = urllib.request.Request(
                url,
                data=json.dumps({"title": f"发布 {data['summary']}", "content": msg}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            print(f"[通知] Webhook 已推送")
        except Exception as e:
            print(f"[通知] 推送失败: {e}")


_result: RunResult | None = None


def get_result() -> RunResult:
    global _result
    if _result is None:
        _result = RunResult()
    return _result


def finish_result():
    global _result
    if _result:
        _result.save_and_notify()
        _result = None
