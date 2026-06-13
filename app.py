# -*- coding: utf-8 -*-
"""
Öğrenci Bilgi Sistemi (OBS) - Backend Sunucu Mantığı
Flask + SQLite (Varsayılan) / MySQL Tabanlı Rol Bazlı Yönetim Sistemi

Bu sistem, herhangi bir MySQL servisi çalıştırılmadan da (SQLite ile)
doğrudan çalıştırılabilir. MySQL kullanmak isterseniz USE_SQLITE = False yapabilirsiniz.
"""

import os
import sqlite3
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'obs_secret_key_123456_advanced_programming')

# ============================================================================
# VERİTABANI KONFİGÜRASYONU
# ============================================================================
# MySQL servisi olmadan çalışması için varsayılan olarak True'dur.
# MySQL kullanmak isterseniz False yapıp aşağıdaki bağlantı bilgilerini girebilirsiniz.
USE_SQLITE = True

# MySQL Bağlantı Bilgileri
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'obs_db')

def get_db_connection(use_db=True):
    """Konfigürasyona göre SQLite veya MySQL veritabanı bağlantısı oluşturur."""
    if USE_SQLITE:
        # SQLite bağlantısı oluştur (Dosya lokal dizinde 'obs.db' olarak açılır)
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'obs.db'))
        # PyMySQL DictCursor davranışı elde etmek için row_factory tanımla
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        # Yabancı anahtar (FK) kısıtlamalarını etkinleştir
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    else:
        # MySQL bağlantısı oluştur
        return pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB if use_db else None,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )

# ============================================================================
# SQL SORGUSU YARDIMCILARI (SQLITE & MYSQL UYUMLULUĞU İÇİN)
# ============================================================================

def get_concat(fields, alias):
    """SQLite (||) ve MySQL (CONCAT) için uyumlu string birleştirme sorgusu döner."""
    if USE_SQLITE:
        return f"({' || \' \' || '.join(fields)}) as {alias}"
    else:
        return f"CONCAT({', \' \', '.join(fields)}) as {alias}"

def db_execute(cursor, sql, params=None):
    """Sorgulardaki %s parametresini SQLite için ? karakterine dönüştürüp çalıştırır."""
    if USE_SQLITE:
        sql = sql.replace('%s', '?')
    if params is not None:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)

# ============================================================================
# VERİTABANI İLK KURULUMU (AUTO-INITIALIZE & SEED)
# ============================================================================

def init_sqlite_db(conn):
    """SQLite veritabanını oluşturur ve örnek verileri yükler."""
    cursor = conn.cursor()
    
    # 1. users tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'academician', 'student')) NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 2. academicians tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    # 3. students tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            student_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gpa REAL DEFAULT 0.00,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    # 4. courses tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            academician_id INTEGER DEFAULT NULL,
            FOREIGN KEY (academician_id) REFERENCES academicians(id) ON DELETE SET NULL
        );
    """)
    
    # 5. student_courses tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
    """)
    
    # 6. grades tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_course_id INTEGER UNIQUE NOT NULL,
            midterm REAL DEFAULT NULL,
            final REAL DEFAULT NULL,
            project REAL DEFAULT NULL,
            presentation REAL DEFAULT NULL,
            average REAL DEFAULT NULL,
            letter_grade TEXT DEFAULT NULL,
            FOREIGN KEY (student_course_id) REFERENCES student_courses(id) ON DELETE CASCADE
        );
    """)
    
    # 7. attendance tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_course_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            status TEXT CHECK(status IN ('Present', 'Absent')) NOT NULL,
            UNIQUE(student_course_id, week_number),
            FOREIGN KEY (student_course_id) REFERENCES student_courses(id) ON DELETE CASCADE
        );
    """)
    
    # Veri var mı kontrol et, yoksa örnek verileri ekle (Seeds)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()['count'] == 0:
        print("SQLite veritabanı örnek verilerle dolduruluyor...")
        
        # Kullanıcılar
        users_data = [
            (1, 'admin', 'admin123', 'admin', 'admin@obs.edu.tr'),
            (2, 'prof_ahmet', 'hoca123', 'academician', 'ahmet.yilmaz@obs.edu.tr'),
            (3, 'doc_elif', 'hoca123', 'academician', 'elif.kaya@obs.edu.tr'),
            (4, 'dr_mehmet', 'hoca123', 'academician', 'mehmet.demir@obs.edu.tr'),
            (5, 'ogr_ali', 'ogr123', 'student', 'ali.ozturk@ogr.obs.edu.tr'),
            (6, 'ogr_ayse', 'ogr123', 'student', 'ayse.yilmaz@ogr.obs.edu.tr'),
            (7, 'ogr_can', 'ogr123', 'student', 'can.demir@ogr.obs.edu.tr'),
            (8, 'ogr_fatma', 'ogr123', 'student', 'fatma.sahin@ogr.obs.edu.tr'),
            (9, 'ogr_burak', 'ogr123', 'student', 'burak.aslan@ogr.obs.edu.tr'),
            (10, 'ogr_zeynep', 'ogr123', 'student', 'zeynep.celik@ogr.obs.edu.tr'),
            (11, 'ogr_mert', 'ogr123', 'student', 'mert.koc@ogr.obs.edu.tr'),
            (12, 'ogr_gamze', 'ogr123', 'student', 'gamze.turan@ogr.obs.edu.tr'),
            (13, 'ogr_emre', 'ogr123', 'student', 'emre.kara@ogr.obs.edu.tr'),
            (14, 'ogr_selin', 'ogr123', 'student', 'selin.yildiz@ogr.obs.edu.tr')
        ]
        cursor.executemany("INSERT INTO users (id, username, password, role, email) VALUES (?, ?, ?, ?, ?)", users_data)
        
        # Akademisyenler
        acad_data = [
            (1, 2, 'Prof. Dr.', 'Ahmet', 'Yılmaz', 'Bilgisayar Mühendisliği'),
            (2, 3, 'Doç. Dr.', 'Elif', 'Kaya', 'Yazılım Mühendisliği'),
            (3, 4, 'Dr. Öğr. Üyesi', 'Mehmet', 'Demir', 'Bilişim Sistemleri Mühendisliği')
        ]
        cursor.executemany("INSERT INTO academicians (id, user_id, title, first_name, last_name, department) VALUES (?, ?, ?, ?, ?, ?)", acad_data)
        
        # Öğrenciler
        student_data = [
            (1, 5, '2026001', 'Ali', 'Öztürk', 3.25),
            (2, 6, '2026002', 'Ayşe', 'Yılmaz', 3.80),
            (3, 7, '2026003', 'Can', 'Demir', 2.45),
            (4, 8, '2026004', 'Fatma', 'Şahin', 3.10),
            (5, 9, '2026005', 'Burak', 'Aslan', 2.90),
            (6, 10, '2026006', 'Zeynep', 'Çelik', 3.65),
            (7, 11, '2026007', 'Mert', 'Koç', 2.10),
            (8, 12, '2026008', 'Gamze', 'Turan', 3.40),
            (9, 13, '2026009', 'Emre', 'Kara', 2.75),
            (10, 14, '2026010', 'Selin', 'Yıldız', 3.95)
        ]
        cursor.executemany("INSERT INTO students (id, user_id, student_number, first_name, last_name, gpa) VALUES (?, ?, ?, ?, ?, ?)", student_data)
        
        # Dersler
        course_data = [
            (1, 'BM101', 'Programlamaya Giriş', 4, 1),
            (2, 'BM202', 'Veri Yapıları ve Algoritmalar', 4, 1),
            (3, 'BM303', 'Veritabanı Yönetim Sistemleri', 3, 2),
            (4, 'BM404', 'Yazılım Mühendisliği', 3, 2),
            (5, 'BM205', 'Nesne Yönelimli Programlama', 4, 3),
            (6, 'BM306', 'Web Tasarımı ve Geliştirme', 3, 3),
            (7, 'BM407', 'İleri Programlama', 3, 1),
            (8, 'BM308', 'İşletim Sistemleri', 3, 2),
            (9, 'BM109', 'Matematik I', 4, 3),
            (10, 'BM210', 'Lineer Cebir', 3, 1)
        ]
        cursor.executemany("INSERT INTO courses (id, course_code, course_name, credits, academician_id) VALUES (?, ?, ?, ?, ?)", course_data)
        
        # Öğrenci Ders Kayıtları
        enroll_data = [
            (1, 1), (1, 3), (1, 7), (1, 9), # Ali
            (2, 1), (2, 3), (2, 7), (2, 8), # Ayşe
            (3, 2), (3, 5), (3, 9), (3, 10), # Can
            (4, 2), (4, 6), (4, 8), (4, 10), # Fatma
            (5, 1), (5, 5), (5, 7), (5, 9), # Burak
            (6, 3), (6, 4), (6, 7), (6, 8), # Zeynep
            (7, 2), (7, 5), (7, 6), (7, 10), # Mert
            (8, 1), (8, 4), (8, 7), (8, 9), # Gamze
            (9, 2), (9, 3), (9, 6), (9, 10), # Emre
            (10, 3), (10, 4), (10, 7), (10, 8) # Selin
        ]
        cursor.executemany("INSERT INTO student_courses (student_id, course_id) VALUES (?, ?)", enroll_data)
        
        # Notlar
        # student_course_id değerleri otomatik 1'den 40'a artacaktır
        grades_data = [
            (1, 75.00, 80.00, 85.00, 90.00, 80.50, 'BB'),
            (2, 60.00, 70.00, 75.00, 80.00, 69.00, 'CC'),
            (3, 85.00, 90.00, 95.00, 100.00, 90.50, 'AA'),
            (4, 50.00, 55.00, 60.00, 70.00, 56.00, 'FD'),
            (5, 95.00, 95.00, 100.00, 100.00, 96.50, 'AA'),
            (6, 90.00, 85.00, 90.00, 95.00, 88.50, 'BA'),
            (7, 88.00, 92.00, 90.00, 90.00, 90.20, 'AA'),
            (8, 85.00, 80.00, 85.00, 90.00, 83.50, 'BB'),
            (9, 45.00, 50.00, 60.00, 50.00, 50.50, 'DD'),
            (10, 55.00, 60.00, 55.00, 70.00, 58.50, 'DD'),
            (11, 40.00, 45.00, 50.00, 50.00, 45.00, 'FF'),
            (12, 60.00, 65.00, 70.00, 60.00, 64.00, 'DC'),
            (13, 70.00, 75.00, 80.00, 80.00, 75.00, 'CB'),
            (14, 80.00, 75.00, 85.00, 90.00, 80.00, 'BB'),
            (15, 65.00, 70.00, 75.00, 70.00, 69.50, 'CC'),
            (16, 75.00, 80.00, 85.00, 80.00, 79.50, 'CB'),
            (17, 70.00, 65.00, 70.00, 80.00, 69.00, 'CC'),
            (18, 60.00, 70.00, 75.00, 70.00, 68.00, 'CC'),
            (19, 75.00, 80.00, 80.00, 85.00, 79.00, 'CB'),
            (20, 55.00, 60.00, 65.00, 70.00, 60.50, 'DD'),
            (21, 85.00, 90.00, 95.00, 90.00, 89.50, 'BA'),
            (22, 90.00, 95.00, 90.00, 95.00, 92.50, 'AA'),
            (23, 80.00, 85.00, 90.00, 90.00, 85.00, 'BA'),
            (24, 85.00, 80.00, 90.00, 85.00, 84.00, 'BB'),
            (25, 40.00, 50.00, 45.00, 50.00, 46.00, 'FF'),
            (26, 50.00, 55.00, 60.00, 60.00, 55.00, 'FD'),
            (27, 55.00, 50.00, 50.00, 60.00, 52.50, 'DD'),
            (28, 45.00, 45.00, 50.00, 55.00, 46.50, 'FF'),
            (29, 80.00, 85.00, 90.00, 90.00, 85.00, 'BA'),
            (30, 85.00, 80.00, 85.00, 90.00, 83.50, 'BB'),
            (31, 75.00, 80.00, 80.00, 85.00, 79.00, 'CB'),
            (32, 90.00, 90.00, 95.00, 95.00, 91.50, 'AA'),
            (33, 60.00, 65.00, 70.00, 75.00, 65.50, 'DC'),
            (34, 70.00, 70.00, 75.00, 80.00, 72.00, 'CC'),
            (35, 65.00, 70.00, 65.00, 70.00, 67.50, 'CC'),
            (36, 55.00, 60.00, 60.00, 70.00, 59.50, 'DD'),
            (37, 95.00, 100.00, 95.00, 100.00, 97.50, 'AA'),
            (38, 90.00, 95.00, 95.00, 95.00, 93.50, 'AA'),
            (39, 95.00, 95.00, 100.00, 100.00, 96.50, 'AA'),
            (40, 90.00, 90.00, 95.00, 95.00, 91.50, 'AA')
        ]
        cursor.executemany("INSERT INTO grades (student_course_id, midterm, final, project, presentation, average, letter_grade) VALUES (?, ?, ?, ?, ?, ?, ?)", grades_data)
        
        # Devamsızlık (Hazır 1-4 haftalık kayıtlar)
        att_data = [
            (1, 1, 'Present'), (1, 2, 'Present'), (1, 3, 'Absent'), (1, 4, 'Present'),
            (2, 1, 'Present'), (2, 2, 'Present'), (2, 3, 'Present'), (2, 4, 'Present'),
            (3, 1, 'Present'), (3, 2, 'Absent'), (3, 3, 'Absent'), (3, 4, 'Present'),
            (5, 1, 'Present'), (5, 2, 'Present'), (5, 3, 'Present'), (5, 4, 'Present'),
            (6, 1, 'Present'), (6, 2, 'Present'), (6, 3, 'Present'), (6, 4, 'Present'),
            (7, 1, 'Present'), (7, 2, 'Present'), (7, 3, 'Present'), (7, 4, 'Present'),
            (21, 1, 'Present'), (21, 2, 'Absent'), (21, 3, 'Present'), (21, 4, 'Present'),
            (22, 1, 'Present'), (22, 2, 'Present'), (22, 3, 'Present'), (22, 4, 'Present'),
            (23, 1, 'Present'), (23, 2, 'Present'), (23, 3, 'Absent'), (23, 4, 'Present')
        ]
        cursor.executemany("INSERT INTO attendance (student_course_id, week_number, status) VALUES (?, ?, ?)", att_data)
        
        # Diğer tüm dersler için haftalık devamsızlık kayıtlarını (1-14. haftalar) 'Present' olarak varsayılan yap
        # Bu işlem arayüzün boş kalmaması içindir
        for sc_id in range(1, 41):
            for week in range(1, 15):
                cursor.execute("""
                    INSERT OR IGNORE INTO attendance (student_course_id, week_number, status)
                    VALUES (?, ?, 'Present')
                """, (sc_id, week))
                
        conn.commit()
        print("SQLite örnek verileri başarıyla yüklendi.")

def init_db():
    """Veritabanını türüne göre otomatik hazırlar."""
    if USE_SQLITE:
        conn = get_db_connection()
        try:
            init_sqlite_db(conn)
        except Exception as e:
            print(f"SQLite başlatma hatası: {e}")
        finally:
            conn.close()
    else:
        # MySQL başlatma mantığı
        try:
            conn = get_db_connection(use_db=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            conn = get_db_connection(use_db=True)
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                if len(tables) == 0:
                    sql_file_path = os.path.join(os.path.dirname(__file__), 'database.sql')
                    if os.path.exists(sql_file_path):
                        print("MySQL şeması kuruluyor...")
                        with open(sql_file_path, 'r', encoding='utf-8') as f:
                            sql_content = f.read()

                        statements = []
                        current_stmt = []
                        for line in sql_content.splitlines():
                            stripped = line.strip()
                            if not stripped or stripped.startswith('--') or stripped.startswith('#'):
                                continue
                            current_stmt.append(line)
                            if stripped.endswith(';'):
                                statements.append("\n".join(current_stmt))
                                current_stmt = []

                        for stmt in statements:
                            if stmt.strip():
                                cursor.execute(stmt)
                        conn.commit()
            conn.close()
        except Exception as e:
            print(f"MySQL başlatma uyarısı: {e}")

# Uygulama başladığında veritabanını otomatik kur
init_db()

# ============================================================================
# İŞ MANTIXI VE YARDIMCILAR
# ============================================================================

def verify_password(stored_password, entered_password):
    """Veritabanındaki şifreyi doğrular (hem hashli hem de düz metin desteği sağlar)."""
    if stored_password.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
        return check_password_hash(stored_password, entered_password)
    return stored_password == entered_password

def calculate_grade(midterm, final, project, presentation):
    """Not ortalamasını ve harf notunu hesaplar."""
    if midterm is None or final is None:
        return None, None
    
    try:
        m = float(midterm)
        f = float(final)
        p = float(project) if project is not None else 0.0
        pr = float(presentation) if presentation is not None else 0.0
        
        # Ağırlıklar: Vize %30, Final %40, Proje %20, Sunum %10
        avg = m * 0.30 + f * 0.40 + p * 0.20 + pr * 0.10
        avg = round(avg, 2)
        
        if avg >= 90:
            letter = 'AA'
        elif avg >= 85:
            letter = 'BA'
        elif avg >= 80:
            letter = 'BB'
        elif avg >= 75:
            letter = 'CB'
        elif avg >= 70:
            letter = 'CC'
        elif avg >= 65:
            letter = 'DC'
        elif avg >= 60:
            letter = 'DD'
        elif avg >= 50:
            letter = 'FD'
        else:
            letter = 'FF'
            
        return avg, letter
    except (ValueError, TypeError):
        return None, None

def recalculate_student_gpa(student_id):
    """Öğrencinin tüm ders notlarına göre Genel Not Ortalamasını (GNO) hesaplar ve günceller."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT g.letter_grade, c.credits 
            FROM grades g
            JOIN student_courses sc ON g.student_course_id = sc.id
            JOIN courses c ON sc.course_id = c.id
            WHERE sc.student_id = %s AND g.letter_grade IS NOT NULL
        """
        db_execute(cursor, query, (student_id,))
        records = cursor.fetchall()
        
        if not records:
            db_execute(cursor, "UPDATE students SET gpa = 0.00 WHERE id = %s", (student_id,))
            conn.commit()
            return
        
        points_map = {
            'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
            'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FD': 0.5, 'FF': 0.0
        }
        
        total_points = 0.0
        total_credits = 0
        for r in records:
            letter = r['letter_grade']
            credits = r['credits']
            if letter in points_map:
                total_points += points_map[letter] * credits
                total_credits += credits
        
        gpa = 0.00
        if total_credits > 0:
            gpa = total_points / total_credits
        
        db_execute(cursor, "UPDATE students SET gpa = %s WHERE id = %s", (round(gpa, 2), student_id))
        conn.commit()
    except Exception as e:
        print(f"GNO hesaplama hatası (Öğrenci ID: {student_id}): {e}")
    finally:
        conn.close()

# ============================================================================
# ROTALAR / CONTROLLERS
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş yapma işlemlerini yönetir."""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Lütfen kullanıcı adı ve şifre alanlarını doldurun.', 'danger')
            return redirect(url_for('login'))
            
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            db_execute(cursor, "SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and verify_password(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['email'] = user['email']
                
                if user['role'] == 'student':
                    db_execute(cursor, "SELECT id, student_number, first_name, last_name FROM students WHERE user_id = %s", (user['id'],))
                    student = cursor.fetchone()
                    if student:
                        session['student_id'] = student['id']
                        session['student_number'] = student['student_number']
                        session['full_name'] = f"{student['first_name']} {student['last_name']}"
                
                elif user['role'] == 'academician':
                    db_execute(cursor, "SELECT id, title, first_name, last_name, department FROM academicians WHERE user_id = %s", (user['id'],))
                    academician = cursor.fetchone()
                    if academician:
                        session['academician_id'] = academician['id']
                        session['full_name'] = f"{academician['title']} {academician['first_name']} {academician['last_name']}"
                        session['department'] = academician['department']
                        
                elif user['role'] == 'admin':
                    session['full_name'] = 'Sistem Yöneticisi'
                    
                flash(f'Hoş geldiniz, {session.get("full_name", session["username"])}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Hatalı kullanıcı adı veya şifre!', 'danger')
        except Exception as e:
            flash(f'Giriş yapılırken veritabanı hatası: {e}', 'danger')
        finally:
            conn.close()
            
    return render_template('index.html', page='login')

@app.route('/logout')
def logout():
    """Oturumu sonlandırır."""
    session.clear()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Ana sayfa router'ı. Oturumu kontrol eder ve uygun paneli yükler."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    page = request.args.get('page', 'dashboard')
    role = session.get('role')
    
    if role != 'admin' and page in ['users', 'courses_mgmt']:
        flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
        return redirect(url_for('index', page='dashboard'))
        
    conn = get_db_connection()
    data = {}
    
    try:
        cursor = conn.cursor()
        
        # ----------------------------------------------------------------
        # 1. PANOLAR (DASHBOARD) ORTAK VERİLERİ
        # ----------------------------------------------------------------
        if page == 'dashboard':
            db_execute(cursor, "SELECT COUNT(*) as count FROM students")
            data['total_students'] = cursor.fetchone()['count']
            
            db_execute(cursor, "SELECT COUNT(*) as count FROM academicians")
            data['total_academicians'] = cursor.fetchone()['count']
            
            db_execute(cursor, "SELECT COUNT(*) as count FROM courses")
            data['total_courses'] = cursor.fetchone()['count']
            
            # Başarı Oranı
            db_execute(cursor, """
                SELECT 
                    COUNT(CASE WHEN letter_grade NOT IN ('FF', 'FD') AND letter_grade IS NOT NULL THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(CASE WHEN letter_grade IS NOT NULL THEN 1 END), 0) as rate
                FROM grades
            """)
            rate_result = cursor.fetchone()
            data['success_rate'] = round(rate_result['rate'], 1) if (rate_result and rate_result['rate'] is not None) else 0.0

            if role == 'student':
                student_id = session.get('student_id')
                db_execute(cursor, "SELECT gpa FROM students WHERE id = %s", (student_id,))
                student_info = cursor.fetchone()
                data['student_gpa'] = student_info['gpa'] if (student_info and student_info['gpa'] is not None) else 0.00
                
                db_execute(cursor, "SELECT COUNT(*) as count FROM student_courses WHERE student_id = %s", (student_id,))
                data['student_courses_count'] = cursor.fetchone()['count']
                
                db_execute(cursor, """
                    SELECT COUNT(*) as count 
                    FROM attendance a
                    JOIN student_courses sc ON a.student_course_id = sc.id
                    WHERE sc.student_id = %s AND a.status = 'Absent'
                """, (student_id,))
                data['student_absent_count'] = cursor.fetchone()['count']
                
            elif role == 'academician':
                acad_id = session.get('academician_id')
                db_execute(cursor, "SELECT COUNT(*) as count FROM courses WHERE academician_id = %s", (acad_id,))
                data['acad_courses_count'] = cursor.fetchone()['count']
                
                db_execute(cursor, """
                    SELECT COUNT(DISTINCT sc.student_id) as count
                    FROM student_courses sc
                    JOIN courses c ON sc.course_id = c.id
                    WHERE c.academician_id = %s
                """, (acad_id,))
                data['acad_students_count'] = cursor.fetchone()['count']
        
        # ----------------------------------------------------------------
        # 2. DERSLER SAYFASI (COURSES)
        # ----------------------------------------------------------------
        elif page == 'courses':
            concat_acad = get_concat(["a.title", "a.first_name", "a.last_name"], "academician_name")
            if role == 'admin':
                db_execute(cursor, f"""
                    SELECT c.*, {concat_acad} 
                    FROM courses c
                    LEFT JOIN academicians a ON c.academician_id = a.id
                    ORDER BY c.course_code
                """)
                data['courses'] = cursor.fetchall()
            elif role == 'academician':
                db_execute(cursor, """
                    SELECT *, (SELECT COUNT(*) FROM student_courses WHERE course_id = courses.id) as student_count
                    FROM courses 
                    WHERE academician_id = %s 
                    ORDER BY course_code
                """, (session.get('academician_id'),))
                data['courses'] = cursor.fetchall()
            elif role == 'student':
                db_execute(cursor, f"""
                    SELECT c.*, {concat_acad}
                    FROM student_courses sc
                    JOIN courses c ON sc.course_id = c.id
                    LEFT JOIN academicians a ON c.academician_id = a.id
                    WHERE sc.student_id = %s
                    ORDER BY c.course_code
                """, (session.get('student_id'),))
                data['courses'] = cursor.fetchall()

        # ----------------------------------------------------------------
        # 3. NOTLAR SAYFASI (GRADES)
        # ----------------------------------------------------------------
        elif page == 'grades':
            concat_stud = get_concat(["s.first_name", "s.last_name"], "student_name")
            if role == 'admin':
                db_execute(cursor, f"""
                    SELECT g.*, c.course_code, c.course_name, s.student_number, {concat_stud}
                    FROM grades g
                    JOIN student_courses sc ON g.student_course_id = sc.id
                    JOIN courses c ON sc.course_id = c.id
                    JOIN students s ON sc.student_id = s.id
                    ORDER BY c.course_code, s.student_number
                """)
                data['grades'] = cursor.fetchall()
            elif role == 'academician':
                acad_id = session.get('academician_id')
                db_execute(cursor, "SELECT id, course_code, course_name FROM courses WHERE academician_id = %s", (acad_id,))
                data['my_courses'] = cursor.fetchall()
                
                selected_course = request.args.get('course_id')
                data['selected_course_id'] = selected_course
                if selected_course:
                    db_execute(cursor, f"""
                        SELECT sc.id as student_course_id, s.id as student_id, s.student_number, {concat_stud},
                               g.midterm, g.final, g.project, g.presentation, g.average, g.letter_grade
                        FROM student_courses sc
                        JOIN students s ON sc.student_id = s.id
                        LEFT JOIN grades g ON g.student_course_id = sc.id
                        WHERE sc.course_id = %s
                        ORDER BY s.student_number
                    """, (selected_course,))
                    data['student_grades'] = cursor.fetchall()
            elif role == 'student':
                db_execute(cursor, """
                    SELECT c.course_code, c.course_name, c.credits,
                           g.midterm, g.final, g.project, g.presentation, g.average, g.letter_grade
                    FROM student_courses sc
                    JOIN courses c ON sc.course_id = c.id
                    LEFT JOIN grades g ON g.student_course_id = sc.id
                    WHERE sc.student_id = %s
                    ORDER BY c.course_code
                """, (session.get('student_id'),))
                data['grades'] = cursor.fetchall()

        # ----------------------------------------------------------------
        # 4. DEVAMSIZLIK SAYFASI (ATTENDANCE)
        # ----------------------------------------------------------------
        elif page == 'attendance':
            concat_stud = get_concat(["s.first_name", "s.last_name"], "student_name")
            if role == 'admin':
                db_execute(cursor, f"""
                    SELECT s.student_number, {concat_stud},
                           c.course_code, c.course_name,
                           COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
                           COUNT(a.id) as total_weeks
                    FROM student_courses sc
                    JOIN students s ON sc.student_id = s.id
                    JOIN courses c ON sc.course_id = c.id
                    LEFT JOIN attendance a ON a.student_course_id = sc.id
                    GROUP BY sc.id
                    ORDER BY s.student_number, c.course_code
                """)
                data['attendance'] = cursor.fetchall()
            elif role == 'academician':
                acad_id = session.get('academician_id')
                db_execute(cursor, "SELECT id, course_code, course_name FROM courses WHERE academician_id = %s", (acad_id,))
                data['my_courses'] = cursor.fetchall()
                
                selected_course = request.args.get('course_id')
                data['selected_course_id'] = selected_course
                if selected_course:
                    db_execute(cursor, f"""
                        SELECT sc.id as student_course_id, s.student_number, {concat_stud},
                               COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
                               COUNT(a.id) as total_weeks
                        FROM student_courses sc
                        JOIN students s ON sc.student_id = s.id
                        LEFT JOIN attendance a ON a.student_course_id = sc.id
                        WHERE sc.course_id = %s
                        GROUP BY sc.id
                        ORDER BY s.student_number
                    """, (selected_course,))
                    data['students_attendance'] = cursor.fetchall()
                    
                    selected_sc_id = request.args.get('sc_id')
                    if selected_sc_id:
                        db_execute(cursor, """
                            SELECT * FROM attendance 
                            WHERE student_course_id = %s 
                            ORDER BY week_number
                        """, (selected_sc_id,))
                        data['detail_attendance'] = cursor.fetchall()
                        data['selected_sc_id'] = selected_sc_id
            elif role == 'student':
                student_id = session.get('student_id')
                db_execute(cursor, """
                    SELECT sc.id as student_course_id, c.course_code, c.course_name,
                           COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
                           COUNT(a.id) as total_weeks
                    FROM student_courses sc
                    JOIN courses c ON sc.course_id = c.id
                    LEFT JOIN attendance a ON a.student_course_id = sc.id
                    WHERE sc.student_id = %s
                    GROUP BY sc.id
                    ORDER BY c.course_code
                """, (student_id,))
                data['summary'] = cursor.fetchall()
                
                db_execute(cursor, """
                    SELECT c.course_code, a.week_number, a.status
                    FROM student_courses sc
                    JOIN courses c ON sc.course_id = c.id
                    JOIN attendance a ON a.student_course_id = sc.id
                    WHERE sc.student_id = %s
                    ORDER BY c.course_code, a.week_number
                """, (student_id,))
                data['weeks'] = cursor.fetchall()

        # ----------------------------------------------------------------
        # 5. KULLANICI YÖNETİMİ (ADMIN ONLY)
        # ----------------------------------------------------------------
        elif page == 'users':
            db_execute(cursor, """
                SELECT s.id as student_id, s.student_number, s.first_name, s.last_name, s.gpa, u.username, u.email, u.id as user_id
                FROM students s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.student_number
            """)
            data['students'] = cursor.fetchall()
            
            db_execute(cursor, """
                SELECT a.id as academician_id, a.title, a.first_name, a.last_name, a.department, u.username, u.email, u.id as user_id
                FROM academicians a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.last_name
            """)
            data['academicians'] = cursor.fetchall()

        # ----------------------------------------------------------------
        # 6. DERS YÖNETİMİ (ADMIN ONLY)
        # ----------------------------------------------------------------
        elif page == 'courses_mgmt':
            concat_acad = get_concat(["a.title", "a.first_name", "a.last_name"], "academician_name")
            db_execute(cursor, f"""
                SELECT c.*, {concat_acad}
                FROM courses c
                LEFT JOIN academicians a ON c.academician_id = a.id
                ORDER BY c.course_code
            """)
            data['courses'] = cursor.fetchall()
            
            concat_acad = get_concat(["title", "first_name", "last_name"], "name")
            db_execute(cursor, f"SELECT id, {concat_acad} FROM academicians ORDER BY last_name")
            data['academicians'] = cursor.fetchall()
            
            concat_stud = get_concat(["first_name", "last_name"], "name")
            db_execute(cursor, f"SELECT id, student_number, {concat_stud} FROM students ORDER BY student_number")
            data['students'] = cursor.fetchall()

    except Exception as e:
        flash(f'Veri çekilirken hata oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return render_template('index.html', page=page, data=data)


# ============================================================================
# API / İŞLEM ROTASI (ADMIN İŞLEMLERİ)
# ============================================================================

@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    """Yeni öğrenci veya akademisyen ekler."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    user_type = request.form.get('user_type')
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    
    if not username or not password or not email or not first_name or not last_name:
        flash('Lütfen tüm zorunlu alanları doldurun.', 'danger')
        return redirect(url_for('index', page='users'))
        
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            flash('Bu kullanıcı adı veya e-posta adresi zaten kullanımda!', 'danger')
            return redirect(url_for('index', page='users'))
            
        if user_type == 'student':
            student_number = request.form.get('student_number')
            gpa = request.form.get('gpa', 0.00)
            if not student_number:
                flash('Öğrenci numarası zorunludur.', 'danger')
                return redirect(url_for('index', page='users'))
                
            db_execute(cursor, "SELECT id FROM students WHERE student_number = %s", (student_number,))
            if cursor.fetchone():
                flash('Bu öğrenci numarası zaten kullanımda!', 'danger')
                return redirect(url_for('index', page='users'))
            
            db_execute(cursor, "INSERT INTO users (username, password, role, email) VALUES (%s, %s, 'student', %s)", (username, hashed_password, email))
            user_id = cursor.lastrowid if not USE_SQLITE else cursor.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            db_execute(cursor, "INSERT INTO students (user_id, student_number, first_name, last_name, gpa) VALUES (%s, %s, %s, %s, %s)", (user_id, student_number, first_name, last_name, gpa))
            conn.commit()
            flash(f'Öğrenci {first_name} {last_name} ({student_number}) başarıyla eklendi.', 'success')
            
        elif user_type == 'academician':
            title = request.form.get('title')
            department = request.form.get('department')
            if not title or not department:
                flash('Akademik unvan ve departman alanları zorunludur.', 'danger')
                return redirect(url_for('index', page='users'))
            
            db_execute(cursor, "INSERT INTO users (username, password, role, email) VALUES (%s, %s, 'academician', %s)", (username, hashed_password, email))
            user_id = cursor.lastrowid if not USE_SQLITE else cursor.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            db_execute(cursor, "INSERT INTO academicians (user_id, title, first_name, last_name, department) VALUES (%s, %s, %s, %s, %s)", (user_id, title, first_name, last_name, department))
            conn.commit()
            flash(f'Akademisyen {title} {first_name} {last_name} başarıyla eklendi.', 'success')
            
    except Exception as e:
        flash(f'Kullanıcı eklenirken veritabanı hatası oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    """Kullanıcıyı sistemden siler."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    if user_id == 1:
        flash('Ana yönetici hesabı silinemez!', 'danger')
        return redirect(url_for('index', page='users'))
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash('Kullanıcı başarıyla sistemden silindi.', 'success')
    except Exception as e:
        flash(f'Kullanıcı silinirken bir hata oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='users'))

@app.route('/admin/add-course', methods=['POST'])
def admin_add_course():
    """Yeni ders oluşturur."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    course_code = request.form.get('course_code')
    course_name = request.form.get('course_name')
    credits = request.form.get('credits')
    academician_id = request.form.get('academician_id')
    
    if not course_code or not course_name or not credits:
        flash('Lütfen kod, isim ve kredi alanlarını doldurun.', 'danger')
        return redirect(url_for('index', page='courses_mgmt'))
        
    acad_val = int(academician_id) if academician_id and academician_id.strip() != "" else None
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "SELECT id FROM courses WHERE course_code = %s", (course_code,))
        if cursor.fetchone():
            flash('Bu ders kodu zaten tanımlı!', 'danger')
            return redirect(url_for('index', page='courses_mgmt'))
            
        db_execute(cursor, "INSERT INTO courses (course_code, course_name, credits, academician_id) VALUES (%s, %s, %s, %s)", (course_code, course_name, credits, acad_val))
        conn.commit()
        flash(f'{course_code} - {course_name} dersi başarıyla oluşturuldu.', 'success')
    except Exception as e:
        flash(f'Ders eklenirken hata oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='courses_mgmt'))

@app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
def admin_delete_course(course_id):
    """Dersi sistemden siler."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "DELETE FROM courses WHERE id = %s", (course_id,))
        conn.commit()
        flash('Ders başarıyla silindi.', 'success')
    except Exception as e:
        flash(f'Ders silinirken hata oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='courses_mgmt'))

@app.route('/admin/assign-academician', methods=['POST'])
def admin_assign_academician():
    """Derse akademisyen atar."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    course_id = request.form.get('course_id')
    academician_id = request.form.get('academician_id')
    
    if not course_id:
        flash('Lütfen bir ders seçin.', 'danger')
        return redirect(url_for('index', page='courses_mgmt'))
        
    acad_val = int(academician_id) if academician_id and academician_id.strip() != "" else None
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "UPDATE courses SET academician_id = %s WHERE id = %s", (acad_val, course_id))
        conn.commit()
        flash('Öğretim üyesi ataması başarıyla güncellendi.', 'success')
    except Exception as e:
        flash(f'Hoca atama işleminde hata: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='courses_mgmt'))

@app.route('/admin/enroll-student', methods=['POST'])
def admin_enroll_student():
    """Öğrenciyi derse kaydeder."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    if not student_id or not course_id:
        flash('Lütfen öğrenci ve ders seçimi yapın.', 'danger')
        return redirect(url_for('index', page='courses_mgmt'))
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, "SELECT id FROM student_courses WHERE student_id = %s AND course_id = %s", (student_id, course_id))
        if cursor.fetchone():
            flash('Öğrenci bu derse zaten kayıtlı!', 'warning')
            return redirect(url_for('index', page='courses_mgmt'))
            
        db_execute(cursor, "INSERT INTO student_courses (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        student_course_id = cursor.lastrowid if not USE_SQLITE else cursor.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        db_execute(cursor, "INSERT INTO grades (student_course_id) VALUES (%s)", (student_course_id,))
        
        # 1-14 haftaları doldur
        for w in range(1, 15):
            db_execute(cursor, "INSERT INTO attendance (student_course_id, week_number, status) VALUES (%s, %s, 'Present')", (student_course_id, w))
            
        conn.commit()
        flash('Öğrenci derse başarıyla kaydedildi.', 'success')
    except Exception as e:
        flash(f'Öğrenci derse eklenirken hata: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='courses_mgmt'))


# ============================================================================
# API / İŞLEM ROTASI (AKADEMİSYEN İŞLEMLERİ)
# ============================================================================

@app.route('/academician/update-grades', methods=['POST'])
def acad_update_grades():
    """Akademisyen tarafından not güncellemeyi sağlar."""
    if 'user_id' not in session or session.get('role') != 'academician':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    student_course_id = request.form.get('student_course_id')
    course_id = request.form.get('course_id')
    
    midterm = request.form.get('midterm')
    final = request.form.get('final')
    project = request.form.get('project')
    presentation = request.form.get('presentation')
    
    m_val = float(midterm) if midterm and midterm.strip() != "" else None
    f_val = float(final) if final and final.strip() != "" else None
    p_val = float(project) if project and project.strip() != "" else None
    pr_val = float(presentation) if presentation and presentation.strip() != "" else None
    
    avg, letter = calculate_grade(m_val, f_val, p_val, pr_val)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Yetki Doğrulama
        db_execute(cursor, """
            SELECT c.academician_id, sc.student_id 
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            WHERE sc.id = %s
        """, (student_course_id,))
        auth_check = cursor.fetchone()
        
        if not auth_check or auth_check['academician_id'] != session.get('academician_id'):
            flash('Bu işlemin yetkisi sizde bulunmuyor!', 'danger')
            return redirect(url_for('index', page='grades', course_id=course_id))
            
        student_id = auth_check['student_id']
        
        # SQLite & MySQL uyumlu INSERT/UPDATE
        if USE_SQLITE:
            query = """
                INSERT INTO grades (student_course_id, midterm, final, project, presentation, average, letter_grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_course_id) DO UPDATE SET 
                    midterm = excluded.midterm,
                    final = excluded.final,
                    project = excluded.project,
                    presentation = excluded.presentation,
                    average = excluded.average,
                    letter_grade = excluded.letter_grade
            """
        else:
            query = """
                INSERT INTO grades (student_course_id, midterm, final, project, presentation, average, letter_grade)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    midterm = VALUES(midterm),
                    final = VALUES(final),
                    project = VALUES(project),
                    presentation = VALUES(presentation),
                    average = VALUES(average),
                    letter_grade = VALUES(letter_grade)
            """
        db_execute(cursor, query, (student_course_id, m_val, f_val, p_val, pr_val, avg, letter))
        conn.commit()
        
        recalculate_student_gpa(student_id)
        
        flash('Not bilgileri başarıyla güncellendi.', 'success')
    except Exception as e:
        flash(f'Not kaydedilirken veritabanı hatası oluştu: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='grades', course_id=course_id))

@app.route('/academician/update-attendance', methods=['POST'])
def acad_update_attendance():
    """Haftalık devamsızlık durumlarını günceller."""
    if 'user_id' not in session or session.get('role') != 'academician':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
        
    student_course_id = request.form.get('student_course_id')
    course_id = request.form.get('course_id')
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, """
            SELECT c.academician_id 
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            WHERE sc.id = %s
        """, (student_course_id,))
        auth_check = cursor.fetchone()
        
        if not auth_check or auth_check['academician_id'] != session.get('academician_id'):
            flash('Bu devamsızlık işlemini yapmaya yetkiniz yok!', 'danger')
            return redirect(url_for('index', page='attendance', course_id=course_id))
            
        for week in range(1, 15):
            status_key = f'week_{week}'
            status = 'Present' if request.form.get(status_key) == 'Present' else 'Absent'
            
            if USE_SQLITE:
                query = """
                    INSERT INTO attendance (student_course_id, week_number, status)
                    VALUES (?, ?, ?)
                    ON CONFLICT(student_course_id, week_number) DO UPDATE SET status = excluded.status
                """
            else:
                query = """
                    INSERT INTO attendance (student_course_id, week_number, status)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status)
                """
            db_execute(cursor, query, (student_course_id, week, status))
            
        conn.commit()
        flash('Devamsızlık durumu güncellendi.', 'success')
    except Exception as e:
        flash(f'Devamsızlık güncellenirken hata: {e}', 'danger')
    finally:
        conn.close()
        
    return redirect(url_for('index', page='attendance', course_id=course_id))

@app.route('/academician/get-attendance/<int:sc_id>')
def get_student_course_attendance(sc_id):
    """AJAX ile öğrenci devamsızlık durumunu haftalık liste olarak döner."""
    if 'user_id' not in session or session.get('role') != 'academician':
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, """
            SELECT c.academician_id 
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            WHERE sc.id = %s
        """, (sc_id,))
        auth_check = cursor.fetchone()
        if not auth_check or auth_check['academician_id'] != session.get('academician_id'):
            return jsonify({'success': False, 'message': 'Yetkisiz ders erişimi'}), 403
            
        db_execute(cursor, "SELECT week_number, status FROM attendance WHERE student_course_id = %s ORDER BY week_number", (sc_id,))
        records = cursor.fetchall()
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/student/profile/<int:student_id>')
def student_profile_json(student_id):
    """AJAX ile profil görüntülemek için öğrencinin bilgilerini JSON formatında döner."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Lütfen giriş yapın'}), 401
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        db_execute(cursor, """
            SELECT s.student_number, s.first_name, s.last_name, s.gpa, u.email, u.username
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = %s
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({'success': False, 'message': 'Öğrenci bulunamadı'}), 404
            
        db_execute(cursor, """
            SELECT c.course_code, c.course_name, c.credits, g.letter_grade
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            LEFT JOIN grades g ON g.student_course_id = sc.id
            WHERE sc.student_id = %s
        """, (student_id,))
        courses = cursor.fetchall()
        
        db_execute(cursor, """
            SELECT c.course_code, 
                   COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_weeks
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            LEFT JOIN attendance a ON a.student_course_id = sc.id
            WHERE sc.student_id = %s
            GROUP BY sc.id
        """, (student_id,))
        attendance = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'student': student,
            'courses': courses,
            'attendance': attendance
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    # Sunucuyu yerel ağda dinlemeye başla (Port: 5000)
    app.run(debug=True, host='0.0.0.0', port=5000)
