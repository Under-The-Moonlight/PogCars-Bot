import sqlite3 as sq
import aiosqlite

db = sq.connect('tg.db')
cursor = db.cursor()


async def start_db(user_id):
    user = cursor.execute("SELECT * FROM User WHERE TelegramChatId = {key}".format(key=user_id)).fetchone()
    if not user:
        cursor.execute(f"INSERT INTO User (TelegramChatId) VALUES ()".format(key=user_id))
        db.commit()


async def show_service():
    cursor.execute("SELECT Name, Cost, Descriprion FROM ServiceTypes")
    services_info = []
    for row in cursor.fetchall():
        name, cost, desc = row
        service_str = f"Сервіс - {name}, Ціна - {cost}"
        if desc:
            service_str += f", Опис - {desc}"
        services_info.append(service_str)
    return "\n".join(services_info)


async def select_date():
    dates = cursor.execute("SELECT Date FROM Appointment WHERE UserId IS NULL OR UserId = ''").fetchall()
    text = ""
    for date in dates:
        escaped_date = date[0].replace('-', '\\-')  # Ескейпіть символ "-" в кожній даті
        text += '\n`' + escaped_date + '`'
    return text


async def choose_date(user_id, date):
    user = cursor.execute("SELECT Id FROM User WHERE TelegramChatId = {key}".format(key=user_id)).fetchone()

    return date


async def update_on_create(userId, appId, servId):
    cursor.execute(
        "INSERT INTO ServiceRecords (UserId, AppointmentID, ServiceTypeId, Status) VALUES (?, ?, ?, 'Active')",
        (userId, appId, servId))
    cursor.execute("UPDATE Appointment SET UserId = ? WHERE Id = ?", (userId, appId))
    db.commit()


async def get_service_name(service_name):
    cor_serv = cursor.execute("SELECT Name FROM ServiceTypes WHERE Name = ?", (service_name,)).fetchone()
    if cor_serv is not None:
        return cor_serv
    else:
        return False


async def get_appointmentId(app):
    appid = cursor.execute("SELECT Id FROM Appointment WHERE Date = ?", (app,)).fetchone()
    return appid[0]


async def get_history(user_id):
    user_history = cursor.execute("""SELECT 
        ServiceRecords.Id,
        A.Date AS AppointmentDate, 
        ST.Name AS ServiceTypeName, 
        ServiceRecords.Status
    FROM 
        ServiceRecords
    JOIN 
        Appointment A ON ServiceRecords.AppointmentID = A.Id
    JOIN 
        ServiceTypes ST ON ServiceRecords.ServiceTypeId = ST.Id
    WHERE 
        ServiceRecords.UserId = (SELECT Id FROM User WHERE TelegramChatId = ?);""", (user_id,))
    history_output = []
    for record in user_history:
        # Ескейпінг спеціальних символів для Markdown V2
        service_type_name = record[2].replace('-', '\\-').replace('.', '\\.').replace('(', '\\(').replace(')',
                                                                                                          '\\)').replace(
            '+', '\\+').replace('=', '\\=').replace('!', '\\!')
        status = record[3].replace('-', '\\-').replace('.', '\\.').replace('(', '\\(').replace(')', '\\)').replace('+',
                                                                                                                   '\\+').replace(
            '=', '\\=').replace('!', '\\!')

        history_output.append(f"ID: {record[0]}, Дата: `{record[1]}`, Сервіс: {service_type_name}, Статус: {status}")

    return '\n'.join(history_output)


async def cmd_service_list():
    services = cursor.execute("SELECT Id, Service FROM ServiceTypes").fetchall()
    return '\n'.join(service[0] for service in services)


async def get_service_id(name):
    serviceid = cursor.execute("SELECT Id FROM ServiceTypes WHERE Name=?", (name,)).fetchone()
    if serviceid:
        return serviceid[0]
    else:
        return None

async def get_user_id(tgid):
    userId = cursor.execute("SELECT Id FROM User WHERE TelegramChatId=?", (tgid,)).fetchone()
    return userId[0]


async def get_records_id(id, tg_id):
    is_exist = cursor.execute(
        "SELECT Id FROM ServiceRecords WHERE UserId = (SELECT Id FROM User WHERE TelegramChatId = ?)",
        (tg_id,)).fetchone()
    if is_exist[0] is not None:
        return True
    else:
        return False


async def update_date(user_id, date, new_date):
    appointment_id = cursor.execute("SELECT Id FROM Appointment WHERE Date = ?", (date,)).fetchone()
    new_appointment_id = cursor.execute("SELECT Id FROM Appointment WHERE Date = ?", (new_date,)).fetchone()
    userid = await get_user_id(user_id)
    if appointment_id and new_appointment_id:
        # Оновити AppointmentId в ServiceRecords на нове значення
        cursor.execute("""
                            UPDATE ServiceRecords
                            SET AppointmentID = ?
                            WHERE UserId = ? AND AppointmentID = ? AND Status = 'Active'
                        """, (new_appointment_id[0], userid, appointment_id[0]))

        # Оновити записи в Appointment
        cursor.execute("UPDATE Appointment SET UserId = NULL WHERE Id = ?", (appointment_id[0],))
        cursor.execute("UPDATE Appointment SET UserId = ? WHERE Id = ?", (userid, new_appointment_id[0]))

        # Застосування змін
        db.commit()


async def delete_date(id, date):
    appointment_id = cursor.execute("SELECT Id FROM Appointment WHERE Date = ?", (date,)).fetchone()
    userid = await get_user_id(id)
    if userid is not None and appointment_id is not None:
        # Переконатися, що appointment_id - це int
        appointment_id_int = appointment_id[0] if isinstance(appointment_id, tuple) else appointment_id

        # Виконати запит на видалення
        cursor.execute("DELETE FROM ServiceRecords WHERE UserId = ? AND AppointmentId = ? AND Status = 'Active'",
                       (userid, appointment_id_int))
        cursor.execute("UPDATE Appointment SET UserId = NULL WHERE UserId = ?", (userid, ))

        # Застосування змін
        db.commit()
        return True
    else:
        return False

async def calculate_services(service_list):
    query = "SELECT SUM(Cost) FROM ServiceTypes WHERE Name IN ({})".format(
        ", ".join(["?"] * len(service_list)))
    cursor.execute(query, service_list)
    result = cursor.fetchone()
    return result[0] if result[0] is not None else 0


async def info_out(user_id, date):
    norm_id = await get_user_id(user_id)
    query = """
    SELECT 
        SR.Id, 
        A.Date, 
        ST.Name, 
        ST.Descriprion, 
        SR.Status, 
        ST.Cost
    FROM 
        ServiceRecords SR
    JOIN 
        Appointment A ON SR.AppointmentID = A.Id
    JOIN 
        ServiceTypes ST ON SR.ServiceTypeId = ST.Id
    WHERE 
        SR.UserId = ? AND A.Date = ?
    """
    cursor.execute(query, (norm_id, date))
    record = cursor.fetchone()

    if record:
        id, date, service_name, desc, status, cost = record
        return f"Id - {id}\nДата - {date}\nПослуги - {service_name}\nОпис - {desc}\nСтатус - {status}\nЦіна - {cost}"
    else:
        return "Запис не знайдено."


async def admin_check(user_id):
    admin_approve = cursor.execute(f"SELECT AdminRules FROM User WHERE TelegramChatId = {user_id}").fetchone()
    if admin_approve[0] == "True":
        return True
    else:
        return False


async def add_phone(user_id, message):
    query = "UPDATE User SET Phone = ? WHERE TelegramChatId = ?"
    cursor.execute(query, (message, user_id))
    db.commit()


async def add_name(user_id, message):
    query = "UPDATE User SET Name = ? WHERE TelegramChatId = ?"
    cursor.execute(query, (message, user_id))
    db.commit()


async def insert_new_date(message):
    querry = "INSERT INTO Appointment (Date, UserId) VALUES(?, NULL)"
    cursor.execute(querry, (message,))
    db.commit()


async def get_all_records():
    all_history = cursor.execute("""SELECT 
        ServiceRecords.Id,
        A.Date AS AppointmentDate, 
        ST.Name AS ServiceTypeName, 
        ServiceRecords.Status
    FROM 
        ServiceRecords
    JOIN 
        Appointment A ON ServiceRecords.AppointmentID = A.Id
    JOIN 
        ServiceTypes ST ON ServiceRecords.ServiceTypeId = ST.Id;""")

    # Формування виводу для кожного запису
    return '\n'.join(
        f"ID: {record[0]}, Дата: {record[1]}, Сервіс: {record[2]}, Статус: {record[3]}" for record in all_history)


async def get_all_users():
    all_users = cursor.execute("SELECT Id, TelegramChatId, Phone, Name FROM User WHERE AdminRules != 'True';")
    return '\n'.join(
        f"ID: {record[0]}, TgId: {record[1]}, Номер: {record[2]}, Ім'я: {record[3]}" for record in all_users)


async def get_record_id(msg):
    recordid = cursor.execute("SELECT Id FROM ServiceRecords WHERE Id = ?", (msg,)).fetchone()
    return recordid[0]


async def update_record_canceld(msg):
    is_alive = get_record_id(msg)
    if is_alive:
        cursor.execute("UPDATE ServiceRecords SET Status= 'Canceled' WHERE Id = ?", (msg,))
        db.commit()
        return True
    else:
        return False


async def get_tgid_by_recordsid(msg):
    userid = cursor.execute(
        "SELECT U.TelegramChatId FROM User U JOIN ServiceRecords SR ON U.Id = SR.UserId WHERE SR.Id = ?;",
        (msg,)).fetchone()
    return userid[0]


async def date_by_appid(msg):
    res = cursor.execute("SELECT Date From Appointment WHERE Id = ?", (msg, )).fetchone()
    return res[0]