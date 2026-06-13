-- Öğrenci Bilgi Sistemi (OBS) Veritabanı Şeması ve Örnek Verileri
-- İleri Programlama Dersi Projesi

CREATE DATABASE IF NOT EXISTS obs_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE obs_db;

-- 1. users tablosu
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'academician', 'student') NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. academicians tablosu
CREATE TABLE IF NOT EXISTS academicians (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    title VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. students tablosu
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    student_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    gpa DECIMAL(3,2) DEFAULT 0.00,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. courses tablosu
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    academician_id INT DEFAULT NULL,
    FOREIGN KEY (academician_id) REFERENCES academicians(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. student_courses tablosu (Öğrenci - Ders İlişkisi)
CREATE TABLE IF NOT EXISTS student_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    UNIQUE KEY unique_student_course (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. grades tablosu (Notlar)
CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_course_id INT UNIQUE NOT NULL,
    midterm DECIMAL(5,2) DEFAULT NULL,
    final DECIMAL(5,2) DEFAULT NULL,
    project DECIMAL(5,2) DEFAULT NULL,
    presentation DECIMAL(5,2) DEFAULT NULL,
    average DECIMAL(5,2) DEFAULT NULL,
    letter_grade VARCHAR(2) DEFAULT NULL,
    FOREIGN KEY (student_course_id) REFERENCES student_courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. attendance tablosu (Devamsızlık)
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_course_id INT NOT NULL,
    week_number INT NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL,
    UNIQUE KEY unique_student_course_week (student_course_id, week_number),
    FOREIGN KEY (student_course_id) REFERENCES student_courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- ÖRNEK VERİLERİN EKNLENMESİ (SEEDS)
-- ============================================================================

-- A. KULLANICILARIN EKLENMESİ (Şifreler düz metindir, app.py bunları hem düz hem hashli kontrol eder)

-- 1 Admin
INSERT INTO users (id, username, password, role, email) VALUES
(1, 'admin', 'admin123', 'admin', 'admin@obs.edu.tr');

-- 3 Akademisyen (Kullanıcı hesapları)
INSERT INTO users (id, username, password, role, email) VALUES
(2, 'prof_ahmet', 'hoca123', 'academician', 'ahmet.yilmaz@obs.edu.tr'),
(3, 'doc_elif', 'hoca123', 'academician', 'elif.kaya@obs.edu.tr'),
(4, 'dr_mehmet', 'hoca123', 'academician', 'mehmet.demir@obs.edu.tr');

-- 10 Öğrenci (Kullanıcı hesapları)
INSERT INTO users (id, username, password, role, email) VALUES
(5, 'ogr_ali', 'ogr123', 'student', 'ali.ozturk@ogr.obs.edu.tr'),
(6, 'ogr_ayse', 'ogr123', 'student', 'ayse.yilmaz@ogr.obs.edu.tr'),
(7, 'ogr_can', 'ogr123', 'student', 'can.demir@ogr.obs.edu.tr'),
(8, 'ogr_fatma', 'ogr123', 'student', 'fatma.sahin@ogr.obs.edu.tr'),
(9, 'ogr_burak', 'ogr123', 'student', 'burak.aslan@ogr.obs.edu.tr'),
(10, 'ogr_zeynep', 'ogr123', 'student', 'zeynep.celik@ogr.obs.edu.tr'),
(11, 'ogr_mert', 'ogr123', 'student', 'mert.koc@ogr.obs.edu.tr'),
(12, 'ogr_gamze', 'ogr123', 'student', 'gamze.turan@ogr.obs.edu.tr'),
(13, 'ogr_emre', 'ogr123', 'student', 'emre.kara@ogr.obs.edu.tr'),
(14, 'ogr_selin', 'ogr123', 'student', 'selin.yildiz@ogr.obs.edu.tr');


-- B. AKADEMİSYEN BİLGİLERİ
INSERT INTO academicians (id, user_id, title, first_name, last_name, department) VALUES
(1, 2, 'Prof. Dr.', 'Ahmet', 'Yılmaz', 'Bilgisayar Mühendisliği'),
(2, 3, 'Doç. Dr.', 'Elif', 'Kaya', 'Yazılım Mühendisliği'),
(3, 4, 'Dr. Öğr. Üyesi', 'Mehmet', 'Demir', 'Bilişim Sistemleri Mühendisliği');


-- C. ÖĞRENCİ BİLGİLERİ (Başlangıç GNO'ları 0.00 veya tahmini değerler)
INSERT INTO students (id, user_id, student_number, first_name, last_name, gpa) VALUES
(1, 5, '2026001', 'Ali', 'Öztürk', 3.25),
(2, 6, '2026002', 'Ayşe', 'Yılmaz', 3.80),
(3, 7, '2026003', 'Can', 'Demir', 2.45),
(4, 8, '2026004', 'Fatma', 'Şahin', 3.10),
(5, 9, '2026005', 'Burak', 'Aslan', 2.90),
(6, 10, '2026006', 'Zeynep', 'Çelik', 3.65),
(7, 11, '2026007', 'Mert', 'Koç', 2.10),
(8, 12, '2026008', 'Gamze', 'Turan', 3.40),
(9, 13, '2026009', 'Emre', 'Kara', 2.75),
(10, 14, '2026010', 'Selin', 'Yıldız', 3.95);


-- D. 10 DERS TANIMLAMASI
INSERT INTO courses (id, course_code, course_name, credits, academician_id) VALUES
(1, 'BM101', 'Programlamaya Giriş', 4, 1),
(2, 'BM202', 'Veri Yapıları ve Algoritmalar', 4, 1),
(3, 'BM303', 'Veritabanı Yönetim Sistemleri', 3, 2),
(4, 'BM404', 'Yazılım Mühendisliği', 3, 2),
(5, 'BM205', 'Nesne Yönelimli Programlama', 4, 3),
(6, 'BM306', 'Web Tasarımı ve Geliştirme', 3, 3),
(7, 'BM407', 'İleri Programlama', 3, 1),
(8, 'BM308', 'İşletim Sistemleri', 3, 2),
(9, 'BM109', 'Matematik I', 4, 3),
(10, 'BM210', 'Lineer Cebir', 3, 1);


-- E. ÖĞRENCİ DERS KAYITLARI (Her öğrenciye birkaç ders tanımlayalım)
INSERT INTO student_courses (id, student_id, course_id) VALUES
-- Öğrenci 1 (Ali)
(1, 1, 1), (2, 1, 3), (3, 1, 7), (4, 1, 9),
-- Öğrenci 2 (Ayşe)
(5, 2, 1), (6, 2, 3), (7, 2, 7), (8, 2, 8),
-- Öğrenci 3 (Can)
(9, 3, 2), (10, 3, 5), (11, 3, 9), (12, 3, 10),
-- Öğrenci 4 (Fatma)
(13, 4, 2), (14, 4, 6), (15, 4, 8), (16, 4, 10),
-- Öğrenci 5 (Burak)
(17, 5, 1), (18, 5, 5), (19, 5, 7), (20, 5, 9),
-- Öğrenci 6 (Zeynep)
(21, 6, 3), (22, 6, 4), (23, 6, 7), (24, 6, 8),
-- Öğrenci 7 (Mert)
(25, 7, 2), (26, 7, 5), (27, 7, 6), (28, 7, 10),
-- Öğrenci 8 (Gamze)
(29, 8, 1), (30, 8, 4), (31, 8, 7), (32, 8, 9),
-- Öğrenci 9 (Emre)
(33, 9, 2), (34, 9, 3), (35, 9, 6), (36, 9, 10),
-- Öğrenci 10 (Selin)
(37, 10, 3), (38, 10, 4), (39, 10, 7), (40, 10, 8);


-- F. NOTLARIN EKLENMESİ (grades)
-- Vize: %30, Final: %40, Proje: %20, Sunum: %10
INSERT INTO grades (student_course_id, midterm, final, project, presentation, average, letter_grade) VALUES
-- Öğrenci 1 (Ali)
(1, 75.00, 80.00, 85.00, 90.00, 80.50, 'BB'),
(2, 60.00, 70.00, 75.00, 80.00, 69.00, 'CC'),
(3, 85.00, 90.00, 95.00, 100.00, 90.50, 'AA'),
(4, 50.00, 55.00, 60.00, 70.00, 56.00, 'FD'),
-- Öğrenci 2 (Ayşe)
(5, 95.00, 95.00, 100.00, 100.00, 96.50, 'AA'),
(6, 90.00, 85.00, 90.00, 95.00, 88.50, 'BA'),
(7, 88.00, 92.00, 90.00, 90.00, 90.20, 'AA'),
(8, 85.00, 80.00, 85.00, 90.00, 83.50, 'BB'),
-- Öğrenci 3 (Can)
(9, 45.00, 50.00, 60.00, 50.00, 50.50, 'DD'),
(10, 55.00, 60.00, 55.00, 70.00, 58.50, 'DD'),
(11, 40.00, 45.00, 50.00, 50.00, 45.00, 'FF'),
(12, 60.00, 65.00, 70.00, 60.00, 64.00, 'DC'),
-- Öğrenci 4 (Fatma)
(13, 70.00, 75.00, 80.00, 80.00, 75.00, 'CB'),
(14, 80.00, 75.00, 85.00, 90.00, 80.00, 'BB'),
(15, 65.00, 70.00, 75.00, 70.00, 69.50, 'CC'),
(16, 75.00, 80.00, 85.00, 80.00, 79.50, 'CB'),
-- Öğrenci 5 (Burak)
(17, 70.00, 65.00, 70.00, 80.00, 69.00, 'CC'),
(18, 60.00, 70.00, 75.00, 70.00, 68.00, 'CC'),
(19, 75.00, 80.00, 80.00, 85.00, 79.00, 'CB'),
(20, 55.00, 60.00, 65.00, 70.00, 60.50, 'DD'),
-- Öğrenci 6 (Zeynep)
(21, 85.00, 90.00, 95.00, 90.00, 89.50, 'BA'),
(22, 90.00, 95.00, 90.00, 95.00, 92.50, 'AA'),
(23, 80.00, 85.00, 90.00, 90.00, 85.00, 'BA'),
(24, 85.00, 80.00, 90.00, 85.00, 84.00, 'BB'),
-- Öğrenci 7 (Mert)
(25, 40.00, 50.00, 45.00, 50.00, 46.00, 'FF'),
(26, 50.00, 55.00, 60.00, 60.00, 55.00, 'FD'),
(27, 55.00, 50.00, 50.00, 60.00, 52.50, 'DD'),
(28, 45.00, 45.00, 50.00, 55.00, 46.50, 'FF'),
-- Öğrenci 8 (Gamze)
(29, 80.00, 85.00, 90.00, 90.00, 85.00, 'BA'),
(30, 85.00, 80.00, 85.00, 90.00, 83.50, 'BB'),
(31, 75.00, 80.00, 80.00, 85.00, 79.00, 'CB'),
(32, 90.00, 90.00, 95.00, 95.00, 91.50, 'AA'),
-- Öğrenci 9 (Emre)
(33, 60.00, 65.00, 70.00, 75.00, 65.50, 'DC'),
(34, 70.00, 70.00, 75.00, 80.00, 72.00, 'CC'),
(35, 65.00, 70.00, 65.00, 70.00, 67.50, 'CC'),
(36, 55.00, 60.00, 60.00, 70.00, 59.50, 'DD'),
-- Öğrenci 10 (Selin)
(37, 95.00, 100.00, 95.00, 100.00, 97.50, 'AA'),
(38, 90.00, 95.00, 95.00, 95.00, 93.50, 'AA'),
(39, 95.00, 95.00, 100.00, 100.00, 96.50, 'AA'),
(40, 90.00, 90.00, 95.00, 95.00, 91.50, 'AA');


-- G. DEVAMSIZLIK KAYITLARI (attendance)
-- Her öğrenci-ders için birkaç haftalık devam/devamsızlık kaydı
INSERT INTO attendance (student_course_id, week_number, status) VALUES
-- Öğrenci 1 dersleri (Ali)
(1, 1, 'Present'), (1, 2, 'Present'), (1, 3, 'Absent'), (1, 4, 'Present'),
(2, 1, 'Present'), (2, 2, 'Present'), (2, 3, 'Present'), (2, 4, 'Present'),
(3, 1, 'Present'), (3, 2, 'Absent'), (3, 3, 'Absent'), (3, 4, 'Present'),
-- Öğrenci 2 dersleri (Ayşe)
(5, 1, 'Present'), (5, 2, 'Present'), (5, 3, 'Present'), (5, 4, 'Present'),
(6, 1, 'Present'), (6, 2, 'Present'), (6, 3, 'Present'), (6, 4, 'Present'),
(7, 1, 'Present'), (7, 2, 'Present'), (7, 3, 'Present'), (7, 4, 'Present'),
-- Öğrenci 6 dersleri (Zeynep)
(21, 1, 'Present'), (21, 2, 'Absent'), (21, 3, 'Present'), (21, 4, 'Present'),
(22, 1, 'Present'), (22, 2, 'Present'), (22, 3, 'Present'), (22, 4, 'Present'),
(23, 1, 'Present'), (23, 2, 'Present'), (23, 3, 'Absent'), (23, 4, 'Present');
