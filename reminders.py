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
    # ───── BLNST ─────────────────────────────────────────
    {
        "id": "blnst_reg_tonight",
        "date": "2026-07-23",
        "hour": 19,
        "title": "🎓 記得報 BLNST!",
        "message": (
            "今晚 5 分鐘搞掂:\n"
            "https://www.csbexam.gov.hk?lang=hk\n"
            "\n"
            "揀最近 slot(下星期都得),稅務大樓 37/F 30 分鐘考完,即日出證書。\n"
            "20 條 MC,答啱 10 條就 pass。免費。"
        ),
        "click": "https://www.csbexam.gov.hk?lang=hk",
        "tags": "mortar_board",
        "priority": 4,
    },
    {
        "id": "blnst_check_in_1",
        "date": "2026-07-28",
        "hour": 12,
        "title": "❓ BLNST 你報咗未?",
        "message": (
            "如果未報,趁 CRE 未黎(10-03)搞掂晒:\n"
            "https://www.csbexam.gov.hk?lang=hk"
        ),
        "click": "https://www.csbexam.gov.hk?lang=hk",
        "tags": "eyes",
        "priority": 3,
    },

    # ───── CRE 報名期 ────────────────────────────────────
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
            "💡 BLNST 已全年隨時網上考,唔洗等呢輪"
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

    # ───── CRE 考試日 ────────────────────────────────────
    {
        "id": "cre_exam_eve",
        "date": "2026-10-02",
        "hour": 21,
        "title": "😴 聽日 CRE 考試,早啲瞓!",
        "message": (
            "3 份卷:英文 / 中文 / 能力傾向,各 45 分鐘。\n"
            "記得帶:\n"
            "- 身分證\n"
            "- 准考證(考評局 email)\n"
            "- HB 鉛筆 + 擦膠\n"
            "- 睇實考場地址"
        ),
        "tags": "sleeping",
        "priority": 4,
    },
    {
        "id": "cre_exam_morning",
        "date": "2026-10-03",
        "hour": 7,
        "title": "☀️ 今日 CRE 考試日!",
        "message": (
            "食好個早餐,提早半個鐘去到。\n"
            "身分證 + 准考證 + 筆膠帶齊。加油!"
        ),
        "tags": "sunrise",
        "priority": 4,
    },

    # ───── AP II 招聘留意 ───────────────────────────────
    {
        "id": "ap2_watch_oct",
        "date": "2026-10-15",
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
        "id": "ap2_watch_nov",
        "date": "2026-11-15",
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
        "id": "ap2_watch_dec",
        "date": "2026-12-15",
        "hour": 9,
        "title": "👀 最後 check AP II 招聘",
        "message": (
            "12 月係 AP II 招聘 window 最後階段:\n"
            "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action\n"
            "\n"
            "如果呢輪 miss 咗,要等 2027 年 10 月。"
        ),
        "click": "https://csboa2.csb.gov.hk/csboa/jve/JVE_001_zh.action",
        "tags": "eyes,briefcase",
        "priority": 4,
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
