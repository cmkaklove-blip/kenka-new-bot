import os
import sys
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# ==========================================
# ⚙️ CONFIGS & SETUP (Cloud Optimized)
# ==========================================
API_ID       = int(os.getenv("API_ID", "37858091"))
API_HASH     = os.getenv("API_HASH", "66f6dd71a5038a817706d4e737f679ff")
OWNER_ID     = int(os.getenv("OWNER_ID", "5611725776"))
# String Session သုံးရင် ပိုအဆင်ပြေတယ် (မရှိရင် ဖုန်းနံပါတ်တောင်းပါလိမ့်မယ်)
STRING_SESSION = os.getenv("STRING_SESSION", None) 

if STRING_SESSION:
    app = Client("kenka_bot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
else:
    app = Client("kenka_bot", api_id=API_ID, api_hash=API_HASH)

# ==========================================
# 🧠 GLOBAL STATES (Logic Storage)
# ==========================================
tasks = {'attack': {}, 'godhell': {}}
hell_targets, hide_targets = set(), set()
godhell_last_msg, speeds = {}, {'attack': 0.5, 'hell': 0.5, 'godhell': 0.5, 'typing': 1.5}

# ==========================================
# 🛡️ AUTH FILTER (Owner Only)
# ==========================================
async def is_owner(_, __, message: Message):
    return (message.from_user and (message.from_user.is_self or message.from_user.id == OWNER_ID)) or \
           (message.sender_chat and message.sender_chat.id == OWNER_ID)

auth_filter = filters.create(is_owner)

# ==========================================
# 🛠️ HELPER LOGIC
# ==========================================
def get_messages():
    try:
        with open("auto_replies.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            return lines if lines else ["ခွေးကောင် သေစမ်း"]
    except: return ["ခွေးကောင် သေစမ်း"]

async def get_target(client, message):
    if message.reply_to_message: return message.reply_to_message.from_user.id
    parts = message.text.split()
    if len(parts) > 1:
        try: return (await client.get_users(parts[1])).id
        except: return int(parts[1]) if parts[1].isdigit() else None
    return None

# ==========================================
# ⚔️ CORE COMMANDS (Logic)
# ==========================================

# 1. Stop All Logic
@app.on_message(auth_filter & (filters.command("done", "/") | filters.regex("^တော်ပြီ")))
async def stop_all(c, m):
    [t.cancel() for t in list(tasks['attack'].values()) + list(tasks['godhell'].values())]
    tasks['attack'].clear(); tasks['godhell'].clear(); hell_targets.clear(); hide_targets.clear()
    await m.reply("**🛑 အကုန်ရပ်လိုက်ပြီ!**")

# 2. Attack Logic (Looping)
@app.on_message(auth_filter & (filters.command("attack", "/") | filters.regex("^တဗဲ့ရိုက်")))
async def start_attack(c, m):
    target = await get_target(c, m)
    if not target: return await m.reply("**⚠️ Target ရွေးပါ!**")
    await m.reply("**⚔️ Attack စတင်နေပြီ...**")
    tasks['attack'][target] = asyncio.create_task(attack_loop(c, m.chat.id, target))

async def attack_loop(c, chat_id, target):
    try:
        mention = (await c.get_users(target)).mention
        while True:
            for line in get_messages():
                await c.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(speeds['typing'])
                await c.send_message(chat_id, f"{mention} {line}")
                await asyncio.sleep(speeds['attack'])
    except asyncio.CancelledError: pass

# 3. Hell Logic (Watcher Pattern)
@app.on_message(auth_filter & (filters.command("hell", "/") | filters.regex("^@NgazenX")))
async def set_hell(c, m):
    target = await get_target(c, m)
    if target: hell_targets.add(target); await m.reply("**🔥 Hell Mode On!**")

@app.on_message(filters.all, group=1)
async def hell_watcher(c, m):
    if m.from_user and m.from_user.id in hell_targets:
        for _ in range(4):
            await c.send_chat_action(m.chat.id, ChatAction.TYPING)
            await asyncio.sleep(speeds['typing'])
            await m.reply(random.choice(get_messages()))
            await asyncio.sleep(speeds['hell'])

# 4. Hide Logic (Ghost Mode)
@app.on_message(auth_filter & (filters.command("hide", "/") | filters.regex("^အာဏာပြလိုက်")))
async def set_hide(c, m):
    target = await get_target(c, m)
    if target: hide_targets.add(target); await m.reply("**👻 Hide Mode On!**")

@app.on_message(filters.all, group=2)
async def hide_watcher(c, m):
    if m.from_user and m.from_user.id in hide_targets:
        try: await m.delete()
        except: pass

# ==========================================
# 📢 UTILS & STARTUP
# ==========================================
@app.on_message(auth_filter & (filters.command("show", "/") | filters.regex("^[Ss]how$")))
async def menu(c, m):
    await m.reply("**☠️ NGAZEN PRO MENU**\n\n`/attack` - ဆက်တိုက်ဆဲ\n`/hell` - သူပို့ရင်ပြန်ဆဲ\n`/hide` - စာဖျက်\n`/done` - ရပ်ရန်")

if __name__ == "__main__":
    print(">>> BOT STARTED! <<<")
    app.run()
  
