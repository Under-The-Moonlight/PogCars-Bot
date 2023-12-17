import sqlite3 as sq
import aiosqlite


db = sq.connect('tg.db')
cursor = db.cursor()



async def cmd_start_db(user_id):
    user = cursor.execute("SELECT * FROM User WHERE TelegramChatId = {key}".format(key=user_id)).fetchone()
    if not user:
        cursor.execute("INSERT INTO User (TelegramChatId) VALUES ({key})".format(key=user_id))
        db.commit()

async def cmd_show_service():
    cursor.execute("SELECT Name, Cost, Descriprion FROM ServiceTypes")
    services_info = []
    for row in cursor.fetchall():
        name, cost, desc = row
        service_str = f"Сервіс - {name}, Ціна - {cost}"
        if desc:
            service_str += f", Опис - {desc}"
        services_info.append(service_str)
    return "\n".join(services_info)