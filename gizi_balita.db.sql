BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS balita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            tanggal_lahir DATE NOT NULL,
            jenis_kelamin TEXT NOT NULL CHECK (jenis_kelamin IN ('L', 'P')),
            nama_ortu TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , usia_tahun INTEGER, usia_bulan INTEGER);
CREATE TABLE IF NOT EXISTS dataset_training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature1 REAL NOT NULL,
            feature2 REAL NOT NULL,
            feature3 REAL NOT NULL,
            target TEXT NOT NULL
        );
CREATE TABLE IF NOT EXISTS klasifikasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pengukuran_id INTEGER UNIQUE NOT NULL,
            status_gizi TEXT NOT NULL CHECK (status_gizi IN ('normal', 'kurang', 'lebih', 'buruk')),
            tanggal_klasifikasi DATE NOT NULL,
            FOREIGN KEY (pengukuran_id) REFERENCES pengukuran (id) ON DELETE CASCADE
        );
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
        );
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
        );
CREATE TABLE IF NOT EXISTS pengukuran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balita_id INTEGER NOT NULL,
            tanggal_ukur DATE NOT NULL,
            berat_badan REAL NOT NULL CHECK (berat_badan > 0),
            tinggi_badan REAL NOT NULL CHECK (tinggi_badan > 0),
            lingkar_lengan REAL NOT NULL CHECK (lingkar_lengan > 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (balita_id) REFERENCES balita (id) ON DELETE CASCADE
        );
CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
INSERT INTO "balita" ("id","nama","tanggal_lahir","jenis_kelamin","nama_ortu","created_at","updated_at","usia_tahun","usia_bulan") VALUES (1,'jawa','2024-02-07','L','andre','2025-05-07 06:15:17','2025-05-07 06:15:17',NULL,NULL),
 (2,'cina','2024-02-21','P','cinis','2025-05-07 06:22:09','2025-05-07 06:22:09',NULL,NULL),
 (3,'batak','2023-01-31','L','siraeils','2025-05-07 06:22:27','2025-05-07 06:22:27',NULL,NULL),
 (4,'minang','2023-03-15','P','susan','2025-05-07 06:22:44','2025-05-07 06:22:44',NULL,NULL),
 (5,'mail','2024-04-01','L','andri','2025-05-08 04:07:34','2025-05-08 04:07:34',NULL,NULL),
 (10,'asam','2021-12-08','L','caca','2025-05-08 06:56:37','2025-05-08 06:56:37',NULL,NULL),
 (11,'urat','2021-05-08','P','cici','2025-05-08 06:56:37','2025-05-08 06:56:37',NULL,NULL),
 (12,'paisal','2024-06-08','P','cucu','2025-05-08 06:56:37','2025-05-08 06:56:37',NULL,NULL),
 (13,'amir','2022-03-08','L','anis','2025-05-08 06:56:37','2025-05-08 06:56:37',NULL,NULL);
INSERT INTO "klasifikasi" ("id","pengukuran_id","status_gizi","tanggal_klasifikasi") VALUES (5,5,'buruk','2025-05-07'),
 (6,6,'buruk','2025-05-07'),
 (7,7,'normal','2025-05-07'),
 (8,8,'kurang','2025-05-07'),
 (9,9,'kurang','2025-05-08'),
 (10,14,'normal','2025-05-08'),
 (11,15,'buruk','2025-05-08'),
 (12,16,'normal','2025-05-08'),
 (13,17,'buruk','2025-05-08');
INSERT INTO "parameter_history" ("id","parameter_id","changed_by","nilai_k","bobot_berat","bobot_tinggi","bobot_lila","bobot_umur","bobot_jk","changed_at") VALUES (1,1,1,3,0.35,0.3,0.15,0.15,0.05,'2025-05-07 06:14:56');
INSERT INTO "parameter_knn" ("id","nilai_k","bobot_berat","bobot_tinggi","bobot_lila","bobot_umur","bobot_jk","created_at") VALUES (1,3,0.35,0.3,0.15,0.15,0.05,'2025-05-07 06:12:37');
INSERT INTO "pengukuran" ("id","balita_id","tanggal_ukur","berat_badan","tinggi_badan","lingkar_lengan","created_at") VALUES (5,3,'2025-05-07',5.0,60.0,10.0,'2025-05-07 21:25:40'),
 (6,4,'2025-05-07',6.5,70.0,11.0,'2025-05-07 21:26:11'),
 (7,1,'2025-05-07',8.0,70.0,13.0,'2025-05-07 21:26:38'),
 (8,2,'2025-05-07',14.0,42.0,10.1,'2025-05-07 21:27:15'),
 (9,5,'2025-05-08',10.0,100.0,12.0,'2025-05-08 04:08:28'),
 (14,10,'2025-05-08',11.5,70.0,13.0,'2025-05-08 06:56:37'),
 (15,11,'2025-05-08',13.0,69.0,11.0,'2025-05-08 06:56:37'),
 (16,12,'2025-05-08',15.0,75.0,15.0,'2025-05-08 06:56:37'),
 (17,13,'2025-05-08',10.0,55.0,10.5,'2025-05-08 06:56:37');
INSERT INTO "users" ("id","username","password","nama_lengkap","role","created_at") VALUES (1,'admin','scrypt:32768:8:1$IaCQlMj5qtuvk8Lv$d0b5b403785cacc9640970c5dda71b8b71acd3e08a6d26ba97bd87809142828b8c764cd2eae2013696971728b45ba1e7e3edc76bf46e27a78581037cd59f295f','Administrator','admin','2025-05-07 06:12:37'),
 (2,'Andri','scrypt:32768:8:1$517akxrU3ygwB4ht$cd964ef8e448c4a63a9c8bef7ac93b52dec818638ead27eb94baf49396c0e026f7ac127cdf3dc990fd894a416897210778f161cb1c8e74e0cb7dc077f001a345','Kurniawan','user','2025-05-07 07:51:00'),
 (3,'andre','scrypt:32768:8:1$au788pvk4BW39HyM$a0ddf0ea377bebd425ac035797f80d83ec04ede4f68b2234fb0d95f298ce30dbde23fa3e84d9ad18dda8f7100acf19b4819af43d7abe986d215b00781c0916d6','Cinas','user','2025-05-07 21:03:28');
COMMIT;
