# -*- coding: utf-8 -*-
"""
OBS Uygulaması Entegrasyon ve Arayüz (Jinja2) Test Kodu
Bu testler veritabanı bağlantılarını taklit ederek (mocking)
Flask rotalarının ve şablon (template) render işlemlerinin hatasız çalıştığını doğrular.
"""

import unittest
from unittest.mock import patch, MagicMock
from app import app, calculate_grade

class TestOBSSystem(unittest.TestCase):
    
    def setUp(self):
        # Test istemcisini (client) ve test modunu aktif et
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_calculate_grade(self):
        """Not ortalaması ve harf notu hesaplama mantığını test eder."""
        # Vize %30, Final %40, Proje %20, Sunum %10
        # 80 * 0.3 + 90 * 0.4 + 100 * 0.2 + 70 * 0.1 = 24 + 36 + 20 + 7 = 87 (BA)
        avg, letter = calculate_grade(80, 90, 100, 70)
        self.assertEqual(avg, 87.0)
        self.assertEqual(letter, 'BA')
        
        # Eksik notlarda ortalama hesaplanmamalıdır
        avg, letter = calculate_grade(80, None, 100, 70)
        self.assertIsNone(avg)
        self.assertIsNone(letter)

    @patch('app.get_db_connection')
    def test_login_page_renders(self, mock_db):
        """Giriş sayfasının sorunsuz yüklendiğini kontrol eder."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('OBS SYSTEM', html)
        self.assertIn('Kullanıcı Adı', html)

    @patch('app.get_db_connection')
    def test_login_success_admin(self, mock_db):
        """Admin girişi yapıldığında oturum açma ve yönlendirmeyi test eder."""
        # DB mocklama
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Kullanıcı sorgu sonucunu taklit et
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'username': 'admin',
            'password': 'admin123', # düz metin veya hash
            'role': 'admin',
            'email': 'admin@obs.edu.tr'
        }
        
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Giriş sonrası yönlendirme ile dashboard açılmalı
        html = response.data.decode('utf-8')
        self.assertIn('Sistem Yöneticisi', html)

    @patch('app.get_db_connection')
    def test_dashboard_renders_without_crashing(self, mock_db):
        """Dashboard'un tüm istatistiklerle hatasız render edildiğini doğrular."""
        # DB mocklama
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Dashboard sorgularını taklit et
        # Toplam öğrenci, akademisyen, ders sayıları ve başarı oranı sorguları sırasıyla
        mock_cursor.fetchone.side_effect = [
            {'count': 10}, # total_students
            {'count': 3},  # total_academicians
            {'count': 10}, # total_courses
            {'rate': 85.5} # success_rate
        ]
        
        # Oturumu (session) simüle et
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['email'] = 'admin@obs.edu.tr'
            sess['full_name'] = 'Sistem Yöneticisi'
            
        response = self.client.get('/?page=dashboard')
        self.assertEqual(response.status_code, 200)
        # Arayüzdeki kart değerlerini kontrol et
        html = response.data.decode('utf-8')
        self.assertIn('10', html)
        self.assertIn('%85.5', html)
        self.assertIn('Sistem Başarı Oranı', html)

    @patch('app.get_db_connection')
    def test_student_dashboard_renders(self, mock_db):
        """Öğrenci dashboard paneli ve verilerinin sorunsuz yüklendiğini kontrol eder."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Sırasıyla: total_students, total_academicians, total_courses, success_rate, student_gpa, student_courses_count, student_absent_count
        mock_cursor.fetchone.side_effect = [
            {'count': 10},
            {'count': 3},
            {'count': 10},
            {'rate': 85.5},
            {'gpa': 3.25},
            {'count': 4},
            {'count': 2}
        ]
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 5
            sess['username'] = 'ogr_ali'
            sess['role'] = 'student'
            sess['student_id'] = 1
            sess['student_number'] = '2026001'
            sess['full_name'] = 'Ali Öztürk'
            
        response = self.client.get('/?page=dashboard')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('3.25 / 4.00', html)
        self.assertIn('2 gün', html)

    @patch('app.get_db_connection')
    def test_academician_courses_page_renders(self, mock_db):
        """Akademisyen dersler sayfasının sorunsuz yüklendiğini kontrol eder."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'course_code': 'BM101', 'course_name': 'Programlamaya Giriş', 'credits': 4, 'student_count': 5},
            {'id': 2, 'course_code': 'BM202', 'course_name': 'Veri Yapıları', 'credits': 4, 'student_count': 3}
        ]
        
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['username'] = 'prof_ahmet'
            sess['role'] = 'academician'
            sess['academician_id'] = 1
            sess['full_name'] = 'Prof. Dr. Ahmet Yılmaz'
            
        response = self.client.get('/?page=courses')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn('BM101', html)
        self.assertIn('Programlamaya Giriş', html)

if __name__ == '__main__':
    unittest.main()
