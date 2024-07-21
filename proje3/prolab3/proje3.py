from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
import dropbox
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DROPBOX_ACCESS_TOKEN = 'sl.B1gzS-igTc6yj3fT5q8Q8hJCo-9QGedClfc0TP2Nb8Z8bVmq7OTM1td3uXWrI9bht25XyQxiQnk6zmHMug83hvqMyDtqI0Do1W_Afbv3zarzyDbPrLRqHNknac5CQzek0Xz5uD5x51kYb5c'

def hash_sifre(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def kullanici_giris(kullanici_adi, sifre, tip):
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    if tip == 'hasta':
        cursor.execute("SELECT * FROM Hastalar WHERE KullaniciAdi = ? AND Sifre = ?", (kullanici_adi, hash_sifre(sifre)))
    elif tip == 'doktor':
        cursor.execute("SELECT * FROM Doktorlar WHERE KullaniciAdi = ? AND Sifre = ?", (kullanici_adi, hash_sifre(sifre)))
    elif tip == 'yonetici':
        cursor.execute("SELECT * FROM Yoneticiler WHERE KullaniciAdi = ? AND Sifre = ?", (kullanici_adi, hash_sifre(sifre)))
    else:
        return None

    user = cursor.fetchone()
    conn.close()

    if user:
        session['kullanici_adi'] = kullanici_adi
        session['tip'] = tip
        session['user_id'] = user[0]
        return user
    else:
        return None

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    kullanici_adi = data.get('kullanici_adi')
    sifre = data.get('sifre')
    tip = data.get('tip')
    user = kullanici_giris(kullanici_adi, sifre, tip)
    if user:
        return jsonify({"success": True, "tip": tip})
    else:
        return jsonify({"success": False, "message": "Kullanıcı adı veya şifre yanlış!"})

@app.route('/hasta-ekle', methods=['POST'])
def hasta_ekle():
    data = request.json
    ad = data.get('ad')
    soyad = data.get('soyad')
    dogum_tarihi = data.get('dogum_tarihi')
    cinsiyet = data.get('cinsiyet')
    telefon = data.get('telefon')
    adres = data.get('adres')
    kullanici_adi = data.get('kullanici_adi')
    sifre = hash_sifre(data.get('sifre'))

    for i in range(5):
        try:
            with sqlite3.connect('hastane.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Hastalar (Ad, Soyad, DogumTarihi, Cinsiyet, Telefon, Adres, KullaniciAdi, Sifre) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (ad, soyad, dogum_tarihi, cinsiyet, telefon, adres, kullanici_adi, sifre))
                conn.commit()
                return jsonify({"success": True, "message": "Hasta başarıyla eklendi!"})
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                pass
            else:
                raise e

    return jsonify({"success": False, "message": "Veritabanı kilitlendi, lütfen tekrar deneyin."})

@app.route('/')
def ana_sayfa():
    return render_template('giris.html')

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'kullanici_adi' not in session:
        return jsonify({"success": False, "message": "Oturum açılmadı!"})

    data = request.json
    ad = data.get('ad')
    soyad = data.get('soyad')
    dogum_tarihi = data.get('dogum_tarihi')
    cinsiyet = data.get('cinsiyet')
    telefon = data.get('telefon')
    adres = data.get('adres')
    kullanici_adi = data.get('kullanici_adi')
    sifre = hash_sifre(data.get('sifre'))

    user_id = session['user_id']

    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE Hastalar
                      SET Ad = ?, Soyad = ?, DogumTarihi = ?, Cinsiyet = ?, Telefon = ?, Adres = ?, KullaniciAdi = ?, Sifre = ?
                      WHERE id = ?''', (ad, soyad, dogum_tarihi, cinsiyet, telefon, adres, kullanici_adi, sifre, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Profil güncellendi!"})

@app.route('/add-appointment', methods=['POST'])
def add_appointment():
    if 'kullanici_adi' not in session:
        return jsonify({"success": False, "message": "Oturum açılmadı!"})

    data = request.json
    randevu_tarihi = data.get('randevu_tarihi')
    randevu_saati = data.get('randevu_saati')

    user_id = session['user_id']
    user_tip = session['tip']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    if user_tip == 'hasta':
        hasta_id = user_id
        doktor_id = data.get('doktor_id')
    else:
        hasta_id = data.get('hasta_id')
        doktor_id = user_id

    cursor.execute("INSERT INTO Randevular (RandevuTarihi, RandevuSaati, hasta_id, doktor_id) VALUES (?, ?, ?, ?)",
                   (randevu_tarihi, randevu_saati, hasta_id, doktor_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Randevu eklendi!"})

@app.route('/doktor-ekle', methods=['POST'])
def doktor_ekle():
    data = request.json
    ad = data.get('ad')
    soyad = data.get('soyad')
    uzmanlik_alani = data.get('uzmanlik_alani')
    calistigi_hastane = data.get('calistigi_hastane')
    kullanici_adi = data.get('kullanici_adi')
    sifre = hash_sifre(data.get('sifre'))

    with sqlite3.connect('hastane.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Doktorlar (Ad, Soyad, UzmanlikAlani, CalistigiHastane, KullaniciAdi, Sifre) VALUES (?, ?, ?, ?, ?, ?)", 
                       (ad, soyad, uzmanlik_alani, calistigi_hastane, kullanici_adi, sifre))
        conn.commit()

    return jsonify({"success": True, "message": "Doktor başarıyla eklendi!"})

@app.route('/hasta-bilgileri', methods=['GET', 'POST'])
def hasta_bilgileri():
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()
        hasta_id = data.get('hasta_id')
        cursor.execute("SELECT * FROM Hastalar WHERE id = ?", (hasta_id,))
    else:
        cursor.execute("SELECT * FROM Hastalar")

    hastalar = cursor.fetchall()
    conn.close()
    return jsonify(hastalar)

@app.route('/doktor-bilgileri', methods=['GET', 'POST'])
def doktor_bilgileri():
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()
        doktor_id = data.get('doktor_id')
        cursor.execute("SELECT * FROM Doktorlar WHERE id = ?", (doktor_id,))
    else:
        cursor.execute("SELECT * FROM Doktorlar")

    doktorlar = cursor.fetchall()
    conn.close()
    return jsonify(doktorlar)

@app.route('/rapor-bilgileri', methods=['GET'])
def rapor_bilgileri():
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TibbiRaporlar")
    raporlar = cursor.fetchall()
    conn.close()
    return jsonify(raporlar)

@app.route('/rapor-ekle-doktor', methods=['POST'])
def rapor_ekle_doktor():
    if 'kullanici_adi' not in session or session['tip'] != 'doktor':
        return jsonify({"success": False, "message": "Oturum açılmadı!"})

    hasta_id = request.form['hasta_id']
    rapor_tarih = request.form['rapor_tarihi']
    rapor_icerik = request.form['rapor_icerigi']
    file = request.files['rapor_dosya']
    
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    filename = secure_filename(file.filename)
    file_path = '/raporlar/' + filename
    try:
        dbx.files_upload(file.read(), file_path)
    except dropbox.exceptions.ApiError as e:
        if isinstance(e.error, dropbox.files.UploadError) and e.error.is_path() and e.error.get_path().is_conflict():
            print(f"File {file_path} already exists.")
        else:
            raise e
    try:
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        rapor_url = shared_link_metadata.url.replace('?dl=0', '?dl=1')
    except dropbox.exceptions.ApiError as e:
        if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError) and e.error.is_shared_link_already_exists():
            shared_links = dbx.sharing_list_shared_links(path=file_path)
            rapor_url = shared_links.links[0].url.replace('?dl=0', '?dl=1')
        else:
            raise e

    user_id = session['user_id']

    for i in range(5):
        try:
            with sqlite3.connect('hastane.db', timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO TibbiRaporlar (RaporTarihi, RaporIcerigi, RaporURL, hasta_id, doktor_id) VALUES (?, ?, ?, ?, ?)",
                               (rapor_tarih, rapor_icerik, rapor_url, hasta_id, user_id))
                conn.commit()
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                pass
            else:
                raise e

    return jsonify({"success": True, "message": "Rapor başarıyla eklendi!"})

@app.route('/doktor-hasta-raporlari', methods=['GET'])
def doktor_hasta_raporlari():
    if 'kullanici_adi' not in session or session['tip'] != 'doktor':
        return jsonify({"success": False, "message": "Oturum açılmadı!"})

    doktor_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TibbiRaporlar.id, TibbiRaporlar.RaporTarihi, TibbiRaporlar.RaporIcerigi, Hastalar.Ad, Hastalar.Soyad, TibbiRaporlar.RaporURL
        FROM TibbiRaporlar
        JOIN Hastalar ON TibbiRaporlar.hasta_id = Hastalar.id
        WHERE TibbiRaporlar.doktor_id = ?
    """, (doktor_id,))
    raporlar = cursor.fetchall()
    conn.close()

    rapor_listesi = []
    for rapor in raporlar:
        rapor_dict = {
            'id': rapor[0],
            'rapor_tarihi': rapor[1],
            'rapor_icerigi': rapor[2],
            'hasta_ad': rapor[3],
            'hasta_soyad': rapor[4],
            'rapor_url': rapor[5]
        }
        rapor_listesi.append(rapor_dict)

    return jsonify(rapor_listesi)

@app.route('/doktor-paneli')
def doktor_paneli():
    if 'kullanici_adi' not in session or session['tip'] != 'doktor':
        return redirect(url_for('ana_sayfa'))

    doktor_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Doktorlar WHERE id = ?", (doktor_id,))
    doktor = cursor.fetchone()
    conn.close()
    return render_template('doktor_paneli.html', doktor=doktor)

@app.route('/hasta-raporlarim', methods=['GET'])
def hasta_raporlarim():
    if 'kullanici_adi' not in session or session['tip'] != 'hasta':
        return redirect(url_for('ana_sayfa'))

    user_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, RaporTarihi, RaporIcerigi, RaporURL FROM TibbiRaporlar WHERE hasta_id = ?", (user_id,))
    raporlar = cursor.fetchall()
    conn.close()

    rapor_listesi = []
    for rapor in raporlar:
        rapor_dict = {
            'id': rapor[0],
            'rapor_tarihi': rapor[1],
            'rapor_icerigi': rapor[2],
            'rapor_url': rapor[3]
        }
        rapor_listesi.append(rapor_dict)

    return render_template('raporlarim.html', raporlar=rapor_listesi)

@app.route('/randevular', methods=['GET'])
def randevular():
    if 'kullanici_adi' not in session or session['tip'] != 'hasta':
        return redirect(url_for('ana_sayfa'))

    user_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Randevular.id, RandevuTarihi, RandevuSaati, Doktorlar.Ad, Doktorlar.Soyad
        FROM Randevular
        JOIN Doktorlar ON Randevular.doktor_id = Doktorlar.id
        WHERE Randevular.hasta_id = ?
    """, (user_id,))
    randevular = cursor.fetchall()
    conn.close()
    return render_template('randevular.html', randevular=randevular)

@app.route('/doktor-hasta-randevulari', methods=['GET'])
def doktor_hasta_randevulari():
    if 'kullanici_adi' not in session or session['tip'] != 'doktor':
        return redirect(url_for('ana_sayfa'))

    doktor_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Randevular.id, RandevuTarihi, RandevuSaati, Hastalar.Ad, Hastalar.Soyad, Hastalar.Telefon, Hastalar.Adres
        FROM Randevular
        JOIN Hastalar ON Randevular.hasta_id = Hastalar.id
        WHERE Randevular.doktor_id = ?
    """, (doktor_id,))
    randevular = cursor.fetchall()
    conn.close()
    return jsonify(randevular)

@app.route('/hasta-sil/<int:id>', methods=['DELETE'])
def hasta_sil(id):
    with sqlite3.connect('hastane.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Hastalar WHERE id = ?", (id,))
        conn.commit()
    return jsonify({"success": True, "message": "Hasta başarıyla silindi!"})

@app.route('/doktor-sil/<int:id>', methods=['DELETE'])
def doktor_sil(id):
    with sqlite3.connect('hastane.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Doktorlar WHERE id = ?", (id,))
        conn.commit()
    return jsonify({"success": True, "message": "Doktor başarıyla silindi!"})

@app.route('/rapor-sil/<int:id>', methods=['DELETE'])
def rapor_sil(id):
    with sqlite3.connect('hastane.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TibbiRaporlar WHERE id = ?", (id,))
        conn.commit()
    return jsonify({"success": True, "message": "Rapor başarıyla silindi!"})

@app.route('/randevu-sil/<int:id>', methods=['DELETE'])
def randevu_sil(id):
    with sqlite3.connect('hastane.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Randevular WHERE id = ?", (id,))
        conn.commit()
    return jsonify({"success": True, "message": "Randevu başarıyla silindi!"})

@app.route('/yonetici-paneli', methods=['GET', 'POST'])
def yonetici_paneli():
    if 'kullanici_adi' not in session or session['tip'] != 'yonetici':
        return redirect(url_for('ana_sayfa'))

    yonetici_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.get_json()
        ad = data['ad']
        soyad = data['soyad']
        kullanici_adi = data['kullanici_adi']
        sifre = data['sifre']

        if sifre:
            sifre = hash_sifre(sifre)
            cursor.execute('''UPDATE Yoneticiler
                            SET Ad = ?, Soyad = ?, KullaniciAdi = ?, Sifre = ?
                            WHERE id = ?''', (ad, soyad, kullanici_adi, sifre, yonetici_id))
        else:
            cursor.execute('''UPDATE Yoneticiler
                            SET Ad = ?, Soyad = ?, KullaniciAdi = ?
                            WHERE id = ?''', (ad, soyad, kullanici_adi, yonetici_id))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Profil güncellendi."})

    cursor.execute("SELECT * FROM Yoneticiler WHERE id = ?", (yonetici_id,))
    yonetici = cursor.fetchone()
    conn.close()

    return render_template('yonetici_paneli.html', yonetici=yonetici)

@app.route('/doktor-randevulari')
def doktor_randevulari():
    if 'kullanici_adi' not in session or session['tip'] != 'doktor':
        return redirect(url_for('ana_sayfa'))

    doktor_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Randevular.id, RandevuTarihi, RandevuSaati, Hastalar.Ad, Hastalar.Soyad
        FROM Randevular
        JOIN Hastalar ON Randevular.hasta_id = Hastalar.id
        WHERE Randevular.doktor_id = ?
    """, (doktor_id,))
    randevular = cursor.fetchall()
    conn.close()
    return render_template('doktor_randevulari.html', randevular=randevular)

@app.route('/hasta-profil', methods=['GET', 'POST'])
def hasta_profil():
    if 'kullanici_adi' not in session:
        return redirect(url_for('ana_sayfa'))

    user_id = session['user_id']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.get_json()
        ad = data['ad']
        soyad = data['soyad']
        dogum_tarihi = data['dogum_tarihi']
        cinsiyet = data['cinsiyet']
        telefon = data['telefon']
        adres = data['adres']
        kullanici_adi = data['kullanici_adi']
        sifre = hash_sifre(data['sifre'])

        cursor.execute('''UPDATE Hastalar
                          SET Ad = ?, Soyad = ?, DogumTarihi = ?, Cinsiyet = ?, Telefon = ?, Adres = ?, KullaniciAdi = ?, Sifre = ?
                          WHERE id = ?''', (ad, soyad, dogum_tarihi, cinsiyet, telefon, adres, kullanici_adi, sifre, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Profil güncellendi."})

    cursor.execute("SELECT * FROM Hastalar WHERE id = ?", (user_id,))
    hasta = cursor.fetchone()
    conn.close()

    return render_template('hasta_profil.html', hasta=hasta)

@app.route('/randevu-ekle', methods=['GET'])
def randevu_ekle():
    if 'kullanici_adi' not in session or (session['tip'] != 'doktor' and session['tip'] != 'hasta'):
        return redirect(url_for('ana_sayfa'))

    user_id = session['user_id']
    user_tip = session['tip']
    conn = sqlite3.connect('hastane.db')
    cursor = conn.cursor()

    if user_tip == 'doktor':
        cursor.execute("SELECT id, Ad, Soyad FROM Hastalar")
        hastalar = cursor.fetchall()
        doktorlar = []
    else:
        cursor.execute("SELECT id, Ad, Soyad FROM Doktorlar")
        doktorlar = cursor.fetchall()
        hastalar = []

    conn.close()
    return render_template('randevu_ekle.html', doktorlar=doktorlar, hastalar=hastalar, user_tip=user_tip)

@app.route('/hasta-kayit', methods=['GET'])
def hasta_kayit():
    return render_template('hasta_kayit.html')

if __name__ == '__main__':
    app.run(debug=True)
