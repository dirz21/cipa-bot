import os, json, time, secrets, threading, urllib.request
import telebot
from telebot import types
from datetime import datetime
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "T8846832655:AAGu72WzNfWDYZYaQXNcvpFq2ENDLPLNS1s")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "6847073444"))
FB        = os.environ.get("FB", "https://bot-key-af648-default-rtdb.asia-southeast1.firebasedatabase.app")
COOLDOWN  = 2 * 86400

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "CIPA ONLY VIP - bot alive"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def fg(p):
    try:
        with urllib.request.urlopen(f"{FB}/{p}.json", timeout=10) as r:
            return json.loads(r.read().decode())
    except: return None

def fp(p, d):
    try:
        r = urllib.request.Request(f"{FB}/{p}.json",
            data=json.dumps(d).encode(), method="PUT",
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(r, timeout=10); return True
    except: return False

def fa(p, d):
    try:
        r = urllib.request.Request(f"{FB}/{p}.json",
            data=json.dumps(d).encode(), method="PATCH",
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(r, timeout=10); return True
    except: return False

def fd(p):
    try:
        r = urllib.request.Request(f"{FB}/{p}.json", method="DELETE")
        urllib.request.urlopen(r, timeout=10); return True
    except: return False

def gk(): return f"CIPA-{secrets.token_hex(3).upper()}"

def dr(s):
    s = s.lower().strip()
    try:
        if s.endswith("d"): return int(s[:-1]) * 86400
        if s.endswith("w"): return int(s[:-1]) * 7 * 86400
        if s.endswith("m"): return int(s[:-1]) * 30 * 86400
    except: pass
    return None

def fw(s):
    h = s // 3600; m = (s % 3600) // 60
    return f"{h//24}h {h%24}j" if h >= 24 else f"{h}j {m}m"

def mk(sec):
    k = gk(); now = int(time.time() * 1000)
    return k if fp(f"keys/{k}", {"key": k, "expires": now + sec*1000,
        "revoked": False, "hwid": None, "created": now}) else None

def menu(uid=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    if uid == ADMIN_ID:
        kb.add(
            types.InlineKeyboardButton("🔑 1 Hari", callback_data="gd"),
            types.InlineKeyboardButton("🔑 1 Minggu", callback_data="gw"),
            types.InlineKeyboardButton("🔑 1 Bulan", callback_data="gm"),
            types.InlineKeyboardButton("📋 List Key", callback_data="list"))
        kb.add(types.InlineKeyboardButton("🗑 Hapus Key", callback_data="dh"))
        kb.add(types.InlineKeyboardButton("❌ Tutup", callback_data="close"))
    else:
        kb.add(types.InlineKeyboardButton("💎 Ambil Key Gratis (1 Hari) 💎", callback_data="gd"))
    return kb

def back():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("◀️ Kembali", callback_data="menu"))
    return kb

@bot.message_handler(commands=["start"])
def s(m):
    uid = m.from_user.id
    a = m.text.split(maxsplit=1)
    if len(a) > 1: return act(m, a[1])
    if uid == ADMIN_ID:
        bot.send_message(m.chat.id,
            "💎 *PANEL ADMIN — CIPA ONLY VIP* 💎\n\nPilih menu di bawah:",
            parse_mode="Markdown", reply_markup=menu(uid))
    else:
        bot.send_message(m.chat.id,
            "💎 *CIPA ONLY VIP — KEY BOT* 💎\n\nTekan tombol di bawah untuk ambil key gratis 1 hari:",
            parse_mode="Markdown", reply_markup=menu(uid))

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    d = c.data; uid = c.from_user.id
    if d == "close":
        bot.edit_message_text("✅ Menu ditutup.", chat_id=c.message.chat.id,
            message_id=c.message.message_id)
        return bot.answer_callback_query(c.id)
    if d == "menu":
        if uid == ADMIN_ID:
            bot.edit_message_text("💎 *PANEL ADMIN — CIPA ONLY VIP* 💎\n\nPilih menu di bawah:",
                chat_id=c.message.chat.id, message_id=c.message.message_id,
                parse_mode="Markdown", reply_markup=menu(uid))
        else:
            bot.edit_message_text("💎 *CIPA ONLY VIP* 💎\n\nTekan tombol untuk ambil key:",
                chat_id=c.message.chat.id, message_id=c.message.message_id,
                parse_mode="Markdown", reply_markup=menu(uid))
        return bot.answer_callback_query(c.id)
    if d == "list":
        if uid != ADMIN_ID:
            return bot.answer_callback_query(c.id, "Akses ditolak.", show_alert=True)
        ks = fg("keys") or {}
        if not ks: return bot.answer_callback_query(c.id, "📂 Database kosong.", show_alert=True)
        now = int(time.time()*1000); out = []
        for k, v in sorted(ks.items(), key=lambda x: -(x[1].get("created",0) or 0))[:40]:
            e = v.get("expires",0) or 0
            if v.get("revoked"): out.append(f"🔴 `{k}` — revoked")
            elif e>0 and now>e: out.append(f"🔴 `{k}` — expired")
            elif v.get("hwid"):
                out.append(f"🟡 `{k}` — {int((e-now)//86400000)}d — `{(v.get('hwid') or '-')[:12]}`")
            else: out.append(f"🟢 `{k}` — siap")
        bot.edit_message_text("📋 *Database Key:*\n\n" + "\n".join(out),
            chat_id=c.message.chat.id, message_id=c.message.message_id,
            parse_mode="Markdown", reply_markup=back())
        return bot.answer_callback_query(c.id)
    if d == "dh":
        if uid != ADMIN_ID:
            return bot.answer_callback_query(c.id, "Akses ditolak.", show_alert=True)
        bot.edit_message_text("🗑 *HAPUS KEY:* `/delete KODE`\n\n♻️ *RESET KEY:* `/resetkey KODE`",
            chat_id=c.message.chat.id, message_id=c.message.message_id,
            parse_mode="Markdown", reply_markup=back())
        return bot.answer_callback_query(c.id)
    if d.startswith("g"):
        if uid != ADMIN_ID and d != "gd":
            return bot.answer_callback_query(c.id, "Hanya 1 hari untuk user.", show_alert=True)
        secs = {"gd":86400, "gw":604800, "gm":2592000}.get(d)
        if not secs: return bot.answer_callback_query(c.id, "?")
        if uid != ADMIN_ID:
            last = fg(f"users/{uid}") or 0
            if isinstance(last, dict): last = last.get("last", 0)
            el = (int(time.time()*1000) - (last or 0)) // 1000
            if el < COOLDOWN:
                return bot.answer_callback_query(c.id,
                    f"⏳ Tunggu {fw(COOLDOWN-el)} lagi.", show_alert=True)
        k = mk(secs)
        if not k: return bot.answer_callback_query(c.id, "❌ Gagal.", show_alert=True)
        if uid != ADMIN_ID: fp(f"users/{uid}", {"last": int(time.time()*1000)})
        lbl = {"gd":"1 Hari","gw":"1 Minggu","gm":"1 Bulan"}[d]
        if uid == ADMIN_ID:
            bot.answer_callback_query(c.id, f"✅ Key: {k}", show_alert=True)
            bot.send_message(c.message.chat.id,
                f"💎 *Key Baru Dibuat* 💎\n\n🔑 Key: `{k}`\n⏱ Durasi: {lbl}\n📌 Status: Siap Digunakan",
                parse_mode="Markdown", reply_markup=menu(ADMIN_ID))
        else:
            bot.answer_callback_query(c.id, f"✅ Key kamu: {k}", show_alert=True)
            bot.send_message(c.message.chat.id,
                f"💎 *Key Gratis Kamu* 💎\n\n"
                f"🔑 Key: `{k}`\n⏱ Durasi: 1 Hari\n\n"
                f"Kirim key ini ke bot untuk aktivasi.\n\n"
                f"⏳ Bisa ambil key lagi dalam 2 hari.",
                parse_mode="Markdown", reply_markup=menu(uid))
            try:
                bot.send_message(ADMIN_ID,
                    f"💎 *User ambil key gratis* 💎\n\nTG ID: `{uid}`\nNama: {c.from_user.first_name}\nKey: `{k}`",
                    parse_mode="Markdown")
            except: pass
        return
    if d.startswith("u_"):
        k = d[2:]
        bot.answer_callback_query(c.id, "Kirim key ke chat untuk aktivasi.")
        bot.send_message(c.message.chat.id, f"Kirim: `{k}`", parse_mode="Markdown")
        return
    bot.answer_callback_query(c.id)

@bot.message_handler(commands=["addkey"])
def ak(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2: return bot.reply_to(m, "Format: `/addkey 1d` / `1w` / `1m`", parse_mode="Markdown")
    secs = dr(a[1])
    if not secs: return bot.reply_to(m, "Durasi: 1d / 1w / 1m")
    k = mk(secs)
    if k: bot.reply_to(m, f"💎 *Key Baru* 💎\n\n🔑 `{k}`", parse_mode="Markdown", reply_markup=back())
    else: bot.reply_to(m, "❌ Gagal.")

@bot.message_handler(commands=["list"])
def lk(m):
    if m.from_user.id != ADMIN_ID: return
    ks = fg("keys") or {}
    if not ks: return bot.reply_to(m, "📂 Kosong.")
    now = int(time.time()*1000); out = []
    for k, v in sorted(ks.items(), key=lambda x: -(x[1].get("created",0) or 0))[:30]:
        e = v.get("expires",0) or 0
        if v.get("revoked"): out.append(f"🔴 `{k}`")
        elif e>0 and now>e: out.append(f"🔴 `{k}`")
        elif v.get("hwid"): out.append(f"🟡 `{k}` — {int((e-now)//86400000)}d")
        else: out.append(f"🟢 `{k}`")
    bot.reply_to(m, "💎 *Key Database* 💎\n\n" + "\n".join(out), parse_mode="Markdown")

@bot.message_handler(commands=["delete"])
def dk(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2: return bot.reply_to(m, "Format: `/delete KEY`", parse_mode="Markdown")
    k = a[1].strip().upper()
    if fg(f"keys/{k}"):
        fd(f"keys/{k}"); bot.reply_to(m, f"🗑 Hapus `{k}`", parse_mode="Markdown")
    else: bot.reply_to(m, "❌ Key nggak ada.")

@bot.message_handler(commands=["resetkey"])
def rk(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2: return bot.reply_to(m, "Format: `/resetkey KEY`", parse_mode="Markdown")
    k = a[1].strip().upper()
    if not fg(f"keys/{k}"): return bot.reply_to(m, "❌ Nggak ada.")
    fa(f"keys/{k}", {"hwid": None, "revoked": False})
    bot.reply_to(m, f"♻️ `{k}` di-reset.", parse_mode="Markdown")

def act(m, payload):
    if "_" in payload: k, dev = payload.split("_", 1)
    else: k, dev = payload, str(m.from_user.id)
    k = k.strip().upper(); dev = dev.strip()[:32]
    r = fg(f"keys/{k}")
    if not r: return bot.reply_to(m, "❌ Key tidak valid.")
    now = int(time.time()*1000)
    if r.get("revoked"): return bot.reply_to(m, "❌ Key dicabut.")
    e = r.get("expires",0) or 0
    if e>0 and now>e: return bot.reply_to(m, "❌ Key kadaluarsa.")
    if r.get("hwid") and r["hwid"] != dev:
        return bot.reply_to(m, "⚠️ Key terikat device lain.")
    fa(f"keys/{k}", {"hwid": dev})
    expd = datetime.fromtimestamp(e/1000).strftime("%d/%m/%Y") if e else "∞"
    bot.reply_to(m, f"💎 *Berhasil Diaktifkan* 💎\n\n🔑 `{k}`\n📱 `{dev}`\n⏳ {expd}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def tx(m):
    t = m.text.strip()
    if not t or t.startswith("/"): return
    if m.from_user.id == ADMIN_ID: return bot.reply_to(m, "Pakai /start.")
    act(m, t.upper())

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("[CIPA] bot running...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30,
                                 none_stop=True, interval=0.3)
        except Exception as e:
            print(f"[retry] {e}")
            time.sleep(5)
