"""
E-Capcom 商品有貨監察器
每次 run:
  1. 攞商品頁面 HTML
  2. 分析係缺貨 (在庫：×) 定 有貨
  3. 對比上次狀態(state.json),只喺「缺貨 → 有貨」轉變嗰刻 push ntfy
  4. 更新 state.json

Env vars:
  NTFY_TOPIC        — 你 ntfy topic 名 (GitHub Secret,唔會出現喺 log)
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
from pathlib import Path

# ─── 配置 ─────────────────────────────────────────────────────────────
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "https://www.e-capcom.com/shop/g/gC00008302/",
).strip()
PRODUCT_NAME = os.environ.get(
    "PRODUCT_NAME",
    "Rockman Granny Street Fighter 6 Jamie",
).strip()

STATE_FILE = Path(__file__).parent / "state.json"

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
    # e-capcom 用 Shift_JIS。Python decode 時試 shift_jis 先,失敗 fall back
    for enc in ("shift_jis", "cp932", "utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def detect_stock(html: str) -> str:
    """Return 'in_stock' / 'out_of_stock' / 'unknown'."""
    # Signature markers 喺 e-capcom.com:
    #   缺貨: "在庫：×", id="nostock" image, class 有 "color_Selected_ color_DisableStock_"
    #   有貨: "在庫：○" 或 "在庫：△", 有 cart button, "color_Selected_ color_EnableStock_"
    if "在庫：×" in html:
        return "out_of_stock"
    # 選中嗰個 variant class 係 color_DisableStock_ 都當缺貨
    if "color_Selected_ color_DisableStock_" in html or 'id="nostock"' in html:
        return "out_of_stock"
    if "在庫：○" in html or "在庫：△" in html:
        return "in_stock"
    if "color_Selected_ color_EnableStock_" in html:
        return "in_stock"
    # 揾唔到 stock marker(可能網站 down 或 layout 變) — 當 unknown,唔通知
    return "unknown"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    # 第一次 run 假設之前係「缺貨」,避免第一次就 spam
    return {"last_status": "out_of_stock", "last_checked": 0}


def save_state(status: str):
    STATE_FILE.write_text(
        json.dumps(
            {"last_status": status, "last_checked": int(time.time())},
            indent=2,
        )
    )


def extract_goods_id(url: str) -> str:
    """Extract 'C00008302' from 'https://www.e-capcom.com/shop/g/gC00008302/'"""
    m = re.search(r"/g/g([A-Z0-9]+)", url)
    return m.group(1) if m else ""


def push_ntfy(title: str, message: str, priority: int = 5, click: str = None,
              tags: str = None, actions: str = None):
    """Send push via ntfy.sh"""
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC 未設定,skip push")
        return False
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": str(priority),  # 1=min, 5=urgent
    }
    if click:
        headers["Click"] = click
    if tags:
        headers["Tags"] = tags
    if actions:
        # ntfy Actions header:多個 action 用 ';' 分隔,格式:type, label, url
        headers["Actions"] = actions.encode("utf-8")
    req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[ntfy] pushed OK ({r.status})")
        return True
    except urllib.error.HTTPError as e:
        print(f"[ntfy] HTTP error: {e.code} {e.reason}")
    except Exception as e:
        print(f"[ntfy] fail: {e}")
    return False


# ─── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"→ Checking: {PRODUCT_URL}")
    try:
        html = fetch_html(PRODUCT_URL)
    except Exception as e:
        print(f"[ERR] fetch fail: {e}")
        # 網站 down 唔通知,避免 spam
        sys.exit(0)

    status = detect_stock(html)
    print(f"→ Detected: {status}")

    state = load_state()
    prev = state.get("last_status", "unknown")
    print(f"→ Previous: {prev}")

    # 只喺 out_of_stock → in_stock 轉變嗰刻通知
    if status == "in_stock" and prev != "in_stock":
        print("🎉 STOCK AVAILABLE — sending push!")
        goods_id = extract_goods_id(PRODUCT_URL)
        # e-capcom 一鍵加 cart URL:訪問呢個 URL 會自動加 item 入 cart 兼跳去 cart 頁
        cart_url = (
            f"https://www.e-capcom.com/shop/cart/cart.aspx?goods={goods_id}"
            if goods_id else PRODUCT_URL
        )
        # ntfy Actions:iPhone 通知上會出兩個大 button
        #   view = 撳咗開 URL 喺 Safari
        actions = (
            f"view, 🛒 加入 Cart 去結帳, {cart_url}, clear=true;"
            f"view, 👀 睇商品詳情, {PRODUCT_URL}, clear=true"
        )
        push_ntfy(
            title=f"🎉 {PRODUCT_NAME} 有貨!",
            message=f"撳「🛒 加入 Cart 去結帳」自動 add to cart:\n{PRODUCT_URL}",
            priority=5,          # urgent — 大聲
            click=cart_url,      # 撳通知本身 = 一鍵去 cart(等於「加入 Cart」button)
            tags="rotating_light,shopping_cart",
            actions=actions,
        )

    # 更新 state (即使 status = unknown 都寫返,keep 記憶)
    if status != "unknown":
        save_state(status)
    else:
        print("[INFO] unknown status → state 保持不變")


if __name__ == "__main__":
    main()
