import json
from datetime import datetime, timedelta
import sqlite3
import random
from faker import Faker
import hashlib

class Hasta:
    def __init__(self, hasta_id, ad, soyad, dogum_tarihi, cinsiyet, telefon, adres, kullanici_adi, sifre):
        self.hasta_id = hasta_id
        self.ad = ad
        self.soyad = soyad
        self.dogum_tarihi = dogum_tarihi
        self.cinsiyet = cinsiyet
        self.telefon = telefon
        self.adres = adres
        self.kullanici_adi = kullanici_adi
        self.sifre = sifre

class Doktor:
    def __init__(self, doktor_id, ad, soyad, uzmanlik_alani, hastane, kullanici_adi, sifre):
        self.doktor_id = doktor_id
        self.ad = ad
        self.soyad = soyad
        self.uzmanlik_alani = uzmanlik_alani
        self.hastane = hastane
        self.kullanici_adi = kullanici_adi
        self.sifre = sifre

class Yonetici:
    def __init__(self, yonetici_id, ad, soyad, kullanici_adi, sifre):
        self.yonetici_id = yonetici_id
        self.ad = ad
        self.soyad = soyad
        self.kullanici_adi = kullanici_adi
        self.sifre = sifre

class Randevu:
    def __init__(self, randevu_id, randevu_tarihi, randevu_saati, hasta_id, doktor_id):
        self.randevu_id = randevu_id
        self.randevu_tarihi = randevu_tarihi
        self.randevu_saati = randevu_saati
        self.hasta_id = hasta_id
        self.doktor_id = doktor_id

class TibbiRapor:
    def __init__(self, rapor_id, rapor_tarihi, rapor_icerigi, hasta_id):
        self.rapor_id = rapor_id
        self.rapor_tarihi = rapor_tarihi
        self.rapor_icerigi = rapor_icerigi
        self.hasta_id = hasta_id

    def json_formatinda(self):
        return json.dumps({
            "rapor_id": self.rapor_id,
            "rapor_tarihi": self.rapor_tarihi.strftime("%Y-%m-%d"),
            "rapor_icerigi": self.rapor_icerigi,
        })

def hash_sifre(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

fake = Faker()

uzmanlik_alanlari = [
    "Dahiliye", "Cerrahi", "Kardiyoloji", "Pediatri", "Jinekoloji",
    "Psikiyatri", "Dermatoloji", "Nöroloji", "Endokrinoloji", 
    "Gastroenteroloji", "Onkoloji", "Üroloji", "Hematoloji", 
    "Radyoloji", "Anesteziyoloji"
]

def veritabani_guncelle():
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE TibbiRaporlar ADD COLUMN hasta_id INTEGER")
    except sqlite3.OperationalError:
        print("TibbiRaporlar tablosunda hasta_id sütunu zaten mevcut.")

    try:
        cursor.execute("ALTER TABLE Randevular ADD COLUMN hasta_id INTEGER")
    except sqlite3.OperationalError:
        print("Randevular tablosunda hasta_id sütunu zaten mevcut.")
    
    try:
        cursor.execute("ALTER TABLE Randevular ADD COLUMN doktor_id INTEGER")
    except sqlite3.OperationalError:
        print("Randevular tablosunda doktor_id sütunu zaten mevcut.")
        
    try:
        cursor.execute("ALTER TABLE TibbiRaporlar ADD COLUMN RaporURL TEXT")
    except sqlite3.OperationalError:
        print("TibbiRaporlar tablosunda RaporURL sütunu zaten mevcut.")

    conn.commit()
    conn.close()

veritabani_guncelle()

conn = sqlite3.connect('hastane.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS Hastalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ad TEXT NOT NULL,
                    Soyad TEXT NOT NULL,
                    DogumTarihi DATE,
                    Cinsiyet TEXT,
                    Telefon TEXT,
                    Adres TEXT,
                    KullaniciAdi TEXT UNIQUE,
                    Sifre TEXT
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Doktorlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ad TEXT NOT NULL,
                    Soyad TEXT NOT NULL,
                    UzmanlikAlani TEXT,
                    CalistigiHastane TEXT,
                    KullaniciAdi TEXT UNIQUE,
                    Sifre TEXT
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Yoneticiler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Ad TEXT NOT NULL,
                    Soyad TEXT NOT NULL,
                    KullaniciAdi TEXT UNIQUE,
                    Sifre TEXT
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS Randevular (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    RandevuTarihi DATE,
                    RandevuSaati TEXT,
                    hasta_id INTEGER,
                    doktor_id INTEGER
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS TibbiRaporlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    RaporTarihi DATE NOT NULL,
                    RaporIcerigi TEXT NOT NULL,
                    RaporURL TEXT,
                    RaporJSON TEXT,
                    hasta_id INTEGER,
                    doktor_id INTEGER,
                    FOREIGN KEY (hasta_id) REFERENCES Hastalar(id),
                    FOREIGN KEY (doktor_id) REFERENCES Doktorlar(id)
                )''')

cursor.execute("SELECT COUNT(*) FROM Hastalar")
hasta_sayisi = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Doktorlar")
doktor_sayisi = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Yoneticiler")
yonetici_sayisi = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Randevular")
randevu_sayisi = cursor.fetchone()[0]

if hasta_sayisi == 0:
    hasta_verileri = []
    for i in range(1, 10000):
        kullanici_adi = fake.first_name().lower() + '.' + fake.last_name().lower() + str(random.randint(100, 999))
        sifre = ''.join(random.choice('1') for i in range(5))
        hasta = Hasta(i, fake.first_name(), fake.last_name(), fake.date_of_birth(), random.choice(['Erkek', 'Kadın']), fake.phone_number(), fake.address(), kullanici_adi, hash_sifre(sifre))
        hasta_verileri.append(hasta)

    for hasta in hasta_verileri:
        cursor.execute('''INSERT INTO Hastalar (Ad, Soyad, DogumTarihi, Cinsiyet, Telefon, Adres, KullaniciAdi, Sifre)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (hasta.ad, hasta.soyad, hasta.dogum_tarihi, hasta.cinsiyet, hasta.telefon, hasta.adres, hasta.kullanici_adi, hasta.sifre))

if doktor_sayisi == 0:
    doktor_verileri = []
    for i in range(1, 500):
        kullanici_adi = fake.first_name().lower() + '.' + fake.last_name().lower() + str(random.randint(100, 999))
        sifre = ''.join(random.choice('1') for i in range(5))
        uzmanlik_alani = random.choice(uzmanlik_alanlari)
        doktor = Doktor(i, fake.first_name(), fake.last_name(), uzmanlik_alani, fake.company(), kullanici_adi, hash_sifre(sifre))
        doktor_verileri.append(doktor)

    for doktor in doktor_verileri:
        cursor.execute('''INSERT INTO Doktorlar (Ad, Soyad, UzmanlikAlani, CalistigiHastane, KullaniciAdi, Sifre)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (doktor.ad, doktor.soyad, doktor.uzmanlik_alani, doktor.hastane, doktor.kullanici_adi, doktor.sifre))

if yonetici_sayisi == 0:
    yonetici_verileri = []
    for i in range(1, 10):
        kullanici_adi = fake.first_name().lower() + '.' + fake.last_name().lower() + str(random.randint(100, 999))
        sifre = ''.join(random.choice('1') for i in range(5))
        yonetici = Yonetici(i, fake.first_name(), fake.last_name(), kullanici_adi, hash_sifre(sifre))
        yonetici_verileri.append(yonetici)

    for yonetici in yonetici_verileri:
        cursor.execute('''INSERT INTO Yoneticiler (Ad, Soyad, KullaniciAdi, Sifre)
                          VALUES (?, ?, ?, ?)''',
                       (yonetici.ad, yonetici.soyad, yonetici.kullanici_adi, yonetici.sifre))

if randevu_sayisi == 0:
    cursor.execute("SELECT id FROM Hastalar")
    hasta_idler = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id FROM Doktorlar")
    doktor_idler = [row[0] for row in cursor.fetchall()]

    randevu_verileri = []
    for i in range(1, 8000):
        randevu_tarihi = fake.date_between(start_date='today', end_date='+30d')
        randevu_saati = fake.time(pattern="%H:%M:%S", end_datetime=None)
        hasta_id = random.choice(hasta_idler)
        doktor_id = random.choice(doktor_idler)
        randevu = Randevu(i, randevu_tarihi, randevu_saati, hasta_id, doktor_id)
        randevu_verileri.append(randevu)

    for randevu in randevu_verileri:
        cursor.execute('''INSERT INTO Randevular (RandevuTarihi, RandevuSaati, hasta_id, doktor_id)
                          VALUES (?, ?, ?, ?)''',
                       (randevu.randevu_tarihi, randevu.randevu_saati, randevu.hasta_id, randevu.doktor_id))

conn.commit()
conn.close()
