import sqlite3 as sq
import aiosqlite

db = sq.connect('tg.db')
cursor = db.cursor()

async def db_start():
    await cursor.execute('''
    CREATE TABLE IF NOT EXISTS ServiceTypes (
    ServiceTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    ServiceName TEXT NOT NULL,
    Description TEXT,
    StandardCost REAL
    )
    ''')

    await cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    TelegramChatID INTEGER UNIQUE
    )
    ''')
    # Створення таблиці Appointments
    await cursor.execute('''
    CREATE TABLE IF NOT EXISTS Appointments (
        AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
        DateTime DATETIME NOT NULL,
        UserID INTEGER,
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
    )
    ''')

    # Створення таблиці ServiceRecords
    await cursor.execute('''
    CREATE TABLE IF NOT EXISTS ServiceRecords (
        RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        AppointmentID INTEGER NOT NULL,
        ServiceTypeID INTEGER NOT NULL,
        ServiceDetails TEXT,
        DateOfService TEXT NOT NULL,
        Cost REAL,
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
        FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID),
        FOREIGN KEY (ServiceTypeID) REFERENCES ServiceTypes(ServiceTypeID)
    )
    ''')

    await db.commit()
    print("db created")


async def cmd_start_db(user_id):
    user = cursor.execute("SELECT * FROM Users WHERE TelegramChatID == {key}".format(key=user_id)).fetchone()
    if not user:
        cursor.execute("INSERT TelegramChatID INTO Users VALUES {key}".format(key=user_id))
        db.commit()