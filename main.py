# main.py - FINAL PRODUCTION (MODIFIED)
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from config import *
from database import *
from keyboards import *

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()
admin_temp = {}

# --- স্বাগতম মেসেজ (ভাইরাল লিংক আপডেটসহ) ---
WELCOME_TEXT = (
    "✨ **স্বাগতম আমাদের বিনোদন জোনে!** ✨\n\n"
    "🇧🇩 **বাংলাদেশের সকল ধরনের ভাইরাল লিংক সবার আগে দেখতে পাবেন আমাদের এই গ্রুপে।**\n\n"
    "📺 আমাদের সকল ভিডিও আপনি পেয়ে যাবেন নিচে দেওয়া মেইন গ্রুপে। এখনই জয়েন করে রাখুন!\n\n"
    "💎 **ডেইলি বোনাস:** আপনার জন্য প্রতিদিন **৫ টি ফ্রি ক্রেডিট** বরাদ্দ করা হয়েছে। প্রতি ২৪ ঘণ্টা পর পর এগুলো অটোমেটিক রিনিউ হবে।\n\n"
    "🎬 **ভিডিও দেখার নিয়ম:**\n"
    "মেইন গ্রুপে যান এবং ভিডিওর নিচে থাকা **[Watch Now]** বাটনে ক্লিক করুন। ভিডিওটি সাথে সাথে এখানে চলে আসবে।\n\n"
    "👑 **ভিআইপি মেম্বারশিপ:**\n"
    "আনলিমিটেড ভিডিও এবং সকল ভিআইপি গ্রুপ এক্সেস করতে মেম্বারশিপ নিন।\n\n"
    f"🚀 **নিচের লিঙ্কে ক্লিক করে গ্রুপে জয়েন করুন:**\n"
    f"🌐 [JOIN MAIN VIDEO GROUP]({MAIN_GROUP_LINK})\n"
    "━━━━━━━━━━━━━━━━━━━━"
)

# --- ভিআইপি মেয়াদ চেক করার ব্যাকগ্রাউন্ড টাস্ক ---
async def check_vip_expiry():
    while True:
        try:
            today_obj = datetime.now()
            tomorrow_obj = today_obj + timedelta(days=1)
            
            today_str = today_obj.strftime("%d-%m-%Y")
            tomorrow_str = tomorrow_obj.strftime("%d-%m-%Y")
            
            users = await get_all_users()
            for u in users:
                if u.get('membership') == 'VIP' and u.get('expiry_date'):
                    exp_date = u['expiry_date']
                    uid = u['user_id']
                    name = u.get('name', 'User')

                    # ২৪ ঘণ্টা আগে নোটিফিকেশন (ইউজারকে)
                    if exp_date == tomorrow_str:
                        try:
                            await bot.send_message(uid, "⚠️ **সতর্কবার্তা!**\nআপনার VIP মেম্বারশিপের মেয়াদ আগামী **২৪ ঘণ্টার** মধ্যে শেষ হয়ে যাবে। নিরবচ্ছিন্ন সেবা পেতে রিনিউ করুন।")
                        except: pass
                    
                    # মেয়াদ শেষ হওয়ার দিন (অ্যাডমিনকে এবং ইউজারকে রিপোর্ট)
                    elif exp_date == today_str:
                        try:
                            await bot.send_message(uid, "🔴 **আপনার VIP মেম্বারশিপের মেয়াদ আজকেই শেষ।**")
                        except: pass
                        
                        report = (
                            "📢 **VIP এক্সপায়ারি রিপোর্ট!**\n\n"
                            f"👤 নাম: {name}\n"
                            f"🆔 আইডি: `{uid}`\n"
                            "⚠️ এই ইউজারের মেম্বারশিপের মেয়াদ আজকেই শেষ।"
                        )
                        await bot.send_message(ADMIN_ID, report)
            
            await asyncio.sleep(43200) # প্রতি ১২ ঘণ্টা পর পর চেক করবে
        except Exception as e:
            logging.error(f"Expiry Loop Error: {e}")
            await asyncio.sleep(60)
            
# --- সহায়ক ফাংশনসমূহ ---
async def check_banned(user_id):
    u = await get_user(user_id)
    return u.get('status') == 'banned' if u else False

# --- ভিডিও অটো ডিলিট লজিক ---
async def delete_after_timer(chat_id, message_id):
    await asyncio.sleep(DELETE_TIMER)
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

# --- মডিফাইড স্টার্ট হ্যান্ডলার (শুধুমাত্র এই অংশটুকু রিপ্লেস করুন) ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if await check_banned(user_id):
        return await message.answer(f"❌ **আপনাকে বট থেকে ব্যান করা হয়েছে!**\n\n🆘 **যোগাযোগ করুন:** @leo20608", reply_markup=types.ReplyKeyboardRemove())
    
    user = await get_user(user_id)
    
    # ইউজার যদি একদম নতুন হয় (ডাটাবেসে না থাকে)
    if not user: 
        await add_user(user_id, message.from_user.full_name)
        
        # লিঙ্ক থেকে রেফারাল আইডি বের করার লজিক
        args = message.text.split()
        if len(args) > 1:
            try:
                referrer_id = int(args[1])
                # নিজের লিঙ্কে নিজে ক্লিক না করলে ৫ ক্রেডিট পাবে
                if referrer_id != user_id:
                    await update_credits(referrer_id, 5) # মূল রেফায়ারকে ৫ ক্রেডিট দেওয়া হলো
                    await users_col.update_one({"user_id": referrer_id}, {"$inc": {"referrals": 1}}) # মোট রেফারেল +১ জন
                    
                    # রেফায়ারকে খুশির খবর পাঠানো
                    try:
                        await bot.send_message(
                            chat_id=referrer_id, 
                            text=f"🎉 **রেফারেল সফল!** আপনার লিঙ্ক ব্যবহার করে একজন নতুন ইউজার জয়েন করেছে। আপনার অ্যাকাউন্টে **৫ ক্রেডিট** (💎) যোগ করা হয়েছে।"
                        )
                    except: pass
            except Exception as e:
                logging.error(f"Referral Error: {e}")
    
    markup = admin_start_kb() if user_id == ADMIN_ID else main_menu()
    await message.answer(WELCOME_TEXT, reply_markup=markup, disable_web_page_preview=False)

# --- অ্যাডমিন পোস্টিং ফ্লো (ভিডিও -> থাম্বনেইল -> পোস্ট) ---
@dp.message(F.video, F.from_user.id == ADMIN_ID)
async def handle_admin_video(message: types.Message):
    admin_temp[ADMIN_ID] = {
        "step": "wait_thumb",
        "video_file_id": message.video.file_id,
        "caption": message.caption or "নতুন একটি প্রিমিয়াম ভিডিও চলে আসলো!"
    }
    await message.reply("✅ ভিডিওটি পেয়েছি। এখন এই ভিডিওর জন্য একটি **AI জেনারেটেড থাম্বনেইল (Photo)** পাঠান।")

@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def handle_admin_thumb(message: types.Message):
    data = admin_temp.get(ADMIN_ID)
    if data and data.get("step") == "wait_thumb":
        data["thumb_id"] = message.photo[-1].file_id
        data["step"] = "confirm_post"
        await message.answer_photo(data["thumb_id"], caption=f"📝 **পোস্ট প্রিভিউ:**\n\n{data['caption']}\n\nআপনি কি এটি পোস্ট করতে চান?", reply_markup=post_confirm_kb())

@dp.callback_query(F.data == "post_confirm")
async def finalize_post(c: types.CallbackQuery):
    data = admin_temp.get(ADMIN_ID)
    if not data: 
        return
    
    post_caption = (
        f"🎬 **{data['caption']}**\n\n"
        "📢 **সতর্কবার্তা:**\n"
        "নিরাপত্তার স্বার্থে আমরা অনেক সময় ভিডিওর আসল থাম্বনেইলের বদলে AI জেনারেটেড ইমেজ ব্যবহার করি। কারণ ভিডিওগুলো অনেক সেনসিティブ এবং এগ্রেসিভ, যা সরাসরি গ্রুপে দিলে আমাদের বট এবং গ্রুপ ব্যান হওয়ার ঝুঁকি থাকে।\n\n"
        "⚠️ যে কোনো সময় এই গ্রুপ ব্যান হয়ে যেতে পারে, তাই অবশ্যই আমাদের **ব্যাকআপ চ্যানেলে** জয়েন থাকুন যেন কানেকশন বিচ্ছিন্ন না হয়।\n\n"
        "👇 ভিডিওটি দেখতে নিচের **[Watch Now]** বাটনে ক্লিক করুন।"
    )

    # এখানে ইনডেন্টেশন একদম পারফেক্টলি ৪টি স্পেস দিয়ে সোজাসুজি করা হয়েছে
    sent_msg = await bot.send_photo(
        chat_id=MAIN_GROUP_ID, 
        photo=data["thumb_id"], 
        caption=post_caption, 
        reply_markup=watch_button() 
    )
    
    # 🌟 র‍্যামেও থাকলো + ডাটাবেসেও সেভ হলো চিরস্থায়ীভাবে
    video_file_id = data["video_file_id"]
    admin_temp[f"video_{sent_msg.message_id}"] = video_file_id
    
    # সরাসরি MongoDB-তে ভিডিওর ডাটা চিরস্থায়ীভাবে পুশ করা হচ্ছে:
    await db["posts_videos"].insert_one({
        "msg_id": sent_msg.message_id,
        "video_id": video_file_id
    })
    
    await c.message.edit_caption(caption="✅ সফলভাবে মেইন গ্রুপে পোস্ট করা হয়েছে।")
    admin_temp.pop(ADMIN_ID, None)

@dp.callback_query(F.data == "post_cancel")
async def cancel_post(c: types.CallbackQuery):
    admin_temp.pop(ADMIN_ID, None)
    await c.message.edit_caption(caption="❌ পোস্টিং বাতিল করা হয়েছে।")

# --- ভিডিও দেখা ও ক্রেডিট লজিক (ফোর্স জয়েন রিমুভড) ---
@dp.callback_query(F.data == "watch_video")
async def handle_watch_video(c: types.CallbackQuery):
    user_id = c.from_user.id
    
    user = await get_user(user_id)
    if user['membership'] != 'VIP' and user.get('credits', 0) <= 0:
        return await c.answer("❌ আপনার পর্যাপ্ত ক্রেডিট নেই!", show_alert=True)

    # 🌟 প্রথমে র‍্যামে খুঁজবে, না পেলে ডাটাবেস থেকে ভিডিও আইডি টেনে আনবে
    msg_key = f"video_{c.message.message_id}"
    video_id = admin_temp.get(msg_key)
    
    if not video_id:
        # ডাটাবেস থেকে খোঁজা হচ্ছে
        db_data = await db["posts_videos"].find_one({"msg_id": c.message.message_id})
        if db_data:
            video_id = db_data["video_id"]
            admin_temp[msg_key] = video_id # পরের বারের জন্য আবার র‍্যামে রেখে দেওয়া হলো

    privacy_msg = (
        "🔐 **আপনার গোপনীয়তা আমাদের অগ্রাধিকার!**\n\n"
        "আমরা চাই আপনার ব্যক্তিগত তথ্য এবং আপনি কী ভিডিও দেখছেন তা সম্পূর্ণ গোপন থাকুক। আপনার ফোন অন্য কারো হাতে পড়লেও যেন তারা কিছু বুঝতে না পারে, সেজন্য আমরা এই ভিডিওটি **১৫ মিনিট পর** অটোমেটিক ডিলিট হয়ে যাবে।\n\n"
        "⏳ ভিডিওটি এখনই দেখে নিন।"
    )

    try:
        if video_id:
            msg = await bot.send_video(chat_id=user_id, video=video_id, caption=privacy_msg)
            asyncio.create_task(delete_after_timer(user_id, msg.message_id))
        else:
            await bot.copy_message(chat_id=user_id, from_chat_id=c.message.chat.id, message_id=c.message.message_id)
            info = await bot.send_message(user_id, privacy_msg)
            asyncio.create_task(delete_after_timer(user_id, info.message_id))
        
        if user['membership'] != 'VIP':
            await update_credits(user_id, -1)
            await c.answer("✅ ১ ক্রেডিট কাটা হয়েছে। ইনবক্স চেক করুন।", show_alert=True)
    except:
        await c.answer("❌ ভিডিও পাঠাতে সমস্যা হয়েছে। বটের ইনবক্সে গিয়ে /start দিন।", show_alert=True)

# --- ইউজার বাটন হ্যান্ডলারস ---
@dp.message(F.text == "My Profile")
async def profile_h(message: types.Message):
    if await check_banned(message.from_user.id): return
    u = await get_user(message.from_user.id)
    if not u: return
    status = u.get('membership', 'Free').upper()
    credit = "♾️ Unlimited" if status == "VIP" else f"{u.get('credits', 0)} 💎"
    exp = u.get('expiry_date')
    expiry_info = f"📅 **মেয়াদ শেষ:** `{exp}`\n" if status == "VIP" and exp else ""
    
    profile_text = (
        "👤 **আপনার প্রোফাইল তথ্য**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 **স্ট্যাটাস:** `{status}`\n"
        f"{expiry_info}"
        f"💰 **ব্যালেন্স:** {credit}\n"
        f"🆔 **আইডি:** `{u['user_id']}`\n"
        f"👥 **মোট রেফারেল:** {u.get('referrals', 0)} জন\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 **রেফারেল ধামাকা অফার!**\n"
        "আপনার রেফারেল লিঙ্ক ব্যবহার করে নতুন কেউ আমাদের বটে জয়েন করলেই আপনি সাথে সাথে পেয়ে যাবেন **৫টি ফ্রি ক্রেডিট** (💎)!\n\n"
        "🔗 **আপনার রেফারেল লিঙ্ক:**\n"
        f"https://t.me/{(await bot.get_me()).username}?start={u['user_id']}"
    )
    await message.answer(profile_text)

@dp.message(F.text == "VIP Membership")
async def vip_h(message: types.Message):
    if await check_banned(message.from_user.id): return
    await message.answer(VIP_PACKAGES_TEXT, reply_markup=vip_keyboard())

@dp.message(F.text == "Main Group")
async def group_h(message: types.Message):
    if await check_banned(message.from_user.id): return
    await message.answer(f"📺 **মেইন ভিডিও গ্রুপ লিঙ্ক:**\n\n{MAIN_GROUP_LINK}")

@dp.message(F.text == "Support")
async def support_h(message: types.Message):
    await message.answer(f"🛠 **সাপোর্টের জন্য যোগাযোগ করুন:**\n{SUPPORT_LINK}")

# --- অ্যাডমিন ড্যাশবোর্ড লজিক ---
@dp.message(F.text == "Admin Panel", F.from_user.id == ADMIN_ID)
async def admin_p(message: types.Message):
    await message.answer("🛠 অ্যাডমিন ড্যাশবোর্ড সচল হয়েছে।", reply_markup=admin_sub_menu())

@dp.message(F.from_user.id == ADMIN_ID)
async def admin_main_handler(message: types.Message):
    aid = message.from_user.id
    if message.text == "Stats":
        users = await get_all_users() # ডাটাবেস থেকে সব ইউজার নেওয়া হচ্ছে
        msg = f"📊 **বট স্ট্যাটাস রিপোর্ট**\n━━━━━━━━━━━━━━━━━━━━\n👥 **মোট ইউজার:** {len(users)} জন\n\n🆕 **সাম্প্রতিক ১০ জন ইউজার:**\n"
        
        # শেষের ১০ জন ইউজারকে লুপ ঘুরিয়ে নাম এবং UID বের করা হচ্ছে
        for u in users[-10:]:
            raw_name = u.get('name', 'N/A')
            
            # নামের ভেতরের স্পেশাল ক্যারেক্টারগুলো পরিষ্কার করা হচ্ছে যাতে মার্কডাউন ক্র্যাশ না করে
            clean_name = raw_name.replace("*", "").replace("_", "").replace("[", "").replace("]", "").replace("`", "")
            
            # এখন একদম নিরাপদভাবে মেসেজে নাম যুক্ত হবে
            msg += f"• 👤 {clean_name} | 🆔 UID: `{u['user_id']}`\n"
            
        await message.answer(msg)
    elif message.text == "Credits":
        kb = [[InlineKeyboardButton(text="➕ Add", callback_data="adm_c_add"), InlineKeyboardButton(text="➖ Remove", callback_data="adm_c_rem")]]
        await message.answer("ক্রেডিট একশন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif message.text == "VIP Update":
        kb = [[InlineKeyboardButton(text="✅ Set VIP", callback_data="adm_v_set"), InlineKeyboardButton(text="❌ Remove VIP", callback_data="adm_v_rem")]]
        await message.answer("VIP একশন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif message.text == "User Ban":
        kb = [[InlineKeyboardButton(text="🚫 Ban", callback_data="adm_u_ban"), InlineKeyboardButton(text="✅ Unban", callback_data="adm_u_unb")]]
        await message.answer("ব্যান কন্ট্রোল:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    elif message.text == "Broadcast":
        await message.answer("📢 ব্রডকাস্ট মেসেজটি লিখুন:")
        admin_temp[aid] = "wait_broadcast"
    elif message.text == "Back to Menu":
        await message.answer("মেনু খোলা হয়েছে।", reply_markup=admin_start_kb())
    else:
        state = admin_temp.get(aid)
        if not state: return
        
        if state == "wait_broadcast":
            users = await get_all_users()
            count = 0
            for u in users:
                try:
                    await bot.send_message(u['user_id'], message.text)
                    count += 1
                except: continue
            await message.answer(f"✅ ব্রডকাস্ট সফল! {count} জন ইউজার মেসেজ পেয়েছে।")
            admin_temp.pop(aid, None)
            
        elif state.startswith("wait_uid_"):
            target_uid = message.text
            admin_temp[f"target_{aid}"] = target_uid
            action = state.replace("wait_uid_", "")
            
            if action == "c_add":
                admin_temp[aid] = "wait_val_c_add"
                await message.answer(f"UID `{target_uid}`-কে কত ক্রেডিট দিবেন?")
            elif action == "c_rem":
                admin_temp[aid] = "wait_val_c_rem"
                await message.answer(f"UID `{target_uid}` থেকে কত ক্রেডিট কাটবেন?")
            elif action == "v_set":
                admin_temp[aid] = "wait_val_v_days"
                await message.answer(f"UID `{target_uid}`-কে কত দিনের VIP দিবেন?")
            elif action == "v_rem":
                await users_col.update_one({"user_id": int(target_uid)}, {"$set": {"membership": "Free"}, "$unset": {"expiry_date": ""}})
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target_uid), "📉 **আপনার VIP মেম্বারশিপ শেষ হয়েছে বা সরিয়ে নেওয়া হয়েছে।**")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"✅ `{target_uid}` এখন ফ্রি মেম্বার।")
                admin_temp.pop(aid, None)
            elif action == "u_ban":
                await users_col.update_one({"user_id": int(target_uid)}, {"$set": {"status": "banned"}})
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target_uid), "🚫 **আপনাকে বট থেকে ব্যান করা হয়েছে!**\n🆘 যোগাযোগ: @leo20608")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"🚫 `{target_uid}` ব্যান হয়েছে।")
                admin_temp.pop(aid, None)
            elif action == "u_unb":
                await users_col.update_one({"user_id": int(target_uid)}, {"$set": {"status": "active"}})
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target_uid), "✅ **অভিনন্দন! আপনার ব্যান সরিয়ে নেওয়া হয়েছে।**")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"✅ `{target_uid}` এখন আনব্যান হয়েছে।")
                admin_temp.pop(aid, None)

        elif state.startswith("wait_val_"):
            target = admin_temp.get(f"target_{aid}")
            val = int(message.text)
            if state == "wait_val_c_add":
                await update_credits(int(target), val)
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target), f"💎 **আপনার অ্যাকাউন্টে {val} ক্রেডিট যোগ করা হয়েছে!**")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"✅ {val} ক্রেডিট অ্যাড হয়েছে।")
            elif state == "wait_val_c_rem":
                await update_credits(int(target), -val)
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target), f"📉 **আপনার অ্যাকাউন্ট থেকে {val} ক্রেডিট কাটা হয়েছে।**")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"✅ {val} ক্রেডিট রিমুভ হয়েছে।")
            elif state == "wait_val_v_days":
                exp_date = (datetime.now() + timedelta(days=val)).strftime("%d-%m-%Y")
                await users_col.update_one({"user_id": int(target)}, {"$set": {"membership": "VIP", "expiry_date": exp_date}})
                # --- ইউজার নোটিফিকেশন শুরু ---
                try: await bot.send_message(int(target), f"👑 **অভিনন্দন! আপনি {val} দিনের VIP মেম্বারশিপ পেয়েছেন।**\n📅 মেয়াদ: {exp_date}")
                except: pass
                # --- ইউজার নোটিফিকেশন শেষ ---
                await message.answer(f"✅ `{target}` এখন {val} দিনের VIP। মেয়াদ: {exp_date}")
            admin_temp.pop(aid, None)
@dp.callback_query(F.data.startswith("adm_"))
async def admin_callback_handler(c: types.CallbackQuery):
    admin_temp[c.from_user.id] = f"wait_uid_{c.data[4:]}"
    await c.message.answer("ইউজারের **UID** দিন:")

import asyncio

# আপনার বাকি কোড (bot, dp, ইত্যাদি) এখানে থাকবে...

async def main():
    # টার্মিনাল ক্লিয়ার করার জন্য (ঐচ্ছিক, একদম ফ্রেশ লুকের জন্য)
    # import os; os.system('cls' if os.name == 'nt' else 'clear')
    
    # ডার্ক হিমু স্পেশাল সিএমডি ব্যানার
    banner = """
  ____             _       _   _ _                  
 |  _ \  __ _ _ __| | __  | | | (_)_ __ ___  _   _ 
 | | | |/ _` | '__| |/ /  | |_| | | '_ ` _ \| | | |
 | |_| | (_| | |  |   <   |  _  | | | | | | | |_| |
 |____/ \__,_|_|  |_|\\_\\  |_| |_|_|_| |_| |_|\\__,_|
                                                   
 ──────────────────────────────────────────────────────────
 [🌙] SYSTEM   : OPERATIONAL
 [👤] DEVELOPER: Dark Himu
 [🚀] STATUS   : BOT IS ONLINE AND RUNNING 24/7
 ──────────────────────────────────────────────────────────
    """
    print(banner)
    
    # আপনার ব্যাকগ্রাউন্ড টাস্ক এবং পোলিং শুরু
    asyncio.create_task(check_vip_expiry()) # ব্যাকগ্রাউন্ড চেক শুরু
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[🌙] Bot stopped by Dark Himu.")

if __name__ == "__main__":
    asyncio.run(main())
