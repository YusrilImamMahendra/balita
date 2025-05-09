from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, jsonify, make_response, current_app, Response
)
from collections import defaultdict, Counter
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from models.knn_lvq import KNN_LVQ
from datetime import datetime
from pathlib import Path
import os
import pdfkit
import csv
import pandas as pd
from dateutil.relativedelta import relativedelta
from flask_login import login_required
import datetime

# =============================================
# KONFIGURASI APLIKASI
# =============================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key'
app.config['DATABASE'] = 'gizi_balita.db'


# =============================================
# FILTER TEMPLATE
# =============================================

@app.template_filter('datetime_format')
def datetime_format_filter(value):
    value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    """Filter untuk memformat tanggal dan waktu dalam template Jinja2"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    return value.strftime('%d-%m-%Y %H:%M')

# =============================================
# FUNGSI DATABASE
# =============================================

def get_db():
    """Membuat koneksi database baru"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inisialisasi database dengan struktur dan data awal"""
    db_path = app.config['DATABASE']
    if Path(db_path).exists():
        Path(db_path).unlink()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        
        # Buat tabel-tabel
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS balita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            tanggal_lahir DATE NOT NULL,
            jenis_kelamin TEXT NOT NULL CHECK (jenis_kelamin IN ('L', 'P')),
            nama_ortu TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS pengukuran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balita_id INTEGER NOT NULL,
            tanggal_ukur DATE NOT NULL,
            berat_badan REAL NOT NULL CHECK (berat_badan > 0),
            tinggi_badan REAL NOT NULL CHECK (tinggi_badan > 0),
            lingkar_lengan REAL NOT NULL CHECK (lingkar_lengan > 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (balita_id) REFERENCES balita (id) ON DELETE CASCADE
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS klasifikasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pengukuran_id INTEGER UNIQUE NOT NULL,
            status_gizi TEXT NOT NULL CHECK (status_gizi IN ('normal', 'kurang', 'lebih', 'buruk')),
            tanggal_klasifikasi DATE NOT NULL,
            FOREIGN KEY (pengukuran_id) REFERENCES pengukuran (id) ON DELETE CASCADE
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS dataset_training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature1 REAL NOT NULL,
            feature2 REAL NOT NULL,
            feature3 REAL NOT NULL,
            target TEXT NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS parameter_knn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nilai_k INTEGER NOT NULL CHECK (nilai_k > 0),
            bobot_berat REAL NOT NULL CHECK (bobot_berat >= 0 AND bobot_berat <= 1),
            bobot_tinggi REAL NOT NULL CHECK (bobot_tinggi >= 0 AND bobot_tinggi <= 1),
            bobot_lila REAL NOT NULL CHECK (bobot_lila >= 0 AND bobot_lila <= 1),
            bobot_umur REAL NOT NULL CHECK (bobot_umur >= 0 AND bobot_umur <= 1),
            bobot_jk REAL NOT NULL CHECK (bobot_jk >= 0 AND bobot_jk <= 1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT bobot_valid CHECK (
            ABS((bobot_berat + bobot_tinggi + bobot_lila + bobot_umur + bobot_jk) - 1.0) < 0.0001
            )
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS parameter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter_id INTEGER NOT NULL,
            changed_by INTEGER NOT NULL,
            nilai_k INTEGER NOT NULL,
            bobot_berat REAL NOT NULL,
            bobot_tinggi REAL NOT NULL,
            bobot_lila REAL NOT NULL,
            bobot_umur REAL NOT NULL,
            bobot_jk REAL NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parameter_id) REFERENCES parameter_knn (id),
            FOREIGN KEY (changed_by) REFERENCES users (id)
        )
        ''')

        # Insert data awal
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
        hashed_pw = generate_password_hash(admin_password)
        c.execute('''
            INSERT OR IGNORE INTO users (username, password, nama_lengkap, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hashed_pw, 'Administrator', 'admin'))
        
        c.execute('''
            INSERT OR IGNORE INTO parameter_knn 
            (nilai_k, bobot_berat, bobot_tinggi, bobot_lila, bobot_umur, bobot_jk)
            VALUES (3, 0.35, 0.30, 0.15, 0.15, 0.05)
        ''')
        
        conn.commit()
        print("✅ Database berhasil diinisialisasi")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inisialisasi database: {str(e)}")
        raise
    finally:
        conn.close()

# =============================================
# DEKORATOR
# =============================================

def login_required(f):
    """Dekorator untuk memeriksa apakah pengguna telah login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Dekorator untuk memeriksa apakah pengguna adalah admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Akses terbatas untuk admin', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# =============================================
# ROUTES
# =============================================

# =============================================
# ROUTE AUTENTIKASI
# =============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Nama pengguna dan kata sandi harus diisi.', 'danger')
            return redirect(url_for('login'))
        conn = None
        try:
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Login berhasil.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Nama pengguna atau kata sandi salah.', 'danger')
        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('auth/auth.html', page_mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        
        if not username or not password or not nama_lengkap:
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('register'))
        
        conn = None  # Pastikan conn diinisialisasi
        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO users (username, password, nama_lengkap, role)
                VALUES (?, ?, ?, ?)
            ''', (username, generate_password_hash(password), nama_lengkap, 'user'))
            conn.commit()
            flash('Registrasi berhasil! Silakan login', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan', 'danger')
        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('auth/auth.html', page_mode='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))

# =============================================
# ROUTE DASHBOARD
# =============================================

@app.route('/')
@login_required
def dashboard():
    with get_db() as conn:
        stats = {
            'balita_count': conn.execute("SELECT COUNT(*) FROM balita").fetchone()[0],
            'status_gizi': conn.execute('''
                SELECT status_gizi, COUNT(*) as jumlah 
                FROM klasifikasi 
                GROUP BY status_gizi
            ''').fetchall()
        }

        # Data tren status gizi selama 6 bulan terakhir
        trend_data = conn.execute('''
            SELECT strftime('%Y-%m', tanggal_ukur) as bulan, 
                   status_gizi, COUNT(*) as jumlah
            FROM pengukuran p
            JOIN klasifikasi k ON p.id = k.pengukuran_id
            WHERE p.tanggal_ukur >= date('now', '-6 months')
            GROUP BY bulan, status_gizi
            ORDER BY bulan
        ''').fetchall()

        # Format data untuk Chart.js
        stats_gizi = {'normal':0, 'kurang':0, 'buruk':0}
        for row in stats['status_gizi']:
            stats_gizi[row['status_gizi']] = row['jumlah']

        # Data pengukuran terbaru (misal 5 terakhir)
        pengukuran_terbaru = conn.execute('''
            SELECT b.nama, p.tanggal_ukur, p.berat_badan, p.tinggi_badan, k.status_gizi
            FROM pengukuran p
            JOIN balita b ON p.balita_id = b.id
            JOIN klasifikasi k ON p.id = k.pengukuran_id
            ORDER BY p.tanggal_ukur DESC
            LIMIT 5
        ''').fetchall()

    return render_template(
        'dashboard.html',
        balita_count=stats['balita_count'],
        stats_gizi=stats_gizi,
        pengukuran_terbaru=pengukuran_terbaru
    )
    
# ROUTE KELOLA USER
@app.route('/user')
@admin_required
def kelola_user():
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('user/index.html', users=users)

@app.route('/user/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_user():
    if request.method == 'POST':
        username = request.form['username']
        nama_lengkap = request.form['nama_lengkap']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, nama_lengkap, password, role) VALUES (?, ?, ?, ?)', 
                         (username, nama_lengkap, password, role))
            conn.commit()
            flash('User berhasil ditambah', 'success')
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan', 'danger')
        conn.close()
        return redirect(url_for('kelola_user'))
    return render_template('user/tambah.html')

@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        username = request.form['username']
        nama_lengkap = request.form['nama_lengkap']
        role = request.form['role']
        if request.form['password']:
            password = generate_password_hash(request.form['password'])
            conn.execute('UPDATE users SET username=?, nama_lengkap=?, password=?, role=? WHERE id=?',
                         (username, nama_lengkap, password, role, id))
        else:
            conn.execute('UPDATE users SET username=?, nama_lengkap=?, role=? WHERE id=?',
                         (username, nama_lengkap, role, id))
        conn.commit()
        conn.close()
        flash('User berhasil diupdate', 'success')
        return redirect(url_for('kelola_user'))
    conn.close()
    return render_template('user/edit.html', user=user)

@app.route('/user/hapus/<int:id>', methods=['POST'])
@admin_required
def hapus_user(id):
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('User berhasil dihapus', 'success')
    return redirect(url_for('kelola_user'))

# =============================================
# ROUTE MANAJEMEN BALITA
# =============================================

@app.route('/balita')
@login_required
def data_balita():
    """Endpoint untuk melihat data balita"""
    with get_db() as conn:
        balita = conn.execute('''
            SELECT b.*, 
                   (SELECT COUNT(*) FROM pengukuran WHERE balita_id = b.id) as jumlah_pengukuran
            FROM balita b
            ORDER BY b.nama
        ''').fetchall()
    return render_template('balita/data.html', balita=balita)

@app.route('/balita/tambah', methods=['GET', 'POST'])
@login_required
def tambah_balita():
    """Menambahkan data balita baru ke dalam database"""
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '')
        jenis_kelamin = request.form.get('jenis_kelamin', '')
        nama_ortu = request.form.get('nama_ortu', '').strip()

        # Validasi input
        if not all([nama, tanggal_lahir, jenis_kelamin, nama_ortu]):
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('tambah_balita'))

        with get_db() as conn:
            try:
                conn.execute(
                    'INSERT INTO balita (nama, tanggal_lahir, jenis_kelamin, nama_ortu) VALUES (?, ?, ?, ?)',
                    (nama, tanggal_lahir, jenis_kelamin, nama_ortu)
                )
                conn.commit()
                flash('Data balita berhasil ditambahkan', 'success')
                return redirect(url_for('data_balita'))
            except Exception as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'danger')

    return render_template('balita/tambah.html')

@app.route('/balita/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_balita(id):
    conn = get_db()
    
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '')
        jenis_kelamin = request.form.get('jenis_kelamin', '')
        nama_ortu = request.form.get('nama_ortu', '').strip()
        
        if not all([nama, tanggal_lahir, jenis_kelamin, nama_ortu]):
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('edit_balita', id=id))
        
        try:
            conn.execute('''
                UPDATE balita 
                SET nama = ?, tanggal_lahir = ?, jenis_kelamin = ?, nama_ortu = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (nama, tanggal_lahir, jenis_kelamin, nama_ortu, id))
            conn.commit()
            flash('Data balita berhasil diupdate', 'success')
            return redirect(url_for('data_balita'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()
    
    balita = conn.execute('SELECT * FROM balita WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not balita:
        flash('Data balita tidak ditemukan', 'danger')
        return redirect(url_for('data_balita'))
    
    return render_template('balita/edit.html', balita=balita)

@app.route('/balita/hapus/<int:id>')
@login_required
def hapus_balita(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM balita WHERE id = ?', (id,))
        conn.commit()
        flash('Data balita berhasil dihapus', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('data_balita'))
# =============================================
# ROUTE MANAJEMEN PENGUKURAN
# =============================================

@app.route('/pengukuran')
@login_required
def data_pengukuran():
    conn = get_db()
    pengukuran = conn.execute('''
        SELECT p.*, b.nama as nama_balita, k.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        LEFT JOIN klasifikasi k ON p.id = k.pengukuran_id
        ORDER BY p.tanggal_ukur DESC
    ''').fetchall()
    conn.close()
    return render_template('pengukuran/data.html', pengukuran=pengukuran)

def hitung_status_gizi(berat_badan, tinggi_badan, lingkar_lengan):
    if lingkar_lengan < 11.5:
        return 'buruk'
    elif lingkar_lengan < 12.5:
        return 'kurang'
    else:
        return 'normal'

@app.route('/pengukuran/tambah', methods=['GET', 'POST'])
@login_required
def tambah_pengukuran():
    if request.method == 'POST':
        balita_id = request.form.get('balita_id', '')
        berat_badan = request.form.get('berat_badan', '')
        tinggi_badan = request.form.get('tinggi_badan', '')
        lingkar_lengan = request.form.get('lingkar_lengan', '')

        # Validasi input
        if not all([balita_id, berat_badan, tinggi_badan, lingkar_lengan]):
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('tambah_pengukuran'))

        try:
            # Konversi input ke tipe data yang sesuai
            berat_badan = float(berat_badan)
            tinggi_badan = float(tinggi_badan)
            lingkar_lengan = float(lingkar_lengan)

            # Operasi database
            with get_db() as conn:
                balita = conn.execute(
                    'SELECT tanggal_lahir, jenis_kelamin FROM balita WHERE id = ?', 
                    (balita_id,)
                ).fetchone()

                if not balita:
                    flash('Data balita tidak ditemukan', 'danger')
                    return redirect(url_for('tambah_pengukuran'))

                # Prediksi status gizi (contoh placeholder)
                status_gizi = hitung_status_gizi(berat_badan, tinggi_badan, lingkar_lengan)

                # Simpan data pengukuran
                conn.execute('''
                    INSERT INTO pengukuran 
                    (balita_id, tanggal_ukur, berat_badan, tinggi_badan, lingkar_lengan)
                    VALUES (?, date('now'), ?, ?, ?)
                ''', (balita_id, berat_badan, tinggi_badan, lingkar_lengan))

                pengukuran_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

                # Simpan hasil klasifikasi
                conn.execute('''
                    INSERT INTO klasifikasi 
                    (pengukuran_id, status_gizi, tanggal_klasifikasi)
                    VALUES (?, ?, date('now'))
                ''', (pengukuran_id, status_gizi))

                conn.commit()
                flash(f'Pengukuran berhasil disimpan. Status gizi: {status_gizi}', 'success')
                return redirect(url_for('data_pengukuran'))

        except ValueError:
            flash('Input tidak valid. Pastikan angka yang dimasukkan benar', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    # Render form tambah pengukuran
    with get_db() as conn:
        balita = conn.execute('SELECT id, nama FROM balita ORDER BY nama').fetchall()
    return render_template('pengukuran/tambah.html', balita=balita)

@app.route('/pengukuran/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_pengukuran(id):
    conn = get_db()
    
    if request.method == 'POST':
        berat_badan = request.form.get('berat_badan', '')
        tinggi_badan = request.form.get('tinggi_badan', '')
        lingkar_lengan = request.form.get('lingkar_lengan', '')
        
        if not all([berat_badan, tinggi_badan, lingkar_lengan]):
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('edit_pengukuran', id=id))
        
        try:
            # Konversi ke float
            berat_badan = float(berat_badan)
            tinggi_badan = float(tinggi_badan)
            lingkar_lengan = float(lingkar_lengan)
            
            conn.execute('''
                UPDATE pengukuran 
                SET berat_badan = ?, tinggi_badan = ?, lingkar_lengan = ?
                WHERE id = ?
            ''', (berat_badan, tinggi_badan, lingkar_lengan, id))
            
            # Update klasifikasi jika diperlukan
            # ...
            
            conn.commit()
            flash('Data pengukuran berhasil diupdate', 'success')
            return redirect(url_for('data_pengukuran'))
        except ValueError:
            flash('Input tidak valid. Pastikan angka yang dimasukkan benar', 'danger')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            conn.close()
    
    pengukuran = conn.execute('''
        SELECT p.*, b.nama, b.tanggal_lahir, b.jenis_kelamin
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    conn.close()
    
    if not pengukuran:
        flash('Data pengukuran tidak ditemukan', 'danger')
        return redirect(url_for('data_pengukuran'))
    
    return render_template('pengukuran/edit.html', pengukuran=pengukuran)

@app.route('/pengukuran/hapus/<int:id>')
@login_required
def hapus_pengukuran(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM pengukuran WHERE id = ?', (id,))
        conn.execute('DELETE FROM klasifikasi WHERE pengukuran_id = ?', (id,))
        conn.commit()
        flash('Data pengukuran berhasil dihapus', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('data_pengukuran'))

# =============================================
# ROUTER LAPORAN
# =============================================

@app.route('/laporan')
def laporan():
    conn = get_db()
    data = conn.execute('''
        SELECT b.nama, p.tanggal_ukur, p.berat_badan, p.tinggi_badan, p.lingkar_lengan, k.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        JOIN klasifikasi k ON p.id = k.pengukuran_id
        ORDER BY p.tanggal_ukur DESC
    ''').fetchall()
    conn.close()

    # Ubah rows ke list of dict agar mudah manipulasi
    data = [dict(row) for row in data]

    # Mapping warna badge status gizi
    def get_status_color(status):
        if status == 'normal':
            return 'success'
        elif status == 'kurang':
            return 'warning'
        elif status == 'buruk':
            return 'danger'
        else:
            return 'secondary'

    for row in data:
        row['status_color'] = get_status_color(row['status_gizi'])

    # --- Chart Data ---
    # Grouping jumlah status gizi per tanggal
    trend = defaultdict(lambda: Counter())
    for row in data:
        tgl = row['tanggal_ukur']
        status = row['status_gizi']
        trend[tgl][status] += 1

    # List tanggal diurutkan
    labels = sorted(trend.keys())

    # Daftar status & warna chart
    status_list = ['normal', 'kurang', 'buruk']
    warna = {'normal': 'green', 'kurang': 'orange', 'buruk': 'red'}

    datasets = []
    for status in status_list:
        datasets.append({
            'label': status.title(),
            'data': [trend[tgl][status] for tgl in labels],
            'borderColor': warna[status],
            'fill': False
        })

    chart_data = {
        'labels': labels,
        'datasets': datasets
    }

    return render_template('laporan/index.html', data=data, chart_data=chart_data)

@app.route('/laporan/pdf')
@login_required
def laporan_pdf():
    conn = get_db()
    data = conn.execute('''
        SELECT b.nama, p.tanggal_ukur, p.berat_badan, p.tinggi_badan, p.lingkar_lengan, k.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        JOIN klasifikasi k ON p.id = k.pengukuran_id
        ORDER BY p.tanggal_ukur DESC
    ''').fetchall()
    conn.close()
    rendered = render_template('laporan/pdf_template.html', data=data)
    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=laporan.pdf'
    return response

@app.route('/laporan/excel')
@login_required
def laporan_excel():
    conn = get_db()
    data = conn.execute('''
        SELECT b.nama, p.tanggal_ukur, p.berat_badan, p.tinggi_badan, p.lingkar_lengan, k.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        JOIN klasifikasi k ON p.id = k.pengukuran_id
        ORDER BY p.tanggal_ukur DESC
    ''').fetchall()
    conn.close()

    # Buat isi file excel (CSV sederhana)
    import csv
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nama', 'Tanggal Ukur', 'Berat Badan', 'Tinggi Badan', 'Lingkar Lengan', 'Status Gizi'])
    for row in data:
        writer.writerow([row['nama'], row['tanggal_ukur'], row['berat_badan'], row['tinggi_badan'], row['lingkar_lengan'], row['status_gizi']])
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=laporan_gizi_balita.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

@app.route('/laporan/cetak')
@login_required
def cetak_laporan():
    conn = get_db()
    data = conn.execute('''
        SELECT b.nama, p.tanggal_ukur, p.berat_badan, p.tinggi_badan, p.lingkar_lengan, k.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        JOIN klasifikasi k ON p.id = k.pengukuran_id
        ORDER BY p.tanggal_ukur DESC
    ''').fetchall()
    conn.close()
    if data is None:
        data = []
    return render_template('laporan/cetak.html', data=data)

@app.route('/cetak_pdf')
def cetak_pdf():
    # Data yang ingin dikirim ke template (opsional)
    data = {
        "judul": "Contoh Laporan",
        "items": ["Item 1", "Item 2", "Item 3"]
    }
    # Render template HTML ke string
    rendered = render_template("laporan.html", data=data)
    # Konfigurasi path wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    # Generate PDF dari HTML string
    pdf = pdfkit.from_string(rendered, False, configuration=config)
    # Return sebagai file PDF ke browser
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=laporan.pdf"})

# =============================================
# ROUTE PARAMETER KNN (ADMIN ONLY)
# =============================================

@app.route('/admin/parameter')
@admin_required
def parameter():
    conn = get_db()
    try:
        params = conn.execute('SELECT * FROM parameter_knn').fetchone()
        history = conn.execute('''
            SELECT p.*, u.username 
            FROM parameter_history p
            JOIN users u ON p.changed_by = u.id
            ORDER BY p.changed_at DESC
            LIMIT 10
        ''').fetchall()
    except sqlite3.OperationalError as e:
        flash(f'Database error: {str(e)}', 'danger')
        params = None
        history = []
    finally:
        conn.close()
    
    return render_template('admin/parameter.html', params=params, history=history)

@app.route('/admin/parameter/update', methods=['POST'])
@admin_required
def update_parameter():
    # Validasi input
    try:
        nilai_k = int(request.form['nilai_k'])
        bobot_berat = float(request.form['bobot_berat'])
        bobot_tinggi = float(request.form['bobot_tinggi'])
        bobot_lila = float(request.form['bobot_lila'])
        bobot_umur = float(request.form['bobot_umur'])
        bobot_jk = float(request.form['bobot_jk'])
    except ValueError:
        flash('Input tidak valid', 'danger')
        return redirect(url_for('parameter'))
    
    # Validasi total bobot
    total_bobot = bobot_berat + bobot_tinggi + bobot_lila + bobot_umur + bobot_jk
    if not 0.99 <= total_bobot <= 1.01:
        flash('Total bobot harus sama dengan 1.0', 'danger')
        return redirect(url_for('parameter'))
    
    conn = get_db()
    try:
        # Update parameter
        conn.execute('''
            UPDATE parameter_knn 
            SET nilai_k = ?, 
                bobot_berat = ?, 
                bobot_tinggi = ?, 
                bobot_lila = ?, 
                bobot_umur = ?, 
                bobot_jk = ?
        ''', (nilai_k, bobot_berat, bobot_tinggi, bobot_lila, bobot_umur, bobot_jk))
        
        # Simpan history
        conn.execute('''
            INSERT INTO parameter_history 
            (parameter_id, changed_by, nilai_k, bobot_berat, bobot_tinggi, bobot_lila, bobot_umur, bobot_jk)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], nilai_k, bobot_berat, bobot_tinggi, bobot_lila, bobot_umur, bobot_jk))
        
        conn.commit()
        flash('Parameter berhasil diperbarui', 'success')
    except sqlite3.OperationalError as e:
        conn.rollback()
        flash(f'Database error: {str(e)}', 'danger')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('parameter'))

# =============================================
# FUNGSI UPLOAD DATA
# =============================================

@app.route('/balita/upload', methods=['GET', 'POST'])
@login_required
def upload_balita_pengukuran():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('File tidak ditemukan', 'danger')
            return redirect(url_for('upload_balita_pengukuran'))

        file = request.files['file']
        if file.filename == '':
            flash('Nama file tidak valid', 'danger')
            return redirect(url_for('upload_balita_pengukuran'))

        conn = None
        try:
            df = pd.read_excel(file)
            required_columns = [
                'nama', 'nama orangtua', 'jenis kelamin', 'usia_tahun', 'usia_bulan',
                'tgl pengukuran', 'berat badan (KG)', 'Tinggi badan (CM)', 'LILA (CM)'
            ]
            if not all(col in df.columns for col in required_columns):
                flash(f'Kolom wajib: {", ".join(required_columns)}', 'danger')
                return redirect(url_for('upload_balita_pengukuran'))

            conn = get_db()
            for _, row in df.iterrows():
                # Proses identik seperti sebelumnya
                try:
                    tahun = int(row['usia_tahun'])
                except:
                    tahun = 0
                try:
                    bulan = int(row['usia_bulan'])
                except:
                    bulan = 0

                if pd.notnull(row['tgl pengukuran']):
                    tgl_ukur = pd.to_datetime(row['tgl pengukuran']).date()
                else:
                    tgl_ukur = datetime.date.today()

                tanggal_lahir = tgl_ukur - relativedelta(years=tahun, months=bulan)

                # Cek apakah balita sudah ada
                balita = conn.execute(
                    'SELECT id FROM balita WHERE nama = ? AND nama_ortu = ? AND jenis_kelamin = ?',
                    (row['nama'], row['nama orangtua'], row['jenis kelamin'])
                ).fetchone()

                if not balita:
                    conn.execute(
                        '''INSERT INTO balita (nama, tanggal_lahir, jenis_kelamin, nama_ortu) 
                           VALUES (?, ?, ?, ?)''',
                        (row['nama'], tanggal_lahir, row['jenis kelamin'], row['nama orangtua'])
                    )
                    balita_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    balita_id = balita['id']

                # Masukkan pengukuran
                conn.execute(
                    '''INSERT INTO pengukuran (balita_id, tanggal_ukur, berat_badan, tinggi_badan, lingkar_lengan)
                       VALUES (?, ?, ?, ?, ?)''',
                    (
                        balita_id,
                        tgl_ukur,
                        float(str(row['berat badan (KG)']).replace(',', '.')),
                        float(str(row['Tinggi badan (CM)']).replace(',', '.')),
                        float(str(row['LILA (CM)']).replace(',', '.'))
                    )
                )
                pengukuran_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

                # === KLASIFIKASI OTOMATIS ===
                berat = float(str(row['berat badan (KG)']).replace(',', '.'))
                tinggi = float(str(row['Tinggi badan (CM)']).replace(',', '.'))
                lila  = float(str(row['LILA (CM)']).replace(',', '.'))
                status_gizi = hitung_status_gizi(berat, tinggi, lila)
                conn.execute(
                    '''INSERT INTO klasifikasi (pengukuran_id, status_gizi, tanggal_klasifikasi)
                       VALUES (?, ?, ?)''',
                    (pengukuran_id, status_gizi, tgl_ukur)
                )
            conn.commit()
            flash('Data balita, pengukuran, dan status gizi berhasil diunggah', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            if conn is not None:
                conn.close()

        return redirect(url_for('upload_balita_pengukuran'))
    return render_template('balita/upload.html')

# =============================================
# FUNGSI PENDUKUNG
# =============================================

def get_knn_parameters():
    """Mengambil parameter KNN dari database"""
    conn = get_db()
    params = conn.execute('SELECT * FROM parameter_knn').fetchone()
    conn.close()
    return params

# =============================================
# JALANKAN APLIKASI
# =============================================

print("Daftar file di folder templates:", os.listdir(os.path.join(app.root_path, 'templates')))
if __name__ == '__main__':
    app.run(debug=True)