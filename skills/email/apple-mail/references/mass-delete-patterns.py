#!/usr/bin/env python3
"""
Mass-delete spam from Mail.app inbox.

Strategy:
  1. SQLite → выгрузка всех тем (быстро, без таймаутов)
  2. Python → фильтрация по паттернам
  3. osascript → обратный проход, группы по ~30 паттернов

Ограничения AppleScript, обойдённые здесь:
  - `messages of inbox` медленный на 1000+ → используем SQLite для анализа
  - Удаление в прямом цикле сдвигает индексы → обратный проход
  - `message id X of inbox` не работает с отрицательными ID → итерация по всем
  - Список >30-40 паттернов → syntax error → разбивка на группы
  - SQLite LIKE не работает с Unicode/кириллицей/эмодзи → фильтр в Python
"""

import sqlite3
import subprocess
import sys

DB = "/Users/jenyanovak/Library/Mail/V10/MailData/Envelope Index"
MAILBOX_ID = 48  # iCloud inbox — узнать через mailboxes table

# ─── ШАГ 1: Анализ через SQLite ───────────────────────────────────

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute(f"""
    SELECT m.ROWID, m.message_id, sj.subject
    FROM messages m
    JOIN subjects sj ON m.subject = sj.ROWID
    WHERE m.mailbox = {MAILBOX_ID} AND m.deleted = 0
""")
rows = cur.fetchall()
conn.close()

print(f"Всего писем в inbox: {len(rows)}")

# ─── ШАГ 2: Паттерны для удаления ────────────────────────────────
# Каждый паттерн — подстрока темы письма (регистрозависимо для osascript)
# Группируем по ~30 штук из-за лимита AppleScript

PATTERN_GROUPS = [
    # Группа 1: Русский маркетинг
    ["Чукреева", "Слёрм", "Слерм", "Лето перемен", "астрологи", "Мамасит",
     "вебинар", "интенсив", "распродаж", "скидк", "фрибет",
     "бесплатн", "ваш вайб", "хороший вкус", "вашем духе",
     "ваш стиль", "статистик", "Итоги недели", "Воркшоп",
     "Кишечник", "Питание по звездам", "Любовь рядом",
     "Фриланс Удаленная работа", "Заработок на создании",
     "Оцените качество", "МФЦ", "Соберите идеальный",
     "Регистрируйтесь", "Регистрация на", "Напоминание о мероприятии"],

    # Группа 2: GitHub + Apple + коды
    ["[GitHub]", "Квитанция от Apple", "Данные Вашего Аккаунта",
     "проверочный код", "验证码", "verification code",
     "Verify your email", "Please confirm your email",
     "Your OpenAI code", "Your ChatGPT code", "Your Activation Code",
     "Brave Search API login", "Login security code",
     "Sign in to Cursor", "Personal Microsoft account",
     "Enabling two-factor", "Udemy Login", "Xiaomi Account",
     "阿里巴巴", "火山引擎", "中国签证",
     "Test", "Notification", "update for you",
     "if you are doing at least 50k", "Explore net-30",
     "sanava.ai", "NGstyle", "Order Update", "Your Order"],

    # Группа 3: Realty + долги + английский маркетинг
    ["Resedential Lease", "Fenbrook Dr", "Ищу сделки sub2",
     "PIONEER ST", "SEGUIN, TX", "foreclosure", "probate leads",
     "real probate", "Still Actively Looking", "Hotel Contract",
     "net-30+ vendors", "vendors picked for you",
     "IMPORTANTE - DEUDA", "payment to Clavion",
     "Проблема с оплатой", "your account specials", "login asap",
     "You're invited", "You are about to reach",
     "We're Updating Our Privacy", "Updates to our sub-processors",
     "Updates to Link", "We're updating our Terms",
     "Renewal Reminder", "They've been lying", "TONIGHT",
     "System design", "See what the Aspire", "RipX DAW", "Retell AI"],

    # Группа 4: leadgenerationninja + daily.dev + social
    ["leadgenerationninja", "daily.dev",
     "novak.jenya, see", "Jeka, your personal update",
     "Reminder: @Ng", "Zhenia, эти идеи", "Zhenia, это похоже",
     "Zhenia, у вас", "Это похоже на ваш", "У вас хороший вкус",
     "MN -Resedential Lease", "рассып", "День сист",
     "привет", "Служба поддержки", "новое сообщение",
     "Уведомление об изменении статуса",
     "Вам понравятся эти пины", "Вам доступны фрибеты",
     "Проверочный код для кинопаба", "Обновите паспортные",
     "Duo ведь не молодеет", "Anchors Aweigh",
     "Send Grid Ready", "Reply From GHL",
     "Vremya vyleta", "Trip.com booking", "Train itinerary",
     "Your eSIM booking", "Your report is ready"],

    # Группа 5: Emoji-спам + travel spam
    ["🍩", "🥺", "🚨", "🚀", "🔥", "🔇", "📆", "💸", "💬",
     "💪", "💥", "🎉", "✅", "⚓", "👋", "🏁", "🍀",
     "‎Одно новое", "?? ПОКУПКА ДОМА",
     "Куда сбежать от осени", "Где встретить май и июнь",
     "Где охладиться летом", "Где начинается туристический сезон",
     "Как спланировать лето", "Планируем ваше лето",
     "Куда путешественникам можно без визы",
     "Где встретить Новый год без снега",
     "новогоднее настроение", "нарядите виртуальную ёлку",
     "Как не наломать дров", "транзит Юпитера",
     "новых Гарри, Гермиону и Рона"],

    # Группа 6: Английский AI/маркетинг
    ["Your own Ad Spy", "Stock Analysis Automation",
     "SEO Audit Automation", "PDF Invoice Automation",
     "My 2026 AI Predictions", "Incoming Call Automation",
     "Full Build of an AI RAG", "Copy the best YouTube hooks",
     "Business Proposal Automation",
     "Access These 11 AI Voice Templates",
     "AI Phone Appointment Setter", "AI Phone Agent for Auto Repair",
     "AI Phone Agent for Accounting", "AI Appointment Scheduler",
     "DeepSeek For Businesses", "Waiting for signal at Coachella",
     "Welcome! Let's finish setting up",
     "Activate Your Account", "Guaranteed CRM",
     "Alert: recent primary activity",
     "Attention required: verify",
     "Action Required: Sign Your Documents",
     "Booking Confirmation", "Audio from Diana",
     "Environment Tags", "China Mobile Hong Kong - Login alert",
     "From Vitaly -Zillow needed", "Event Replay",
     "Tomorrow's Treat", "Co-Living Secrets", "Co-Living Masterclass"],

    # Группа 7: Realty адреса + остатки
    ["Linam St SE", "Ormond St SE", "Stone Rd SW",
     "Sweep up the savings", "ICON Cooler",
     "Black Friday is coming", "Ep:158 Dominic McFadin",
     "Automate the Boring Parts",
     "Попробуйте нового AI SMMщика",
     "Генерируем ответы на комментарии",
     "Готовим вопросы для подкаста",
     "Тук-тук... это", "Угадай кто! Это",
     "5 установок, которые держат", "3 набора декабря",
     "Почему кожа устает",
     "Хотите чувствовать себя на 30 лет моложе",
     "Фруктоза: Сладкий убийца", "Формально в паре",
     "Флиппинг в США", "Ушло 7 кг",
     "Трансформация за 21 день", "Топ-5 ошибок",
     "Тест: какой вы", "Терапия для души",
     "Твой путь к успеху", "Секреты стройности",
     "Секреты молодости", "Марафон желаний"],
]

# ─── ШАГ 3: Удаление через osascript ──────────────────────────────

def make_script(patterns):
    """Сгенерировать AppleScript для одной группы паттернов (~30 шт)."""
    items = "{" + ", ".join(f'"{p}"' for p in patterns) + "}"
    return f'''
set patternList to {items}

tell application "Mail"
    set msgs to messages of inbox
    set msgCount to count of msgs
    set totalDeleted to 0

    repeat with i from msgCount to 1 by -1
        set msg to item i of msgs
        set msgSubject to subject of msg
        set shouldDelete to false

        if msgSubject is "" then
            set shouldDelete to true
        else
            repeat with p in patternList
                if msgSubject contains p then
                    set shouldDelete to true
                    exit repeat
                end if
            end repeat
        end if

        if shouldDelete then
            delete msg
            set totalDeleted to totalDeleted + 1
        end if
    end repeat

    return totalDeleted
end tell
'''

total_deleted = 0
for i, group in enumerate(PATTERN_GROUPS):
    print(f"Проход {i+1}/{len(PATTERN_GROUPS)}...", end=" ", flush=True)
    script = make_script(group)

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=600
    )

    if result.returncode == 0:
        count = result.stdout.strip()
        print(f"удалено: {count}")
        if count.isdigit():
            total_deleted += int(count)
    else:
        print(f"ошибка: {result.stderr.strip()[:80]}")

print(f"\nИтого удалено: {total_deleted}")

# ─── ШАГ 4: Проверка остатка ─────────────────────────────────────

conn2 = sqlite3.connect(DB)
remaining = conn2.execute(
    f"SELECT COUNT(*) FROM messages WHERE mailbox = {MAILBOX_ID} AND deleted = 0"
).fetchone()[0]
conn2.close()

print(f"Осталось: {remaining} писем")
