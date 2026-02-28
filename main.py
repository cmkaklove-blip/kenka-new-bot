import os
import sys
import asyncio
import random
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# ==========================================
# 🌐 RENDER KEEP-ALIVE SERVER (FOR PORT 10000)
# ==========================================
# Render က Web Service အဖြစ် အသိအမှတ်ပြုဖို့အတွက် ဒီအပိုင်းက မရှိမဖြစ်လိုအပ်ပါတယ်
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "NGAZEN USERBOT IS ONLINE!"

def run_flask():
    # Render ရဲ့ Default Port 10000 မှာ Flask ကို ပေး Run တာပါ
    flask_app.run(host='0.0.0.0', port=10000)

# Flask ကို Background Thread အနေနဲ့ စတင်ပေးလိုက်ပါတယ်
threading.Thread(target=run_flask, daemon=True).start()

# ==========================================
# ⚙️ CONFIGS & SETUP
# ==========================================
# GitHub Secrets သို့မဟုတ် Render Environment Variables ထဲကနေ ဆွဲဖတ်ပါတယ်
API_ID       = int(os.getenv("API_ID", "37858091"))
API_HASH     = os.getenv("API_HASH", "66f6dd71a5038a817706d4e737f679ff")
OWNER_ID     = int(os.getenv("OWNER_ID", "5611725776"))
SESSION_NAME = "kenka_userbot"

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# ==========================================
# 🧠 GLOBAL STATES (ZERO-LAG MEMORY)
# ==========================================
tasks = {
    'attack': {},
    'godhell': {}
}
hell_targets = set()
hide_targets = set()
godhell_last_msg = {} 

speeds = {
    'attack': 0.5,
    'hell': 0.5,
    'godhell': 0.5,
    'typing': 1.5
}

# ==========================================
# 🛡️ AUTH FILTER (OWNER ONLY)
# ==========================================
def is_owner_or_me(_, __, message: Message):
    if not message.from_user: 
        if message.sender_chat and message.sender_chat.id == OWNER_ID:
            return True
        return False
    return message.from_user.is_self or message.from_user.id == OWNER_ID

auth_filter = filters.create(is_owner_or_me)

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def get_messages():
    try:
        with open("auto_replies.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            return lines if lines else ["ခွေးကောင် သေစမ်း"]
    except FileNotFoundError:
        with open("auto_replies.txt", "w", encoding="utf-8") as f:
            f.write("ခွေးကောင် သေစမ်း\n")
        return ["ခွေးကောင် သေစမ်း"]

async def get_target(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    
    text_parts = message.text.split()
    if len(text_parts) > 1:
        try:
            user = await client.get_users(text_parts[1])
            return user.id
        except:
            try:
                return int(text_parts[1])
            except:
                pass
    return None

# ==========================================
# 🛑 STOP ALL (/done)
# ==========================================
@app.on_message(auth_filter & (filters.command("done", prefixes="/") | filters.regex(r"^တော်ပြီ(?:\s+|$)")))
async def stop_all_cmds(client, message):
    for task in tasks['attack'].values(): task.cancel()
    for task in tasks['godhell'].values(): task.cancel()
    
    tasks['attack'].clear()
    tasks['godhell'].clear()
    hell_targets.clear()
    hide_targets.clear()
    godhell_last_msg.clear()
    
    await message.reply("**✅ အကုန်ရပ်လိုက်ပါပြီ!**")

# ==========================================
# ⚔️ ATTACK MODE (/attack)
# ==========================================
@app.on_message(auth_filter & (filters.command("attack", prefixes="/") | filters.regex(r"^တဗဲ့ရိုက်(?:\s+|$)")))
async def start_attack(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    
    await message.reply("**⚔️ Operation စတင်ပြီ!**")
    
    if target_id in tasks['attack']:
        tasks['attack'][target_id].cancel()
        
    tasks['attack'][target_id] = asyncio.create_task(attack_loop(client, message.chat.id, target_id))

async def attack_loop(client, chat_id, target_id):
    try:
        user = await client.get_users(target_id)
        mention = user.mention
    except:
        mention = f"ဟေ့ကောင် {target_id}"

    while True:
        try:
            lines = get_messages()
            for line in lines:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(speeds['typing']) 
                try:
                    await client.send_message(chat_id, f"{mention} {line}")
                except Exception:
                    continue
                await asyncio.sleep(speeds['attack'])
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)

# ==========================================
# 🔥 HELL MODE (/hell)
# ==========================================
@app.on_message(auth_filter & (filters.command("hell", prefixes="/") | filters.regex(r"^@NgazenX(?:\s+|$)")))
async def start_hell(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    hell_targets.add(target_id)
    await message.reply("**🔥 Hell Mode Activated!**")

@app.on_message(filters.all, group=1)
async def hell_watcher(client, message):
    if message.from_user and message.from_user.id in hell_targets:
        asyncio.create_task(hell_reply_task(client, message))

async def hell_reply_task(client, message):
    try:
        lines = get_messages()
        for i in range(4):
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(speeds['typing'])
            try:
                line = random.choice(lines)
                await message.reply(line, quote=True)
            except Exception:
                continue
            await asyncio.sleep(speeds['hell'])
    except Exception:
        pass

# ==========================================
# 😈 GODHELL MODE (/godhell)
# ==========================================
@app.on_message(auth_filter & (filters.command("godhell", prefixes="/") | filters.regex(r"^ရိုက်ကွာ(?:\s+|$)")))
async def start_godhell(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    
    await message.reply("**😈 GodHell Started!**")
    
    if target_id in tasks['godhell']:
        tasks['godhell'][target_id].cancel()
        
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == target_id:
        godhell_last_msg[target_id] = (message.chat.id, message.reply_to_message.id)
        
    tasks['godhell'][target_id] = asyncio.create_task(godhell_loop(client, target_id))

@app.on_message(filters.all, group=2)
async def godhell_watcher(client, message):
    if message.from_user and message.from_user.id in tasks['godhell']:
        godhell_last_msg[message.from_user.id] = (message.chat.id, message.id)

async def godhell_loop(client, target_id):
    while True:
        try:
            if target_id in godhell_last_msg:
                chat_id, msg_id = godhell_last_msg[target_id]
                lines = get_messages()
                line = random.choice(lines)
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(speeds['typing'])
                try:
                    await client.send_message(chat_id, line, reply_to_message_id=msg_id)
                except Exception:
                    pass
            await asyncio.sleep(speeds['godhell'])
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)

# ==========================================
# 📢 OTHER UTILS (HIDE, BROADCAST, DB)
# ==========================================
@app.on_message(auth_filter & (filters.command("hide", prefixes="/") | filters.regex(r"^အာဏာပြလိုက်(?:\s+|$)")))
async def start_hide(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    hide_targets.add(target_id)
    await message.reply("**👻 Ghost Mode On!**")

@app.on_message(filters.all, group=3)
async def hide_watcher(client, message):
    if message.from_user and message.from_user.id in hide_targets:
        asyncio.create_task(delete_msg_task(message))

async def delete_msg_task(message):
    try:
        await asyncio.sleep(0.1)
        await message.delete()
    except Exception:
        pass

@app.on_message(auth_filter & filters.command("show", prefixes="/"))
async def show_commands(client, message):
    cmds = """
╭━━ ☠️ **NGAZEN USERBOT PRO** ☠️ ━━╮
➤ `/attack` » တဗဲ့ရိုက်
➤ `/hell` » @NgazenX
➤ `/godhell` » ရိုက်ကွာ
➤ `/hide` » အာဏာပြလိုက်
➤ `/done` » တော်ပြီ 🛑
➤ `/show` » ဒီ Menu ကိုပြမယ်
╰━━━━━━━━━━━━━━━━━━━━━╯
    """
    await message.reply(cmds)

# ==========================================
# 🚀 ASYNC MAIN ENTRY (FIX FOR RUNTIMERROR)
# ==========================================
async def main():
    print("="*50)
    print(" ☠️  NGAZEN USERBOT V2 - PRO EDITION INITIALIZING... ")
    await app.start()
    print(" >>> BOT STARTED SUCCESSFULLY! ")
    print("="*50)
    await idle() # Bot ကို အမြဲတမ်း Run ထားပေးမယ်
    await app.stop()

if __name__ == "__main__":
    # Event loop အသစ်ဆောက်ပြီး Main function ကို run ပါတယ် (Python 3.12+ error ရှင်းရန်)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
