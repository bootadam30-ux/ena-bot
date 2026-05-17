# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = [
        [KeyboardButton(text="My Profile"), KeyboardButton(text="VIP Membership")],
        [KeyboardButton(text="Main Group"), KeyboardButton(text="Support")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_start_kb():
    kb = [
        [KeyboardButton(text="My Profile")],
        [KeyboardButton(text="Admin Panel")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_sub_menu():
    kb = [
        [KeyboardButton(text="Stats"), KeyboardButton(text="Credits")],
        [KeyboardButton(text="VIP Update"), KeyboardButton(text="Broadcast")],
        [KeyboardButton(text="User Ban")],
        [KeyboardButton(text="Back to Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# আপনার রিকোয়েস্ট অনুযায়ী ওয়াচ বাটন এবং ব্যাকআপ চ্যানেল বাটন পাশাপাশি সেট করা হয়েছে
def watch_button():
    kb = [
        [
            InlineKeyboardButton(text="🎬 Watch Now", callback_data="watch_video"),
            InlineKeyboardButton(text="📢 Backup Channel", url="https://t.me/+kWDCNyfJqO41NTU1")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def vip_keyboard():
    kb = [[InlineKeyboardButton(text="📩 Buy Now / মেম্বারশিপ কিনুন", url="https://t.me/leo20608")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def post_confirm_kb():
    kb = [[InlineKeyboardButton(text="✅ Post Video", callback_data="post_confirm")],
          [InlineKeyboardButton(text="❌ Cancel", callback_data="post_cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)
