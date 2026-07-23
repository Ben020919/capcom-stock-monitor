"""
Date-based reminders — 到期就 push,唔會重複。

支援:
- 一次性(冇 repeat_days)
- 週期性(repeat_days=7 每星期,until=... 到期停)
- 動態 {days_left} template — 顯示 deadline 倒數

State 用 state.json 內 'sent_reminders' list keep track (格式 "id@YYYY-MM-DD")。
Reminder 只 push 落 REMINDER_TOPICS,唔會 spam 到 stock alert 個 Jamie01。
"""
from datetime import datetime, timezone, timedelta

HK_TZ = timezone(timedelta(hours=8))
REMINDER_TOPICS = ["TestMode"]

# ─────────────────────────────────────────────────────────────
# 到期未 send 就 push
# id 用嚟去重(recurring 會加日期後綴,例:"weekly_reg@2026-07-30")
# ─────────────────────────────────────────────────────────────
REMINDERS = [
    # ───── 每星期提報 CRE + BLNST(到 CRE 截止就停)─────
    {
        "id": "weekly_exam_reg",
        "date": "2026-07-23",
        "hour": 19,
        "repeat_days": 7,           # 每 7 日 fire 一次
        "until": "2026-08-07",      # CRE 截止日,之後停
        "deadline": "2026-08-07",   # 用嚟計 {days_left}
        "title": "📝 報名提醒:CRE(綜合招聘)+ BLNST(基本法/國安法)",
        "message": (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "① CRE 綜合招聘考試\n"
            "  📅 截止:2026-08-07 (剩 {days_left} 日)\n"
            "  🎯 考試日:2026-10-03\n"
            "  🔗 https://www.csb.gov.hk/tc_chi/recruit/cre/949.html\n"
            "  一次過 tick:英文運用/中文運用/能力傾向\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "② BLNST《基本法及香港國安法》測試\n"
            "  📅 冇 deadline,全年任揀日子\n"
            "  🎯 學位程度數碼版,稅務大樓 37/F\n"
            "  🔗 https://www.csbexam.gov.hk?lang=hk\n"
            "  30 分鐘,20 條 MC,免費,即日拎證書\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "\n"
            "兩個都報咗就當我冇 send 過,一星期再嘈你。"
        ),
        "click": "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html",
        "tags": "memo",
        "priority": 4,
    },

    # ───── CRE 截止前 2 日最後警告 ────────────────────────
    {
        "id": "cre_2026_oct_final_warn",
        "date": "2026-08-05",
        "hour": 10,
        "title": "⏰ CRE(綜合招聘考試)剩 2 日截止!",
        "message": (
            "CRE 綜合招聘考試\n"
            "📅 08-07 截止,miss 咗要等 2027 年!\n"
            "🔗 https://www.csb.gov.hk/tc_chi/recruit/cre/949.html\n"
            "\n"
            "順便:BLNST《基本法及國安法》測試如果都未報,\n"
            "🔗 https://www.csbexam.gov.hk?lang=hk (全年隨時)"
        ),
        "click": "https://www.csb.gov.hk/tc_chi/recruit/cre/949.html",
        "tags": "alarm_clock",
        "priority": 5,
    },

    # ───── AP II 招聘留意(順延一年,2027)─────────────────
    {
        "id": "ap2_watch_oct_2027",
        "date": "2027-10-15",
        "hour": 9,
        "title": "👀 開始留意 AP II 招聘公告",
        "message": (
            "AP II 通常 10-12 月開招聘。留意:\n"
            "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action\n"
            "\n"
            "search:「二級系統分析」或「Analyst/Programmer II」"
        ),
        "click": "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action",
        "tags": "eyes,briefcase",
        "priority": 3,
    },
    {
        "id": "ap2_watch_nov_2027",
        "date": "2027-11-15",
        "hour": 9,
        "title": "👀 再 check AP II 招聘公告",
        "message": (
            "如果 10 月未見到,呢個時間好可能開:\n"
            "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action"
        ),
        "click": "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action",
        "tags": "eyes,briefcase",
        "priority": 3,
    },
    {
        "id": "ap2_watch_dec_2027",
        "date": "2027-12-15",
        "hour": 9,
        "title": "👀 最後 check AP II 招聘",
        "message": (
            "12 月係 AP II 招聘 window 最後階段:\n"
            "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action\n"
            "\n"
            "如果呢輪 miss 咗,要等 2028 年 10 月。"
        ),
        "click": "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action",
        "tags": "eyes,briefcase",
        "priority": 4,
    },
]


def _fire_times(r: dict, now_hk: datetime):
    """Yield all datetime instances when this reminder should have fired,
    up to (and including) now_hk."""
    start = datetime.fromisoformat(r["date"]).replace(
        hour=r.get("hour", 9), tzinfo=HK_TZ
    )
    if now_hk < start:
        return

    until = None
    if r.get("until"):
        until = datetime.fromisoformat(r["until"]).replace(
            hour=23, minute=59, tzinfo=HK_TZ
        )

    repeat = r.get("repeat_days", 0)
    current = start
    while current <= now_hk:
        if until and current > until:
            break
        yield current
        if not repeat:
            break
        current += timedelta(days=repeat)


def _render_message(r: dict, fire_time: datetime) -> str:
    """Fill dynamic placeholders like {days_left}."""
    msg = r["message"]
    if "{days_left}" in msg and r.get("deadline"):
        dl = datetime.fromisoformat(r["deadline"]).replace(tzinfo=HK_TZ)
        days_left = max(0, (dl.date() - fire_time.date()).days)
        msg = msg.replace("{days_left}", str(days_left))
    return msg


def check_reminders(state: dict, push_fn):
    """跑一次:到期未 send 嘅 reminder 全部 push,成功就 mark。"""
    now_hk = datetime.now(HK_TZ)
    sent = set(state.get("sent_reminders", []))

    for r in REMINDERS:
        for ft in _fire_times(r, now_hk):
            fire_id = f"{r['id']}@{ft:%Y-%m-%d}"
            if fire_id in sent:
                continue

            message = _render_message(r, ft)
            print(f"→ Reminder due: {fire_id}")
            ok = push_fn(
                title=r["title"],
                message=message,
                priority=r.get("priority", 5),
                click=r.get("click"),
                tags=r.get("tags"),
                topics=REMINDER_TOPICS,
            )
            if ok:
                sent.add(fire_id)

    state["sent_reminders"] = sorted(sent)
