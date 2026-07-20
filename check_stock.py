"""
E-Capcom 商品有貨監察器
每次 run:
  1. 攞商品頁面 HTML
  2. 分析係缺貨 (在庫：×) 定 有貨
  3. 對比上次狀態(state.json),只喺「缺貨 → 有貨」轉變嗰刻 push ntfy
  4. HK 時間 ≥ 09:00 且今日未 send 過 heartbeat → 順便 send 每日 heartbeat
  5. 更新 state.json

Env vars:
  NTFY_TOPIC        — ntfy topic 名。支援 comma-separated 多 topic
                       例:"Jamie01,TestMode" 兩個 topic 都會收到
  PRODUCT_URL       — 商品 URL (可 override default)
  PRODUCT_NAME      — 商品名 (用喺 notification 標題)
"""
import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── 配置 ─────────────────────────────────────────────────────────────
_raw_topics = os.environ.get("NTFY_TOPIC", "").strip()
NTFY_TOPICS = [t.strip() for t in _raw_topics.split(",") if t.strip()]

PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "https://www.e-capcom.com/shop/g/gC00008302/",
).strip()
PRODUCT_NAME = os.environ.get(
    "PRODUCT_NAME",
    "Rockman Granny Street Fighter 6 Jamie",
).strip()

STATE_FILE = Path(__file__).parent / "state.json"
HK_TZ = timezone(timedelta(hours=8))
HEARTBEAT_HK_HOUR = 9  # HK 09:00 之後嘅第一次 check 會 send heartbeat

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Safari/605.1.15"
)


# ─── Helpers ──────────────────────────────────────────────────────────
def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ("shift_jis", "cp932", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def detect_stock(html: str) -> str:
    """Return 'in_stock' / 'out_of_stock' / 'unknown'."""
    if "在庫：×" in html:
        return "out_of_stock"
    if "color_Selected_ color_DisableStock_" in html or 'id="nostock"' in html:
        return "out_of_stock"
    if "在庫：○" in html or "在庫：△" in html:
        return "in_stock"
    if "color_Selected_ color_EnableStock_" in html:
        return "in_stock"
    return "unknown"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_status": "out_of_stock", "last_checked": 0}


def save_state(state: dict):
    state["last_checked"] = int(time.time())
    STATE_FILE.write_text(json.dumps(state, indent=2))


def extract_goods_id(url: str) -> str:
    m = re.search(r"/g/g([A-Z0-9]+)", url)
    return m.group(1) if m else ""


def _post_ntfy(topic: str, message: bytes, headers: dict) -> bool:
    url = f"https://ntfy.sh/{topic}"
    req = urllib.request.Request(url, data=message, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[ntfy:{topic}] pushed OK ({r.status})")
        return True
    except urllib.error.HTTPError as e:
        print(f"[ntfy:{topic}] HTTP error: {e.code} {e.reason}")
    except Exception as e:
        print(f"[ntfy:{topic}] fail: {e}")
    return False


def push_ntfy(title: str, message: str, priority: int = 5, click: str = None,
              tags: str = None, actions: str = None) -> bool:
    """Send push via ntfy.sh — 逐個 topic 都 push"""
    if not NTFY_TOPICS:
        print("[WARN] NTFY_TOPIC 未設定,skip push")
        return False
    headers_base = {
        "Title": title.encode("utf-8"),
        "Priority": str(priority),
    }
    if click:
        headers_base["Click"] = click
    if tags:
        headers_base["Tags"] = tags
    if actions:
        headers_base["Actions"] = actions.encode("utf-8")

    body = message.encode("utf-8")
    any_ok = False
    for topic in NTFY_TOPICS:
        if _post_ntfy(topic, body, dict(headers_base)):
            any_ok = True
    return any_ok


def maybe_send_heartbeat(state: dict, current_status: str):
    """HK ≥ 09:00 而今日未 send 過 → send heartbeat + mark。"""
    now_hk = datetime.now(HK_TZ)
    today_hk = now_hk.strftime("%Y-%m-%d")
    last_hb = state.get("last_heartbeat_date")

    if now_hk.hour < HEARTBEAT_HK_HOUR:
        return
    if last_hb == today_hk:
        return

    print(f"→ Sending daily heartbeat (HK {now_hk:%H:%M})")
    status_display = {
        "out_of_stock": "🔴 缺貨",
        "in_stock": "🟢 有貨",
        "unknown": "⚪ 未知",
    }.get(current_status, f"⚠️ {current_status}")

    ok = push_ntfy(
        title="💓 Capcom Monitor 運行中",
        message=(
            f"監察緊: {PRODUCT_NAME}\n"
            f"現況: {status_display}\n"
            f"下次 heartbeat: 明日 HK 09:00"
        ),
        priority=2,
        tags="heart",
    )
    if ok:
        state["last_heartbeat_date"] = today_hk


# ─── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"→ Checking: {PRODUCT_URL}")
    print(f"→ NTFY topics: {NTFY_TOPICS or '(未設定)'}")
    try:
        html = fetch_html(PRODUCT_URL)
    except Exception as e:
        print(f"[ERR] fetch fail: {e}")
        sys.exit(0)

    status = detect_stock(html)
    print(f"→ Detected: {status}")

    state = load_state()
    prev = state.get("last_status", "unknown")
    print(f"→ Previous: {prev}")

    if status == "in_stock" and prev != "in_stock":
        print("🎉 STOCK AVAILABLE — sending push!")
        goods_id = extract_goods_id(PRODUCT_URL)
        cart_url = (
            f"https://www.e-capcom.com/shop/cart/cart.aspx?goods={goods_id}"
            if goods_id else PRODUCT_URL
        )
        actions = (
            f"view, 🛒 加入 Cart 去結帳, {cart_url}, clear=true;"
            f"view, 👀 睇商品詳情, {PRODUCT_URL}, clear=true"
        )
        push_ntfy(
            title=f"🎉 {PRODUCT_NAME} 有貨!",
            message=f"撳「🛒 加入 Cart 去結帳」自動 add to cart:\n{PRODUCT_URL}",
            priority=5,
            click=cart_url,
            tags="rotating_light,shopping_cart",
            actions=actions,
        )

    if status != "unknown":
        state["last_status"] = status

    maybe_send_heartbeat(state, status)
    save_state(state)


if __name__ == "__main__":
    main()
