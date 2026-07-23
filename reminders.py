"""
Date-based reminders — 到期就 push,唔會重複。
State 用 state.json 內 'sent_reminders' list keep track。

新增 reminder 只需要 append 落 REMINDERS list。
Reminder 只 push 落 REMINDER_TOPICS (預設 TestMode),
唔會 spam 到 stock alert 個 Jamie01 topic。
"""
from datetime import datetime, timezone, timedelta

HK_TZ = timezone(timedelta(hours=8))

# Reminders 專用 topic list — 唔跟 stock alert 嘅 NTFY_TOPICS
REMINDER_TOPICS = ["TestMode"]

# ─────────────────────────────────────────────────────────────
# 到期未 send 就 push。id 用嚟去重,永久記住 (state.sent_reminders)
# ─────────────────────────────────────────────────────────────
REMINDERS = [
    {
        "id": "cre_2026_oct_open",
        "date": "2026-07-25",
        "hour": 9,
        "title": "🎯 CRE 綜合招聘考試今日開始報名!",
        "message": (
            "報名期:07-25 至 08-07 (14日 window)\n"
            "考試日:2026-10-03\n"
            "\n"
            "報名網址:\n"
            "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html\n"
            "\n"
            "同一次報名可以選:\n"
            "- 英文運用(拎二級)\n"
            "- 中文運用(拎一級)\n"
            "- 能力傾向測試(拎及格)\n"
            "\n"
            "💡 BLNST(基本法+國安法)學位程度已全年隨時網上考,唔洗等呢輪"
        ),
        "click": "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html",
        "tags": "memo,mortar_board",
        "priority": 4,
    },
    {
        "id": "cre_2026_oct_final_warn",
        "date": "2026-08-05",
        "hour": 10,
        "title": "⏰ CRE 剩 2 日截止(08-07)!",
        "message": (
            "如果未報 CRE(下次要等 2027 年),今日或聽日搞掂:\n"
            "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html"
        ),
        "click": "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html",
        "tags": "alarm_clock",
        "priority": 5,
    },
]


def check_reminders(state: dict, push_fn):
    """跑一次:到期未 send 嘅 reminder 全部 push,成功就 mark。"""
    now_hk = datetime.now(HK_TZ)
    sent = set(state.get("sent_reminders", []))

    for r in REMINDERS:
        if r["id"] in sent:
            continue
        due = datetime.fromisoformat(r["date"]).replace(
            hour=r.get("hour", 9), tzinfo=HK_TZ
        )
        if now_hk < due:
            continue

        print(f"→ Reminder due: {r['id']} → topics={REMINDER_TOPICS}")
        ok = push_fn(
            title=r["title"],
            message=r["message"],
            priority=r.get("priority", 5),
            click=r.get("click"),
            tags=r.get("tags"),
            topics=REMINDER_TOPICS,
        )
        if ok:
            sent.add(r["id"])

    state["sent_reminders"] = sorted(sent)
