from flask import Flask, request, redirect, render_template, url_for, jsonify, session, flash
import pickle
import pandas as pd
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import os
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfigurasi Unggah
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = 'supersecretkey' 

# Buat folder untuk menyimpan file jika belum ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = os.urandom(24)

# Konfigurasi koneksi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Ensure the password is set
app.config['MYSQL_DB'] = 'musclegym'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CONNECT_TIMEOUT'] = 10  # Optional timeout

mysql = MySQL(app)

class Anggota:
    def __init__(self, id, name, gender, age, height, weight, timestamp, prediction):
        self.id = id
        self.name = name
        self.gender = gender
        self.age = age
        self.height = height
        self.weight = weight
        self.timestamp = timestamp
        self.prediction = prediction

# Model untuk user
class User:
    def __init__(self, id_user, nama, username, password, nohp, before, after):
        self.id_user = id_user
        self.nama = nama
        self.username = username 
        self.password = password
        self.nohp = nohp
        self.before = before
        self.after = after


# Memuat model
with open('svm_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

# Fungsi untuk prediksi
def Label(data):
    prediction = model.predict(data)
    return prediction

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # Koneksi ke MySQL
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()
    # Validasi username dan password
    if user:
        session['username'] = user['username']
        if user['username'] == 'destroygym1':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('dashboard_anggota'))
    else:
        error = 'Invalid credentials'
        return render_template('index.html', error=error)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard')) if session['username'] == 'destroygym1' else redirect(url_for('dashboard_anggota'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session and session['username'] == 'destroygym1':
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('index'))

@app.route('/dashboard_anggota')
def dashboard_anggota():
    if 'username' in session and session['username'] != 'destroygym1':
        return render_template('dashboard_anggota.html', username=session['username'])
    return redirect(url_for('index'))


@app.route('/hitung', methods=['GET'])  # Perlu menangani metode GET untuk menampilkan halaman form
def hitung_form():
    return render_template('hitung.html')

@app.route('/hitung', methods=['POST'])  # Perlu menangani metode POST untuk memproses data form
def hitung():
    Name = request.form['Name']
    Gender = request.form['Gender']
    Age = float(request.form['Age'])
    Height = float(request.form['Height'])
    Weight = float(request.form['Weight'])

    data = pd.DataFrame({
        'Gender': [Gender],
        'Age': [Age],
        'Height': [Height],
        'Weight': [Weight]
    })

    prediction = Label(data)

    # Tambahkan keterangan berdasarkan hasil prediksi
    if prediction == "Berat Kurang":
            message = ("Lakukan latihan 4-5 hari per minggu dengan fokus pada latihan kekuatan dan kardio ringan. "
                           "Untuk latihan kekuatan, bagi sesi menjadi upper body dan lower body. Pada hari upper body, "
                           "lakukan latihan seperti bench press, bent over row, dumbbell shoulder press, bicep curls, "
                           "dan tricep dips. Pada hari lower body, lakukan squats, deadlifts, leg press, lunges, dan "
                           "calf raises. Sisihkan satu atau dua hari untuk kardio ringan seperti jalan cepat atau "
                           "bersepeda, serta stretching dan yoga untuk pemulihan. Akhiri minggu dengan aktivitas fisik "
                           "menyenangkan seperti hiking atau berenang, dan pastikan ada hari istirahat untuk recovery "
                           "yang mencakup stretching dan foam rolling.")
    elif prediction == "Obesitas":
            message = ("Ketika sampai pada makan malam, prioritaskan minum air putih sebagai minuman utama untuk menjaga hidrasi." 
                        "Teh herbal tanpa kafein bisa menjadi pilihan yang baik sebagai minuman penutup yang menenangkan sebelum tidur."
                        "Hindari minuman beralkohol atau minuman berenergi yang dapat mengganggu kualitas tidur dan memberikan kalori tambahan yang tidak diperlukan.")
    elif prediction == "Berat Normal":
            message = ("Rutinitas gym yang terencana dengan baik adalah kunci kesuksesan dalam mencapai tujuan kebugaran."
                       "Mulai dari hari Senin yang didedikasikan untuk latihan kekuatan dan membangun otot bagian atas dengan latihan seperti bench press, pull-ups, shoulder press, dan barbel curl." 
                       "Selasa, fokusnya beralih pada kardio dan latihan otot bagian bawah melalui squat, deadlift, lunges, dan leg press. Rabu dijadwalkan sebagai hari istirahat atau pemulihan dengan yoga ringan untuk merilekskan otot-otot. Kemudian, Kamis kembali menantang otot bagian atas dengan latihan seperti lat pull-down, dumbbell bench press, dumbbell row, dan tricep dips. Jumat, intensitas meningkat kembali dengan latihan kardio intensif, seperti high-intensity interval training (HIIT), diikuti dengan latihan beban ringan untuk menjaga kebugaran. Akhir pekan digunakan untuk latihan keseimbangan dan fleksibilitas seperti yoga atau pilates, atau aktivitas luar ruangan seperti hiking, memberi tubuh kesempatan untuk pulih dan mempersiapkan diri untuk minggu berikutnya." 
                       "Hal terpenting adalah mendengarkan tubuh dan melakukan penyesuaian sesuai kebutuhan serta menjaga konsistensi dalam menjalankan jadwal latihan.")
    elif prediction == "Kelebihan Berat":
            message = ("Setiap hari latihan memiliki fokus yang berbeda untuk membantu membangun kekuatan, meningkatkan kardio, dan mendukung penurunan berat badan. Mulai dari latihan kekuatan bagian atas pada hari Senin, dengan latihan seperti bench press dan lat pull-down, hingga latihan kardio intensif pada hari Selasa dengan high-intensity interval training (HIIT), setiap sesi latihan dirancang untuk mencapai tujuan kebugaran Anda."
                       "Hari Rabu ditetapkan sebagai hari istirahat atau pemulihan dengan aktivitas ringan seperti yoga atau berjalan santai, sementara hari Kamis kembali menantang dengan latihan kekuatan bagian bawah seperti squat dan deadlift. Pada hari Jumat, Anda akan mencampur latihan kekuatan dan kardio dengan circuit training untuk memaksimalkan pembakaran kalori dan memperkuat otot-otot tubuh secara keseluruhan. Akhir pekan merupakan kesempatan untuk menjalani aktivitas yang menyenangkan seperti berenang atau hiking, yang juga membantu dalam proses penurunan berat badan."
                       "Penting untuk mengikuti jadwal latihan dengan konsisten dan mendengarkan tubuh Anda, serta berkonsultasi dengan profesional kesehatan jika diperlukan untuk memastikan program latihan yang aman dan efektif bagi kondisi tubuh Anda.")
    
    # Menyimpan data ke database
    cur = mysql.connection.cursor()
    cur.execute('''
        INSERT INTO anggota (name, gender, age, height, weight, timestamp, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (Name, Gender, Age, Height, Weight, datetime.now(), prediction[0]))
    mysql.connection.commit()
    cur.close()

    # Mendapatkan data anggota terbaru dari database
    # cur.execute("SELECT * FROM anggota ORDER BY id DESC LIMIT 1")
    # new_anggota = cur.fetchone()
    # cur.close()
    
    return render_template('hitung.html', prediction=prediction[0], message=message)
    
    return str(e)  # Untuk debug
    return render_template('hitung.html')

@app.route('/print_anggota', methods=['GET'])
def print_anggota():
    try:
        # Mengambil data anggota terbaru dari database
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, gender, age, height, weight, timestamp, prediction FROM anggota ORDER BY timestamp DESC LIMIT 1")
        anggota = cur.fetchone()
        cur.close()

        # Mengecek apakah data anggota ada
        if anggota:
            # Mengonversi hasil tuple menjadi kamus
            anggota_dict = {
                "name": anggota[0],
                "gender": anggota[1],
                "age": anggota[2],
                "height": anggota[3],
                "weight": anggota[4],
                "timestamp": anggota[5],
                "prediction": anggota[6]
            }
            return jsonify(anggota_dict)
        else:
            app.logger.warning('Tidak ada data anggota yang ditemukan.')
            return jsonify({"error": "Data anggota tidak ditemukan"}), 404
    except Exception as e:
        app.logger.error('Terjadi kesalahan: %s', e)
        return jsonify({"error": "Terjadi kesalahan pada server"}), 500

@app.route('/history')
def history():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM anggota")
    anggota_data = cur.fetchall()
    cur.close()

    anggota_list = [Anggota(row['id'], row['name'], row['gender'], row['age'], row['height'], row['weight'], row['timestamp'], row['prediction']) for row in anggota_data]

    return render_template('history.html', anggota_list=anggota_list)

@app.route('/anggota')
def anggota():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM user")
    user_data = cur.fetchall()
    cur.close()

    user_list = [User(row['id_user'], row['nama'], row['username'], row['password'], row['nohp'], row['before'], row['after']) for row in user_data]

    return render_template('anggota.html', user_list=user_list)

@app.route('/edit_anggota/<int:id_user>')
def edit_anggota(id_user):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM user")
    user_data = cur.fetchall()
    cur.close()

    user_list = [User(row['id_user'], row['nama'], row['username'], row['password'], row['nohp'], row['before'], row['after']) for row in user_data]
    user = next((user for user in user_list if user.id_user == id_user), None)
    if user:
        return render_template('edit_anggota.html', user=user)
    else:
        return "User not found", 404
    
@app.route('/update_anggota/<int:id_user>', methods=['POST'])
def update_anggota(id_user):
    # Koneksi ke MySQL untuk mengambil data user lama
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM user WHERE id_user = %s", (id_user,))
    user_data = cur.fetchone()

    if user_data:
        user_data['nama'] = request.form['nama']
        user_data['username'] = request.form['username']
        user_data['nohp'] = request.form['nohp']
        user_data['password'] = request.form['password']

        # Cek apakah file before diunggah dan disimpan dengan benar
        if 'before' in request.files and request.files['before'].filename != '':
            before_file = request.files['before']
            before_filename = secure_filename(before_file.filename)
            before_file_path = os.path.join(app.config['UPLOAD_FOLDER'], before_filename)
            before_file.save(before_file_path)
            user_data['before'] = before_filename  # Perbarui nama file di data user
            app.logger.debug(f"before file uploaded: {before_filename}")

        # Cek apakah file after diunggah dan disimpan dengan benar
        if 'after' in request.files and request.files['after'].filename != '':
            after_file = request.files['after']
            after_filename = secure_filename(after_file.filename)
            after_file_path = os.path.join(app.config['UPLOAD_FOLDER'], after_filename)
            after_file.save(after_file_path)
            user_data['after'] = after_filename  # Perbarui nama file di data user
            app.logger.debug(f"after file uploaded: {after_filename}")

        # Perbarui entri user di database
        app.logger.debug(f"Updating user: {user_data}")
        cur.execute(
            "UPDATE user SET nama=%s, username=%s, nohp=%s, password=%s, `before`=%s, `after`=%s WHERE id_user=%s",
            (user_data['nama'], user_data['username'], user_data['nohp'], user_data['password'], user_data['before'], user_data['after'], id_user)
        )
        mysql.connection.commit()

        flash('User updated successfully', 'success')
        cur.close()
        return redirect(url_for('anggota'))
    else:
        cur.close()
        return "User not found", 404

    
@app.route('/hapus_anggota/<int:id_user>', methods=['POST'])
def hapus_anggota(id_user):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user WHERE id_user=%s", (id_user,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('anggota'))
    
@app.route('/tambah_anggota', methods=['GET', 'POST'])
def tambah_anggota():
    if request.method == 'POST':
        nama = request.form['nama']
        username = request.form['username']
        password = request.form['password']
        nohp = request.form['nohp']
        before = request.files['before']
        after = request.files['after']

        before_filename = None
        after_filename = None

        if before and before.filename != '':
            before_filename = secure_filename(before.filename)
            before_path = os.path.join(app.config['UPLOAD_FOLDER'], before_filename)
            before.save(before_path)

        if after and after.filename != '':
            after_filename = secure_filename(after.filename)
            after_path = os.path.join(app.config['UPLOAD_FOLDER'], after_filename)
            after.save(after_path)

        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO user (nama, username, password, nohp, `before`, `after`) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (nama, username, password, nohp, before_filename, after_filename))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('anggota'))
    return render_template('tambah_anggota.html')

@app.route('/hitung_anggota')
def hitung_anggota_form():
    return render_template('hitung_anggota.html')

@app.route('/hitung_anggota', methods=['POST'])  # Perlu menangani metode POST untuk memproses data form
def hitung_anggota():
    Name = request.form['Name']
    Gender = request.form['Gender']
    Age = float(request.form['Age'])
    Height = float(request.form['Height'])
    Weight = float(request.form['Weight'])

    data = pd.DataFrame({
        'Gender': [Gender],
        'Age': [Age],
        'Height': [Height],
        'Weight': [Weight]
    })

    prediction = Label(data)

    # Tambahkan keterangan berdasarkan hasil prediksi
    if prediction == "Berat Kurang":
            message = ("Lakukan latihan 4-5 hari per minggu dengan fokus pada latihan kekuatan dan kardio ringan. "
                           "Untuk latihan kekuatan, bagi sesi menjadi upper body dan lower body. Pada hari upper body, "
                           "lakukan latihan seperti bench press, bent over row, dumbbell shoulder press, bicep curls, "
                           "dan tricep dips. Pada hari lower body, lakukan squats, deadlifts, leg press, lunges, dan "
                           "calf raises. Sisihkan satu atau dua hari untuk kardio ringan seperti jalan cepat atau "
                           "bersepeda, serta stretching dan yoga untuk pemulihan. Akhiri minggu dengan aktivitas fisik "
                           "menyenangkan seperti hiking atau berenang, dan pastikan ada hari istirahat untuk recovery "
                           "yang mencakup stretching dan foam rolling.")
    elif prediction == "Obesitas":
            message = ("Ketika sampai pada makan malam, prioritaskan minum air putih sebagai minuman utama untuk menjaga hidrasi." 
                        "Teh herbal tanpa kafein bisa menjadi pilihan yang baik sebagai minuman penutup yang menenangkan sebelum tidur."
                        "Hindari minuman beralkohol atau minuman berenergi yang dapat mengganggu kualitas tidur dan memberikan kalori tambahan yang tidak diperlukan.")
    elif prediction == "Berat Normal":
            message = ("Rutinitas gym yang terencana dengan baik adalah kunci kesuksesan dalam mencapai tujuan kebugaran."
                       "Mulai dari hari Senin yang didedikasikan untuk latihan kekuatan dan membangun otot bagian atas dengan latihan seperti bench press, pull-ups, shoulder press, dan barbel curl." 
                       "Selasa, fokusnya beralih pada kardio dan latihan otot bagian bawah melalui squat, deadlift, lunges, dan leg press. Rabu dijadwalkan sebagai hari istirahat atau pemulihan dengan yoga ringan untuk merilekskan otot-otot. Kemudian, Kamis kembali menantang otot bagian atas dengan latihan seperti lat pull-down, dumbbell bench press, dumbbell row, dan tricep dips. Jumat, intensitas meningkat kembali dengan latihan kardio intensif, seperti high-intensity interval training (HIIT), diikuti dengan latihan beban ringan untuk menjaga kebugaran. Akhir pekan digunakan untuk latihan keseimbangan dan fleksibilitas seperti yoga atau pilates, atau aktivitas luar ruangan seperti hiking, memberi tubuh kesempatan untuk pulih dan mempersiapkan diri untuk minggu berikutnya." 
                       "Hal terpenting adalah mendengarkan tubuh dan melakukan penyesuaian sesuai kebutuhan serta menjaga konsistensi dalam menjalankan jadwal latihan.")
    elif prediction == "Kelebihan Berat":
            message = ("Setiap hari latihan memiliki fokus yang berbeda untuk membantu membangun kekuatan, meningkatkan kardio, dan mendukung penurunan berat badan. Mulai dari latihan kekuatan bagian atas pada hari Senin, dengan latihan seperti bench press dan lat pull-down, hingga latihan kardio intensif pada hari Selasa dengan high-intensity interval training (HIIT), setiap sesi latihan dirancang untuk mencapai tujuan kebugaran Anda."
                       "Hari Rabu ditetapkan sebagai hari istirahat atau pemulihan dengan aktivitas ringan seperti yoga atau berjalan santai, sementara hari Kamis kembali menantang dengan latihan kekuatan bagian bawah seperti squat dan deadlift. Pada hari Jumat, Anda akan mencampur latihan kekuatan dan kardio dengan circuit training untuk memaksimalkan pembakaran kalori dan memperkuat otot-otot tubuh secara keseluruhan. Akhir pekan merupakan kesempatan untuk menjalani aktivitas yang menyenangkan seperti berenang atau hiking, yang juga membantu dalam proses penurunan berat badan."
                       "Penting untuk mengikuti jadwal latihan dengan konsisten dan mendengarkan tubuh Anda, serta berkonsultasi dengan profesional kesehatan jika diperlukan untuk memastikan program latihan yang aman dan efektif bagi kondisi tubuh Anda.")
    
    # Menyimpan data ke database
    cur = mysql.connection.cursor()
    cur.execute('''
        INSERT INTO anggota (name, gender, age, height, weight, timestamp, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (Name, Gender, Age, Height, Weight, datetime.now(), prediction[0]))
    mysql.connection.commit()
    cur.close()

    # Mendapatkan data anggota terbaru dari database
    # cur.execute("SELECT * FROM anggota ORDER BY id DESC LIMIT 1")
    # new_anggota = cur.fetchone()
    # cur.close()
    
    return render_template('hitung_anggota.html', prediction=prediction[0], message=message)
    
    return str(e)  # Untuk debug
    return render_template('hitung_anggota.html')

@app.route('/edit_user')
def edit_user():
    if 'username' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        return render_template('edit_user.html', user=user)
    return redirect(url_for('index'))

@app.route('/update_user', methods=['POST'])
def update_user():
    if 'username' in session:
        username = session['username']
        nama = request.form['nama']
        new_username = request.form['username']
        password = request.form['password']
        nohp = request.form['nohp']
        
        # Koneksi ke MySQL untuk mengambil data user lama
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT `before`, `after` FROM user WHERE username = %s', (username,))
        user_data = cursor.fetchone()
        
        # Cek apakah file before diunggah dan disimpan dengan benar
        before_filename = user_data['before']
        if 'before' in request.files:
            before_file = request.files['before']
            if before_file.filename != '':
                before_filename = secure_filename(before_file.filename)
                before_file_path = os.path.join(app.config['UPLOAD_FOLDER'], before_filename)
                before_file.save(before_file_path)
        
        # Cek apakah file after diunggah dan disimpan dengan benar
        after_filename = user_data['after']
        if 'after' in request.files:
            after_file = request.files['after']
            if after_file.filename != '':
                after_filename = secure_filename(after_file.filename)
                after_file_path = os.path.join(app.config['UPLOAD_FOLDER'], after_filename)
                after_file.save(after_file_path)
        
        # Perbarui data user di database dengan path gambar yang baru
        cursor.execute('''
            UPDATE user 
            SET nama = %s, username = %s, password = %s, nohp = %s, `before` = %s, `after` = %s 
            WHERE username = %s
        ''', (nama, new_username, password, nohp, before_filename, after_filename, username))
        mysql.connection.commit()
        
        session['username'] = new_username
        return redirect(url_for('dashboard_anggota'))
    return redirect(url_for('dashboard_anggota'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
