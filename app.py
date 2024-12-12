from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
import datetime
import calendar

app = Flask(__name__)
app.secret_key = 'your_secret_key'

ADMIN_EMAIL = "senderszymom@gmail.com"

EMAIL_USER = "zajeciastrona@gmail.com"  # Twój email
EMAIL_PASSWORD = "kkfp irfl trld poaa"  # Hasło aplikacji z Google
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def get_db_connection():
    conn = sqlite3.connect('rezerwacja_sesji.db')
    conn.row_factory = sqlite3.Row
    return conn


def send_email_to_admin(name, email, phone, message):
    # Funkcja wysyłająca email do admina (przykładowa konfiguracja Gmail + hasło aplikacji)
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header
    from email.utils import formataddr

    subject = "Wiadomość od klienta ze strony fotografii"
    body = f"Imię: {name}\nEmail: {email}\nTelefon: {phone}\n\nTreść:\n{message}"

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr(("Formularz Kontaktowy", EMAIL_USER))
    msg['To'] = ADMIN_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email został wysłany pomyślnie.")
    except Exception as e:
        print("Błąd wysyłania emaila:", e)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'contact':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            message = request.form.get('message')

            if not (name and email and phone and message):
                flash('Wszystkie pola w formularzu kontaktowym są wymagane.', 'danger')
            else:
                send_email_to_admin(name, email, phone, message)
                flash(f'Wiadomość została wysłana na email admina: {ADMIN_EMAIL}.', 'success')
            return redirect(url_for('home'))

        elif form_type == 'reserve':
            if not session.get('user_id'):
                flash('Musisz być zalogowany, aby zarezerwować termin.', 'danger')
                return redirect(url_for('login'))
            session_type = request.form.get('session_type')
            date = request.form.get('date')
            time = request.form.get('time')
            if not session_type or not date or not time:
                flash('Wszystkie pola rezerwacji są wymagane.', 'danger')
            else:
                conn = get_db_connection()
                conn.execute(
                    'INSERT INTO rezerwacje (uzytkownik_id, typ_sesji, data_rezerwacji, godzina) VALUES (?, ?, ?, ?)',
                    (session.get('user_id'), session_type, date, time))
                conn.commit()
                conn.close()
                flash('Twoja rezerwacja została złożona. Oczekuje na potwierdzenie.', 'success')
            return redirect(url_for('home'))

    # Wyświetlanie strony głównej
    portfolio = [
        {"title": "Reportaż ślubny", "img": "static/images/slub.jpg"},
        {"title": "Wydarzenia firmowe", "img": "static/images/firma.jpg"},
        {"title": "Reportaż ślubny", "img": "static/images/slub.jpg"},
        {"title": "Wydarzenia firmowe", "img": "static/images/firma.jpg"},
    ]

    now = datetime.date.today()
    current_year = now.year
    current_month = now.month

    # Pobieramy rezerwacje z bazy dla aktualnego miesiąca
    conn = get_db_connection()
    bookings = conn.execute(
        "SELECT typ_sesji, data_rezerwacji, godzina FROM rezerwacje WHERE strftime('%Y', data_rezerwacji) = ? AND strftime('%m', data_rezerwacji) = ?",
        (str(current_year), f"{current_month:02d}")
    ).fetchall()
    conn.close()

    reserved_days = set()
    bookings_by_day = {}

    for b in bookings:
        date_parts = b['data_rezerwacji'].split('-')
        if len(date_parts) == 3:
            d_year, d_month, d_day = date_parts
            d_day = int(d_day)
            reserved_days.add(d_day)
            if d_day not in bookings_by_day:
                bookings_by_day[d_day] = []
            bookings_by_day[d_day].append({
                "typ_sesji": b["typ_sesji"],
                "godzina": b["godzina"]
            })

    cal = calendar.monthcalendar(current_year, current_month)

    return render_template('index.html',
                           portfolio=portfolio,
                           current_year=current_year,
                           current_month=current_month,
                           calendar_matrix=cal,
                           reserved_days=reserved_days,
                           bookings_by_day=bookings_by_day)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('client_panel'))
        else:
            flash('Błędny login lub hasło!', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']

        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?',
                                     (username, email)).fetchone()
        if existing_user:
            flash('Taki użytkownik już istnieje lub email jest zajęty.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        conn.execute(
            'INSERT INTO users (username, password, imie, nazwisko, email, numer_telefonu, is_admin) VALUES (?, ?, ?, ?, ?, ?, 0)',
            (username, password, first_name, last_name, email, phone))
        conn.commit()
        conn.close()
        flash('Rejestracja przebiegła pomyślnie! Teraz możesz się zalogować.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Wylogowano pomyślnie!', 'success')
    return redirect(url_for('home'))


@app.route('/client_panel')
def client_panel():
    user_id = session.get('user_id')
    if not user_id:
        flash('Musisz się zalogować.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user['is_admin']:
        bookings = conn.execute('''
            SELECT r.*, u.email as user_email, u.numer_telefonu as user_phone 
            FROM rezerwacje r
            JOIN users u ON r.uzytkownik_id = u.id
        ''').fetchall()

        folders = conn.execute(
            'SELECT f.id AS folder_id, f.nazwa_folderu, f.link_do_folderu, u.email AS user_email, u.username AS user_username FROM foldery f JOIN users u ON f.uzytkownik_id = u.id').fetchall()
    else:
        bookings = conn.execute('''
            SELECT r.*, u.email as user_email, u.numer_telefonu as user_phone 
            FROM rezerwacje r
            JOIN users u ON r.uzytkownik_id = u.id
            WHERE u.id = ?
        ''', (user_id,)).fetchall()

        folders = conn.execute('SELECT * FROM foldery WHERE uzytkownik_id = ?', (user_id,)).fetchall()

    conn.close()

    return render_template('client_panel.html', user=user, bookings=bookings, folders=folders)


@app.route('/delete_booking', methods=['POST'])
def delete_booking():
    booking_id = request.form['booking_id']
    user_id = session.get('user_id')
    if not user_id:
        flash('Musisz być zalogowany.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    booking = conn.execute('SELECT * FROM rezerwacje WHERE id = ?', (booking_id,)).fetchone()
    if not booking:
        flash('Nie znaleziono takiej rezerwacji.', 'danger')
        conn.close()
        return redirect(url_for('client_panel'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user['is_admin'] or booking['uzytkownik_id'] == user_id:
        conn.execute('DELETE FROM rezerwacje WHERE id = ?', (booking_id,))
        conn.commit()
        conn.close()
        flash('Rezerwacja została usunięta.', 'success')
    else:
        conn.close()
        flash('Nie masz uprawnień do usunięcia tej rezerwacji.', 'danger')

    return redirect(url_for('client_panel'))


@app.route('/edit_booking', methods=['POST'])
def edit_booking():
    booking_id = request.form.get('booking_id')
    new_type = request.form.get('session_type')
    new_date = request.form.get('date')
    new_time = request.form.get('time')

    user_id = session.get('user_id')
    if not user_id:
        flash('Musisz być zalogowany.', 'danger')
        return redirect(url_for('login'))

    if not (new_type and new_date and new_time):
        flash('Wszystkie pola są wymagane do edycji.', 'danger')
        return redirect(url_for('client_panel'))

    conn = get_db_connection()
    booking = conn.execute('SELECT * FROM rezerwacje WHERE id = ?', (booking_id,)).fetchone()
    if not booking:
        flash('Nie znaleziono takiej rezerwacji.', 'danger')
        conn.close()
        return redirect(url_for('client_panel'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['is_admin'] or booking['uzytkownik_id'] == user_id:
        conn.execute('UPDATE rezerwacje SET typ_sesji = ?, data_rezerwacji = ?, godzina = ? WHERE id = ?',
                     (new_type, new_date, new_time, booking_id))
        conn.commit()
        conn.close()
        flash('Rezerwacja została zaktualizowana.', 'success')
    else:
        conn.close()
        flash('Nie masz uprawnień do edycji tej rezerwacji.', 'danger')

    return redirect(url_for('client_panel'))


@app.route('/add_folder', methods=['POST'])
def add_folder():
    if not session.get('is_admin'):
        flash('Tylko administrator może dodawać foldery.', 'danger')
        return redirect(url_for('client_panel'))

    email = request.form['email']
    folder_name = request.form['folder_name']
    folder_file = request.files['folder_file']

    if folder_file:
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        folder_path = os.path.join('uploads', folder_file.filename)
        folder_file.save(folder_path)

        conn = get_db_connection()
        user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            conn.execute('INSERT INTO foldery (uzytkownik_id, nazwa_folderu, link_do_folderu) VALUES (?, ?, ?)',
                         (user['id'], folder_name, folder_path))
            conn.commit()
            flash('Folder został dodany pomyślnie.', 'success')
        else:
            flash('Nie znaleziono użytkownika o podanym adresie e-mail.', 'danger')
        conn.close()

    return redirect(url_for('client_panel'))


@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    if not session.get('is_admin'):
        flash('Tylko administrator może usuwać foldery.', 'danger')
        return redirect(url_for('client_panel'))

    folder_id = request.form.get('folder_id')
    if not folder_id:
        flash('Brak ID folderu do usunięcia.', 'danger')
        return redirect(url_for('client_panel'))

    conn = get_db_connection()
    folder = conn.execute('SELECT * FROM foldery WHERE id = ?', (folder_id,)).fetchone()
    if not folder:
        conn.close()
        flash('Nie znaleziono folderu o podanym ID.', 'danger')
        return redirect(url_for('client_panel'))

    folder_path = folder['link_do_folderu']
    conn.execute('DELETE FROM foldery WHERE id = ?', (folder_id,))
    conn.commit()
    conn.close()

    if os.path.exists(folder_path):
        os.remove(folder_path)

    flash('Folder został usunięty.', 'success')
    return redirect(url_for('client_panel'))


@app.route('/edit_user', methods=['POST'])
def edit_user():
    user_id = session.get('user_id')
    if not user_id:
        flash('Musisz być zalogowany, aby edytować swoje dane.', 'danger')
        return redirect(url_for('login'))

    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    if not (first_name and last_name and email and phone):
        flash('Wszystkie pola są wymagane.', 'danger')
        return redirect(url_for('client_panel'))

    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id)).fetchone()
    if existing:
        flash('Podany email jest już zajęty przez innego użytkownika.', 'danger')
        conn.close()
        return redirect(url_for('client_panel'))

    conn.execute('UPDATE users SET imie = ?, nazwisko = ?, email = ?, numer_telefonu = ? WHERE id = ?',
                 (first_name, last_name, email, phone, user_id))
    conn.commit()
    conn.close()
    flash('Dane zostały zaktualizowane.', 'success')
    return redirect(url_for('client_panel'))


@app.route('/download_folder/<int:folder_id>')
def download_folder(folder_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Musisz być zalogowany, aby pobrać folder.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    folder = conn.execute('SELECT * FROM foldery WHERE id = ?', (folder_id,)).fetchone()
    if not folder:
        flash('Nie znaleziono takiego folderu.', 'danger')
        conn.close()
        return redirect(url_for('client_panel'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['is_admin'] or folder['uzytkownik_id'] == user_id:
        folder_path = folder['link_do_folderu']
        conn.close()
        if not os.path.exists(folder_path):
            flash('Plik nie istnieje na serwerze.', 'danger')
            return redirect(url_for('client_panel'))
        return send_file(folder_path, as_attachment=True)
    else:
        conn.close()
        flash('Nie masz uprawnień do pobrania tego folderu.', 'danger')
        return redirect(url_for('client_panel'))


if __name__ == '__main__':
    app.run(debug=True)
