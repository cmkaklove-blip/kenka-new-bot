import os
import sys
import asyncio
import random
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# ==========================================
# 🌐 RENDER WEB SERVER (PORT BINDING FIX)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "NGAZEN USERBOT PRO IS ALIVE AND RUNNING!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ⚙️ CONFIGS & SETUP
# ==========================================
API_ID       = int(os.getenv("API_ID",  "37858091"))
API_HASH     = os.getenv("API_HASH",   "66f6dd71a5038a817706d4e737f679ff")
OWNER_ID     = int(os.getenv("OWNER_ID",  "5611725776"))
SESSION_NAME = "kenka_userbot"

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# ==========================================
# 🧠 GLOBAL STATES (ZERO-LAG MEMORY)
# ==========================================
tasks = {
    'attack': {},   # target_id: asyncio.Task
    'godhell': {}   # target_id: asyncio.Task
}
hell_targets = set()
hide_targets = set()
godhell_last_msg = {} # target_id: (chat_id, message_id)

# Default Speeds
speeds = {
    'attack': 0.5,  # ကြားထဲမှာနားမယ့်အချိန်
    'hell': 0.5,
    'godhell': 0.5,
    'typing': 1.5   # Typing ပေါ်မယ့်အချိန်
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
# 🛑 STOP ALL (/done | ရပ်လိုက်)
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
    await message.reply("**✅ အကုန်ရပ်လိုက်ပါပြီ! Operation Cancelled.**")

# ==========================================
# ⚔️ ATTACK MODE (/attack | တဗဲ့ရိုက်)
# ==========================================
@app.on_message(auth_filter & (filters.command("attack", prefixes="/") | filters.regex(r"^တဗဲ့ရိုက်(?:\s+|$)")))
async def start_attack(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...** (Reply သို့မဟုတ် ID/Mention တွဲရေးပါ)")
        return
    await message.reply("**⚔️ Attack Operation စတင်ပြီ!**")
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
# 🔥 HELL MODE (/hell | @NgazenX)
# ==========================================
@app.on_message(auth_filter & (filters.command("hell", prefixes="/") | filters.regex(r"^@NgazenX(?:\s+|$)")))
async def start_hell(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    hell_targets.add(target_id)
    await message.reply("**🔥 ငဇန် အမိန့်အတိုင်း ဟိုကောင့်ကို Hell ထဲ ပို့လိုက်ပြီ!**")

@app.on_message(filters.all, group=1)
async def hell_watcher(client, message):
    if message.from_user and message.from_user.id in hell_targets:
        asyncio.create_task(hell_reply_task(client, message))

async def hell_reply_task(client, message):
    try:
        lines = get_messages()
        for i in range(4): # သူပို့တိုင်း ၄ ကြောင်းပြန်မယ်
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
# 😈 GODHELL MODE (/godhell | ရိုက်ကွာ)
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
# 👻 HIDE MODE (/hide | အာဏာပြလိုက်)
# ==========================================
@app.on_message(auth_filter & (filters.command("hide", prefixes="/") | filters.regex(r"^အာဏာပြလိုက်(?:\s+|$)")))
async def start_hide(client, message):
    target_id = await get_target(client, message)
    if not target_id:
        await message.reply("**⚠️ ဘယ်ကောင်လဲ ရွေးပေးပါဦး...**")
        return
    hide_targets.add(target_id)
    await message.reply("**👻 ကဲ ငဇန် အမိန့်ပဲ... ဟိုကောင့်စာတွေ အကုန်ဖျက်မယ်!**")

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

# ==========================================
# ⚙️ SPEED CONTROLS (Full Logic Added)
# ==========================================
@app.on_message(auth_filter & filters.command("speed", prefixes="/"))
async def set_attack_speed(client, message):
    if len(message.command) > 1:
        try:
            speeds['attack'] = float(message.command[1])
            await message.reply(f"**⚡ Attack အမြန်နှုန်း {speeds['attack']}s သို့ ပြောင်းလိုက်ပါပြီ။**")
        except ValueError:
            await message.reply("**⚠️ ဂဏန်းထည့်ပါ...**")
    else:
        await message.reply(f"**⚡ လက်ရှိ Attack မြန်နှုန်း:** {speeds['attack']}s")

@app.on_message(auth_filter & filters.command("speedhell", prefixes="/"))
async def set_hell_speed(client, message):
    if len(message.command) > 1:
        try:
            speeds['hell'] = float(message.command[1])
            await message.reply(f"**🔥 Hell အမြန်နှုန်း {speeds['hell']}s သို့ ပြောင်းလိုက်ပါပြီ။**")
        except ValueError:
            await message.reply("**⚠️ ဂဏန်းထည့်ပါ...**")
    else:
        await message.reply(f"**🔥 လက်ရှိ Hell မြန်နှုန်း:** {speeds['hell']}s")

@app.on_message(auth_filter & filters.command("godspeed", prefixes="/"))
async def set_god_speed(client, message):
    if len(message.command) > 1:
        try:
            speeds['godhell'] = float(message.command[1])
            await message.reply(f"**😈 GodHell အမြန်နှုန်း {speeds['godhell']}s သို့ ပြောင်းလိုက်ပါပြီ။**")
        except ValueError:
            await message.reply("**⚠️ ဂဏန်းထည့်ပါ...**")
    else:
        await message.reply(f"**😈 လက်ရှိ GodHell မြန်နှုန်း:** {speeds['godhell']}s")

# ==========================================
# 📢 BROADCAST
# ==========================================
@app.on_message(auth_filter & filters.command("broadcast", prefixes="/"))
async def broadcast_msg(client, message):
    if not message.reply_to_message:
        await message.reply("**⚠️ Reply လုပ်ပြီးမှ သုံးပါ...**")
        return
    status_msg = await message.reply("**📢 Broadcast စတင်နေပြီ...**")
    success, failed = 0, 0
    async for dialog in client.get_dialogs():
        if dialog.chat.id == message.chat.id:
            continue
        try:
            await client.send_chat_action(dialog.chat.id, ChatAction.TYPING)
            await asyncio.sleep(0.2)
            await message.reply_to_message.copy(dialog.chat.id)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
    await status_msg.edit(f"**✅ Broadcast ပြီးဆုံး!**\n**✓ အောင်မြင်:** {success}\n**✗ ကျရှုံး:** {failed}")

# ==========================================
# 📝 MESSAGE MANAGEMENT
# ==========================================
@app.on_message(auth_filter & filters.command("add_message", prefixes="/"))
async def add_txt(client, message):
    if len(message.command) < 2:
        await message.reply("**⚠️ ထည့်ချင်တဲ့ စာသားရေးပါ...**")
        return
    text = message.text.split(maxsplit=1)[1]
    if text:
        with open("auto_replies.txt", "a", encoding="utf-8") as f:
            f.write(text + "\n")
        await message.reply(f"**✅ စာသားအသစ် ထည့်သွင်းပြီးပါပြီ**\n`{text}`")

@app.on_message(auth_filter & filters.command("list_messages", prefixes="/"))
async def list_messages(client, message):
    lines = get_messages()
    msg_list = "\n".join([f"**{i+1}.** `{line}`" for i, line in enumerate(lines)])
    await message.reply(f"**📋 လက်ရှိ ဆဲမယ့် စာသားများ**\n\n{msg_list}")

@app.on_message(auth_filter & filters.command("remove_message", prefixes="/"))
async def remove_message(client, message):
    if len(message.command) < 2:
        await message.reply("**⚠️ ဖျက်ချင်တဲ့ နံပါတ် ထည့်ပါ...**")
        return
    try:
        index = int(message.command[1]) - 1
        lines = get_messages()
        if 0 <= index < len(lines):
            removed = lines.pop(index)
            with open("auto_replies.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
            await message.reply(f"**🗑️ စာသားဖျက်လိုက်ပါပြီ**\n`{removed}`")
        else:
            await message.reply("**⚠️ နံပါတ် မှားနေပါတယ်။**")
    except ValueError:
        await message.reply("**⚠️ ဂဏန်းပဲ ထည့်ပါ။**")

# ==========================================
# 💎 SHOW MENU (/show)
# ==========================================
@app.on_message(auth_filter & (filters.command("show", prefixes="/") | filters.regex(r"^[Ss]how$")))
async def show_commands(client, message):
    cmds = """
╭━━ ☠️ **NGAZEN USERBOT PRO** ☠️ ━━╮

**⚔️ ATTACK MODES (တိုက်ခိုက်ရေး)**
➤ `/attack` or `တဗဲ့ရိုက်` 
➤ `/hell` or `@NgazenX` 
➤ `/godhell` or `ရိုက်ကွာ` 
➤ `/hide` or `အာဏာပြလိုက်` 
➤ `/done` or `တော်ပြီ` 

**⚙️ SPEED CONTROLS (မြန်နှုန်း)**
➤ `/speed [sec]` » Attack အမြန်နှုန်း
➤ `/speedhell [sec]` » Hell အမြန်နှုန်း
➤ `/godspeed [sec]` » GodHell အမြန်နှုန်း

**📝 MESSAGE DB (စာသားစီမံရန်)**
➤ `/add_message [စာသား]` » စာထည့်ရန်
➤ `/list_messages` » စာရင်းကြည့်ရန်
➤ `/remove_message [နံပါတ်]` » စာဖျက်ရန်

**🌐 UTILS (အခြား)**
➤ `/broadcast` » Reply စာကို Group အကုန်ပို့မယ်
➤ `/show` သို့မဟုတ် `show` » ဒီ Menu ကိုပြမယ်
➤ `/restart` » Bot ကို ပြန်ဖွင့်မယ်

╰━━━━━━━━━━━━━━━━━━━━━╯
    """
    await message.reply(cmds)

# ==========================================
# 🔄 RESTART
# ==========================================
@app.on_message(auth_filter & filters.command("restart", prefixes="/"))
async def restart_bot(client, message):
    await message.reply("**🔄 System Rebooting... ပြန်ဖွင့်နေပါပြီ!**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==========================================
# 🚀 RUN BOT & WEB SERVER
# ==========================================
if __name__ == "__main__":
    os.system('clear' if os.name == 'posix' else 'cls')
    print("="*50)
    print(" ☠️  NGAZEN USERBOT V2 - PRO EDITION INITIALIZING...  ☠️ ")
    
    # Start Flask Web Server in Background Thread
    threading.Thread(target=run_web, daemon=True).start()
    print(" >>> WEB SERVER STARTED (PORT BINDING SUCCESS) ")
    
    # Start Telegram Bot
    print(" >>> WAITING FOR COMMANDS... ")
    print("="*50)
    app.run()
