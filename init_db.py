import sqlite3

connection = sqlite3.connect('rezerwacja_sesji.db')
cursor = connection.cursor()

# Tworzenie tabel
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    imie TEXT,
    nazwisko TEXT,
    email TEXT UNIQUE NOT NULL,
    numer_telefonu TEXT,
    is_admin BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rezerwacje (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id INTEGER NOT NULL,
    typ_sesji TEXT NOT NULL,
    data_rezerwacji TEXT NOT NULL,
    godzina TEXT NOT NULL,
    FOREIGN KEY (uzytkownik_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS foldery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id INTEGER NOT NULL,
    nazwa_folderu TEXT NOT NULL,
    link_do_folderu TEXT NOT NULL,
    FOREIGN KEY (uzytkownik_id) REFERENCES users (id) ON DELETE CASCADE
);

""")

# Dodanie użytkownika admina
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, imie, nazwisko, email, numer_telefonu, is_admin)
VALUES ('admin', 'admin123', 'Admin', 'User', 'admin@example.com', '123456789', 1)
""")

connection.commit()
connection.close()
print("Baza danych została zainicjalizowana.")
