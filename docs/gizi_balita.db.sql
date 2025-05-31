BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS balita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            tanggal_lahir DATE NOT NULL,
            jenis_kelamin TEXT NOT NULL CHECK (jenis_kelamin IN ('L', 'P')),
            nama_ortu TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , usia_tahun INTEGER, usia_bulan INTEGER, nik TEXT, provinsi VARCHAR(255) DEFAULT 'Banten', kabupaten VARCHAR(255) DEFAULT 'Lebak', kecamatan VARCHAR(255) DEFAULT 'Cimarga', puskesmas VARCHAR(255) DEFAULT 'Cimarga', desa VARCHAR(255), rt VARCHAR(10), rw VARCHAR(10), alamat_detail TEXT);
CREATE TABLE IF NOT EXISTS dataset_lvq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature1 REAL,
    feature2 REAL,
    feature3 REAL,
    target TEXT
);
CREATE TABLE IF NOT EXISTS dataset_training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature1 REAL NOT NULL,
            feature2 REAL NOT NULL,
            feature3 REAL NOT NULL,
            target TEXT NOT NULL
        );
CREATE TABLE IF NOT EXISTS desa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        , alamat TEXT, tempat_lahir TEXT, tanggal_lahir DATE, pendidikan TEXT, email TEXT, photo TEXT);
COMMIT;
