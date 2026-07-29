import sqlite3
from threading import Lock

DB_NAME = "bot.db"

lock = Lock()


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            joined_at TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats(
            key TEXT PRIMARY KEY,
            value INTEGER
        )
        """)

        self.conn.commit()

    # ===========================
    # المستخدمون
    # ===========================

    def add_user(self, user):

        with lock:

            self.cursor.execute("""

            INSERT OR IGNORE INTO users

            VALUES(
                ?,
                ?,
                ?,
                datetime('now')
            )

            """,

            (

                user.id,

                user.first_name,

                user.username

            ))

            self.conn.commit()

    def get_users(self):

        self.cursor.execute(

            "SELECT user_id FROM users"

        )

        return [

            x[0]

            for x in self.cursor.fetchall()

        ]

    def total_users(self):

        self.cursor.execute(

            "SELECT COUNT(*) FROM users"

        )

        return self.cursor.fetchone()[0]

    # ===========================
    # الرسائل
    # ===========================

    def save_message(

        self,

        user_id,

        role,

        content

    ):

        with lock:

            self.cursor.execute("""

            INSERT INTO messages(

                user_id,

                role,

                content,

                created_at

            )

            VALUES(

                ?,

                ?,

                ?,

                datetime('now')

            )

            """,

            (

                user_id,

                role,

                content

            ))

            self.conn.commit()

    def get_history(

        self,

        user_id,

        limit=10

    ):

        self.cursor.execute("""

        SELECT

            role,

            content

        FROM messages

        WHERE user_id=?

        ORDER BY id DESC

        LIMIT ?

        """,

        (

            user_id,

            limit

        ))

        rows = self.cursor.fetchall()

        rows.reverse()

        history = []

        for role, content in rows:

            history.append({

                "role": role,

                "content": content

            })

        return history

    # ===========================
    # الإحصائيات
    # ===========================

    def increase(

        self,

        key

    ):

        self.cursor.execute("""

        INSERT INTO stats(

            key,

            value

        )

        VALUES(

            ?,

            1

        )

        ON CONFLICT(key)

        DO UPDATE

        SET value=value+1

        """,

        (

            key,

        ))

        self.conn.commit()

    def get_stat(

        self,

        key

    ):

        self.cursor.execute(

            "SELECT value FROM stats WHERE key=?",

            (

                key,

            )

        )

        row = self.cursor.fetchone()

        if row:

            return row[0]

        return 0


db = Database()
