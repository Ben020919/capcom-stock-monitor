"""
Daily heartbeat — 每日 confirm monitor 仲活住。
低 priority push,唔會嘈醒你,只係一個 status update。
"""
import urllib.request
from check_stock import (
    fetch_html,
    detect_stock,
    PRODUCT_URL,
    PRODUCT_NAME,
    NTFY_TOPIC,
)


def push_low_priority(title: str, message: str):
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC 未設定,skip heartbeat")
        return False
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title.encode("utf-8"),
            "Priority": "2",  # low = silent,唔震唔響,只 badge count +1
            "Tags": "heart",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[ntfy] heartbeat sent OK ({r.status})")
        return True
    except Exception as e:
        print(f"[ntfy] fail: {e}")
        return False


def main():
    try:
        html = fetch_html(PRODUCT_URL)
        status = detect_stock(html)
    except Exception as e:
        status = f"error({e})"
    print(f"Heartbeat status: {status}")

    status_display = {
        "out_of_stock": "🔴 缺貨",
        "in_stock": "🟢 有貨",
        "unknown": "⚪ 未知 (可能網站 layout 變咗)",
    }.get(status, f"⚠️ {status}")

    push_low_priority(
        title="💓 Capcom Monitor 運行中",
        message=(
            f"監察緊: {PRODUCT_NAME}\n"
            f"現況: {status_display}\n"
            f"下次 heartbeat: 24 小時後"
        ),
    )


if __name__ == "__main__":
    main()
