import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

class DingTalkNotifier:
    """
    钉钉自定义机器人 Webhook 推送（支持加签）
    加签算法：timestamp+"\n"+secret -> HmacSHA256 -> base64 -> urlEncode
    再把 timestamp 和 sign 拼到 webhook 上。:contentReference[oaicite:1]{index=1}
    """
    def __init__(self, webhook_url: str, secret: str = ""):
        self.webhook_url = (webhook_url or "").strip()
        self.secret = (secret or "").strip()

    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def _signed_url(self) -> str:
        if not self.secret:
            return self.webhook_url
        ts = str(int(time.time() * 1000))
        string_to_sign = f"{ts}\n{self.secret}".encode("utf-8")
        h = hmac.new(self.secret.encode("utf-8"), string_to_sign, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(h))
        # 钉钉约定：url 上拼 timestamp 和 sign
        sep = "&" if "?" in self.webhook_url else "?"
        return f"{self.webhook_url}{sep}timestamp={ts}&sign={sign}"

    def send_text(self, text: str) -> None:
        if not self.webhook_url:
            return
        url = self._signed_url()
        payload = {"msgtype": "text", "text": {"content": text}}
        requests.post(url, json=payload, timeout=5)
