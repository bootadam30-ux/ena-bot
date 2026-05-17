# database.py
import motor.motor_asyncio
from datetime import datetime, timedelta
from config import MONGO_URI, DAILY_FREE_CREDITS

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.premium_bot_db
users_col = db.users

async def get_user(user_id):
    return await users_col.find_one({"user_id": user_id})

async def add_user(user_id, name):
    user_data = {
        "user_id": user_id,
        "name": name,
        "credits": DAILY_FREE_CREDITS,
        "membership": "Free",
        "referrals": 0,
        "join_date": datetime.now()
    }
    await users_col.insert_one(user_data)
    return user_data

async def get_total_users():
    return await users_col.count_documents({})

async def get_all_users():
    return await users_col.find().to_list(length=None)

async def update_credits(user_id, amount):
    await users_col.update_one({"user_id": user_id}, {"$inc": {"credits": amount}})

async def set_vip(user_id, days):
    expire_date = datetime.now() + timedelta(days=days)
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"membership": "VIP", "vip_expire": expire_date}}
    )
