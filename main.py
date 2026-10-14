import telebot, json, os, time, secrets, threading
from telebot import types
from datetime import datetime
from flask import Flask, request

BOT_TOKEN = "8674370589:AAECouJNY7HFF9EPyKjOvqNFlPRcgunsL9w"
ADMIN_ID  = 6847073444
DB = "/tmp/cipa_keys.json"
COOLDOWN = 2 * 86400

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "CIPA ONLY VIP - bot alive"

@app.route("/validate")
def validate():
    key = request.args.get("key", "").strip().upper()
    hwid = request.args.get("hwid", "").strip()[:32]
    if not key or not hwid:
        return {"valid": False, "error": "missing_params"}, 400
    d = load()
    if key not in d["keys"]:
        return {"valid": False, "error": "not_found"}
    r = d["keys"][key]
    now = int(time.time())
    if r.get("used"):
        exp = r.get("expired_at") or 0
        if now > exp:
            return {"valid": False, "error": "expired"}
        if r.get("device_id") and r["device_id"] != hwid:
            return {"valid": False, "error": "hwid_mismatch"}
        return {"valid": True, "expires": exp}
    exp = now + r["duration"]
    r["used"] = True
    r["expired_at"] = exp
    r["device_id"] = hwid
    save(d)
    return {"valid": True, "expires": exp, "bound": True}

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def load():
    if os.path.exists(DB):
        try: return json.load(open(DB))
        except: pass
    return {"keys": {}, "users": {}}

def save(d): json.dump(d, open(DB, "w"), indent=2)
def gen(): return f"CIPA-{secrets.token_hex(3).upper()}"

def dur(s):
    s = s.lower().strip()
    try:
        if s.endswith("d"): return int(s[:-1]) * 86400
        if s.endswith("w"): return int(s[:-1]) * 7 * 86400
        if s.endswith("m"): return int(s[:-1]) * 30 * 86400
    except: pass
    return None

def fmt_wait(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    if h >= 24:
        return f"{h//24}h {h%24}j"
    return f"{h}j {m}m"

def main_menu(uid=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    if uid == ADMIN_ID:
        kb.add(
            types.InlineKeyboardButton("🔑 1 Hari",  callback_data="gen_d"),
            types.InlineKeyboardButton("🔑 1 Minggu", callback_data="gen_w"),
            types.InlineKeyboardButton("🔑 1 Bulan", callback_data="gen_m"),
            types.InlineKeyboardButton("📋 List Key", callback_data="list")
        )
        kb.add(types.InlineKeyboardButton("🗑 Hapus Key", callback_data="del_help"))
        kb.add(types.InlineKeyboardButton("❌ Tutup", callback_data="close"))
    else:
        kb.add(types.InlineKeyboardButton("💎 Ambil Key Gratis (1 Hari) 💎", callback_data="gen_d"))
    return kb

def back_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("◀️ Kembali", callback_data="menu"))
    return kb

@bot.message_handler(commands=["start"])
def c_start(m):
    uid = m.from_user.id
    args = m.text.split(maxsplit=1)
    if len(args) > 1:
        return activate_key(m, args[1])
    if uid == ADMIN_ID:
        bot.send_message(m.chat.id,
            "💎 *PANEL ADMIN — CIPA ONLY VIP* 💎\n\nPilih menu di bawah:",
            parse_mode="Markdown", reply_markup=main_menu(uid))
    else:
        bot.send_message(m.chat.id,
            "💎 *CIPA ONLY VIP — KEY BOT* 💎\n\nTekan tombol di bawah untuk ambil key gratis 1 hari:",
            parse_mode="Markdown", reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c: True)
def on_cb(c):
    data = c.data
    uid = c.from_user.id

    if data == "close":
        bot.edit_message_text("✅ Menu ditutup.",
            chat_id=c.message.chat.id, message_id=c.message.message_id)
        return bot.answer_callback_query(c.id)

    if data == "menu":
        title = ("💎 *PANEL ADMIN — CIPA ONLY VIP* 💎\n\nPilih menu di bawah:"
                 if uid == ADMIN_ID
                 else "💎 *CIPA ONLY VIP — KEY BOT* 💎\n\nTekan tombol untuk ambil key:")
        bot.edit_message_text(title,
            chat_id=c.message.chat.id, message_id=c.message.message_id,
            parse_mode="Markdown", reply_markup=main_menu(uid))
        return bot.answer_callback_query(c.id)

    if data == "list":
        if uid != ADMIN_ID:
            return bot.answer_callback_query(c.id, "Akses ditolak.", show_alert=True)
        d = load()
        if not d["keys"]:
            return bot.answer_callback_query(c.id, "Database kosong.", show_alert=True)
        now = int(time.time()); out = []
        for k, v in sorted(d["keys"].items(), key=lambda x: -x[1]["created"])[:40]:
            if not v["used"]:
                out.append(f"🟢 `{k}` — siap — {v['duration']//86400}d")
            else:
                exp = v["expired_at"] or 0
                if now > exp:
                    out.append(f"🔴 `{k}` — expired")
                else:
                    sisa = int((exp - now) // 86400)
                    dev = (v.get("device_id") or "-")[:12]
                    out.append(f"🟡 `{k}` — {sisa}d — `{dev}`")
        bot.edit_message_text("📋 *Database Key:*\n\n" + "\n".join(out),
            chat_id=c.message.chat.id, message_id=c.message.message_id,
            parse_mode="Markdown", reply_markup=back_menu())
        return bot.answer_callback_query(c.id)

    if data == "del_help":
        if uid != ADMIN_ID:
            return bot.answer_callback_query(c.id, "Akses ditolak.", show_alert=True)
        bot.edit_message_text(
            "🗑 *HAPUS KEY*\n\n`/delete KODE_KEY`\n\n"
            "♻️ *RESET KEY* (bisa dipakai ulang)\n`/resetkey KODE_KEY`",
            chat_id=c.message.chat.id, message_id=c.message.message_id,
            parse_mode="Markdown", reply_markup=back_menu())
        return bot.answer_callback_query(c.id)

    if data.startswith("gen_"):
        if uid != ADMIN_ID and data != "gen_d":
            return bot.answer_callback_query(c.id,
                "Hanya tersedia 1 hari untuk user.", show_alert=True)
        dur_secs = {"d": 86400, "w": 604800, "m": 2592000}.get(data[-1])
        if not dur_secs:
            return bot.answer_callback_query(c.id, "Durasi tidak dikenal.")
        now = int(time.time())
        db = load()

        if uid != ADMIN_ID:
            users = db.setdefault("users", {})
            last = users.get(str(uid), 0)
            if now - last < COOLDOWN:
                sisa = COOLDOWN - (now - last)
                return bot.answer_callback_query(c.id,
                    f"⏳ Tunggu {fmt_wait(sisa)} lagi.", show_alert=True)

        key = gen()
        db["keys"][key] = {"duration": dur_secs, "created": now, "used": False,
                           "expired_at": None, "device_id": None}
        if uid != ADMIN_ID:
            db.setdefault("users", {})[str(uid)] = now
        save(db)

        lbl = {"d": "1 Hari", "w": "1 Minggu", "m": "1 Bulan"}[data[-1]]

        if uid == ADMIN_ID:
            bot.answer_callback_query(c.id, f"✅ Key: {key}", show_alert=True)
            bot.send_message(c.message.chat.id,
                f"💎 *Key Baru Dibuat* 💎\n\n"
                f"🔑 Key: `{key}`\n⏱ Durasi: {lbl}\n📌 Status: Siap Digunakan",
                parse_mode="Markdown", reply_markup=back_menu())
        else:
            bot.answer_callback_query(c.id, f"✅ Key kamu: {key}", show_alert=True)
            bot.send_message(c.message.chat.id,
                f"💎 *Key Gratis Kamu* 💎\n\n"
                f"🔑 Key: `{key}`\n⏱ Durasi: 1 Hari\n\n"
                f"Kirim key ini ke bot untuk aktivasi, atau tap tombol di bawah.\n\n"
                f"⏳ Bisa ambil key lagi dalam 2 hari.",
                parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("⚡ Aktivasi sekarang ⚡", callback_data=f"use_{key}")))
            try:
                bot.send_message(ADMIN_ID,
                    f"💎 *User ambil key gratis* 💎\n\n"
                    f"TG ID: `{uid}`\nNama: {c.from_user.first_name}\n"
                    f"Key: `{key}`",
                    parse_mode="Markdown")
            except: pass
        return

    if data.startswith("use_"):
        key = data.replace("use_", "")
        bot.answer_callback_query(c.id, "Kirim key ke chat untuk aktivasi.")
        bot.send_message(c.message.chat.id, f"Kirim: `{key}`", parse_mode="Markdown")
        return

    bot.answer_callback_query(c.id)

@bot.message_handler(commands=["addkey"])
def c_add(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2:
        return bot.reply_to(m, "Pakai /start untuk menu tombol.")
    secs = dur(a[1])
    if not secs: return bot.reply_to(m, "Durasi: 1d / 1w / 1m")
    k = gen(); now = int(time.time())
    d = load()
    d["keys"][k] = {"duration": secs, "created": now, "used": False,
                    "expired_at": None, "device_id": None}
    save(d)
    bot.reply_to(m, f"💎 *Key Baru* 💎\n\n🔑 `{k}`",
                 parse_mode="Markdown", reply_markup=back_menu())

@bot.message_handler(commands=["list"])
def c_list(m):
    if m.from_user.id != ADMIN_ID: return
    d = load()
    if not d["keys"]: return bot.reply_to(m, "📂 Kosong.")
    now = int(time.time()); out = []
    for k, v in sorted(d["keys"].items(), key=lambda x: -x[1]["created"])[:30]:
        if not v["used"]: out.append(f"🟢 `{k}`")
        else:
            exp = v["expired_at"] or 0
            if now > exp: out.append(f"🔴 `{k}`")
            else: out.append(f"🟡 `{k}` — {int((exp-now)//86400)}d")
    bot.reply_to(m, "💎 *Key Database* 💎\n\n" + "\n".join(out), parse_mode="Markdown")

@bot.message_handler(commands=["delete"])
def c_del(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2: return bot.reply_to(m, "Format: /delete KEY")
    d = load(); k = a[1].strip().upper()
    if k in d["keys"]:
        del d["keys"][k]; save(d)
        bot.reply_to(m, f"🗑 Hapus `{k}`", parse_mode="Markdown")
    else:
        bot.reply_to(m, "❌ Key nggak ada.")

@bot.message_handler(commands=["resetkey"])
def c_resetkey(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2:
        return bot.reply_to(m, "Format: `/resetkey KODE_KEY`\n\n"
                               "Reset key supaya bisa dipakai ulang di device lain.",
                         parse_mode="Markdown")
    d = load(); k = a[1].strip().upper()
    if k not in d["keys"]:
        return bot.reply_to(m, f"❌ Key `{k}` nggak ada.", parse_mode="Markdown")
    r = d["keys"][k]
    r["used"] = False
    r["expired_at"] = None
    r["device_id"] = None
    save(d)
    bot.reply_to(m,
        f"♻️ *Key di-reset* ♻️\n\n"
        f"🔑 `{k}`\n"
        f"📌 Status: Siap dipakai ulang\n"
        f"⏱ Durasi tetap: {r['duration']//86400} hari\n"
        f"📱 HWID: kosong (bisa bind ke device baru)",
        parse_mode="Markdown")

@bot.message_handler(commands=["reset"])
def c_reset(m):
    if m.from_user.id != ADMIN_ID: return
    a = m.text.split(maxsplit=1)
    if len(a) < 2: return bot.reply_to(m, "Format: /reset USER_ID\n\nReset cooldown user.")
    d = load()
    users = d.setdefault("users", {})
    uid = a[1].strip()
    if uid in users:
        del users[uid]; save(d)
        bot.reply_to(m, f"✅ Cooldown user `{uid}` di-reset.", parse_mode="Markdown")
    else:
        bot.reply_to(m, "User belum pernah ambil key.")

def activate_key(m, payload):
    if "_" in payload:
        key, device_id = payload.split("_", 1)
    else:
        key, device_id = payload, str(m.from_user.id)
    key = key.strip().upper(); device_id = device_id.strip()[:32]
    d = load()
    if key not in d["keys"]:
        return bot.reply_to(m, f"❌ Key `{key}` tidak valid.", parse_mode="Markdown")
    r = d["keys"][key]; now = int(time.time())
    if r["used"]:
        exp = r["expired_at"] or 0
        if now > exp:
            return bot.reply_to(m, "❌ Key kadaluarsa.")
        return bot.reply_to(m, "⚠️ Key sudah dipakai.")
    exp = now + r["duration"]
    r["used"] = True; r["expired_at"] = exp; r["device_id"] = device_id
    save(d)
    expd = datetime.fromtimestamp(exp).strftime("%H:%M:%S - %A, %d %B %Y")
    bot.reply_to(m,
        f"💎 *Berhasil Diaktifkan* 💎\n\n🔑 `{key}`\n📱 `{device_id}`\n⏳ {expd}",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def c_text(m):
    t = m.text.strip()
    if not t or t.startswith("/"): return
    if m.from_user.id == ADMIN_ID:
        return bot.reply_to(m, "Gunakan /start untuk menu admin.")
    activate_key(m, t.upper())

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
