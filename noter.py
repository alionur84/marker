from flask import Flask, render_template, flash, request, redirect, url_for, session, send_from_directory
import os
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from wtforms.validators import ValidationError, DataRequired
import uuid
from xls_creator import *


app=Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["UPLOADS"] = os.environ['UPLOADS']
# Do not forget to remove the pdf
app.config["ALLOWED_EXTENSIONS"] = ["XLSX", "XLS", "CSV", "PDF"]
app.config['DOWNLOAD_FOLDER'] = os.environ['DOWNLOADS']
MAX_CONTENT_LENGTH = 1500000



class UploadForm(FlaskForm):
    marks = FileField("Optik Okuyucu Dosyası")
    sablon_o =FileField("Örgün Şablon")
    sablon_io = FileField("İkinci Öğretim Şablon")

def allowed_ext(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_EXTENSIONS"]:
        return True
    else:
        return False

def check_size(file):
    pos = file.tell()
    file.seek(0, 2)  #seek to end
    size = file.tell()
    file.seek(pos)
    if size <= MAX_CONTENT_LENGTH:
        return True
    else:
        return False




@app.route("/")
@app.route("/home")
def home():
    session.pop('user_id', default=None)
    session.pop('unknown_students', default=None)
    user_id = str(uuid.uuid4())
    session['user_id'] = user_id
    session['unknown_students'] = {}
    session['corrected_ids'] = {}
    return render_template("index.html", title='Home')


@app.route("/sessioner")
def check():
    return render_template("session.html", user_id=session['user_id'])


# upload file
@app.route("/upload-file", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if request.files:

            
            not_listesi = request.files["not_listesi"]
            orgun_sablon = request.files["orgun_sablon"]
            IO_sablon = request.files["IO_sablon"]

            if not_listesi.filename == "" or orgun_sablon.filename == "" or IO_sablon.filename == "":
                flash('Lütfen dosya adlarını kontrol ediniz!!', 'danger')
                session.pop('user_id', default=None)
                return redirect(url_for('home'))

            if check_size(not_listesi) and check_size(orgun_sablon) and check_size(IO_sablon):

                if allowed_ext(not_listesi.filename) and allowed_ext(orgun_sablon.filename) and allowed_ext(IO_sablon.filename):
                    not_listesi_fname = secure_filename(not_listesi.filename)
                    orgun_sablon_fname = secure_filename(orgun_sablon.filename)
                    IO_sablon_fname = secure_filename(IO_sablon.filename)

                    not_listesi_path = os.path.join(app.config["UPLOADS"], session['user_id'] + "_" + not_listesi_fname)
                    orgun_sablon_path = os.path.join(app.config["UPLOADS"], session['user_id'] + "_" + orgun_sablon_fname)
                    IO_sablon_path = os.path.join(app.config["UPLOADS"], session['user_id'] + "_" + IO_sablon_fname)


                    not_listesi.save(not_listesi_path)
                    orgun_sablon.save(orgun_sablon_path)
                    IO_sablon.save(IO_sablon_path)

                    df = file_uploader(not_listesi_path)
                    df = header_dropper(df)
                    df = clean_na(df)
                    df = convert_datatypes(df)
                    template = template_concat(orgun_sablon_path, IO_sablon_path)
                    id_corrected = id_correct(df, template)
                    df = id_corrected[0]
                    unknown_students = id_corrected[1]
                    corrected_ids = id_corrected[2]
                    
                    for i in unknown_students.index:
                        session['unknown_students'][str(unknown_students.loc[i, ['TCKimlikNo']][0])] = [str(unknown_students.loc[i, ['Adı ']][0]), str(unknown_students.loc[i, ['Soyadı']][0]), int(unknown_students.loc[i, [unknown_students.columns[-1]]][0])]

                    for z in corrected_ids.index:
                        session['corrected_ids'][str(corrected_ids.loc[z, ['TCKimlikNo']][0])] = [str(corrected_ids.loc[z, ['Adı ']][0]), str(corrected_ids.loc[z, ['Soyadı']][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-1]]][0])]

                    




                    final_file = finalizer(df, template)
                    final_file[0].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], session['user_id'] + "_" + "orgun.xlsx" ))
                    final_file[1].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], session['user_id'] + "_" + "io.xlsx" ))
                    flash('Dosyalar başarıyla yüklendi', 'success')

                    filename_orgun = session['user_id'] + "_" + "orgun.xlsx"
                    filename_io = session['user_id'] + "_" + "io.xlsx"


                    return redirect(url_for('download_page', filename1=filename_orgun, filename2=filename_io))
                else:
                    session.pop('user_id', default=None)
                    flash('Dosya uzantıları xls, xlsx ya da csv olmalıdır!!', 'danger')
                    return redirect(url_for('home'))
            else:
                session.pop('user_id', default=None)
                flash("Dosya boyutu 1.5 megabyte'dan yüksek olamaz!!", "danger")
                return redirect(url_for('home'))

    return render_template('upload_file.html', title='Upload File')


@app.route('/downloads/<filename1>+<filename2>')
def download_page(filename1, filename2):
    filename1 = filename1
    filename2 = filename2

    unknown_students = session['unknown_students']
    corrected_ids = session['corrected_ids']
    if len(unknown_students)>0:
        unknowns = True
    else:
        unknowns = False

    if len(corrected_ids)>0:
        corrected = True
    else:
        corrected = False

    return render_template("downloads.html", filename1=filename1, filename2=filename2, unknown_students=unknown_students, unknowns=unknowns, corrected_ids=corrected_ids, corrected=corrected)

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def downloads(filename):
    # Appending app path to upload folder path within app root folder
    download_dir = app.config['DOWNLOAD_FOLDER']
    # Returning file from appended path
    return send_from_directory(download_dir, filename, as_attachment=True)


#invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


if __name__ == '__main__':
    app.run(debug=True)