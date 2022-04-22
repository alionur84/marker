from flask import Flask, render_template, flash, request, redirect, url_for, session, send_from_directory, abort, send_file
import os
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import SubmitField, BooleanField, ValidationError, FileField
import uuid
import io
from xls_creator import *



app=Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["UPLOADS"] = os.environ['UPLOADS']

app.config["ALLOWED_EXTENSIONS"] = ["XLSX", "XLS", "CSV"]
app.config['DOWNLOAD_FOLDER'] = os.environ['DOWNLOADS']
MAX_CONTENT_LENGTH = 1500000


class FileForm(FlaskForm):
    io_var = BooleanField("İkinci Öğretim")
    but = BooleanField("Bütünleme")
    submit = SubmitField("Yükle")

# allowed extensions func


def allowed_ext(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_EXTENSIONS"]:
        return True
    else:
        return False

# allowed file size func

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
    session.pop('corrected_ids', default=None)
    session.pop('attended_count', default=None)
    session.pop('mean_mark', default=None)
    session.pop('enrolled_count', default=None)
    session.pop('std_dev', default=None)
    session.pop('io_var', default=None)
    user_id = str(uuid.uuid4())
    session['user_id'] = user_id
    session['unknown_students'] = {}
    session['corrected_ids'] = {}
    session['attended_count'] = str(0)
    session['mean_mark'] = str(0)
    session['enrolled_count'] = str(0)
    session['std_dev'] = str(0)
    session['io_var'] = str(1)

    return render_template("index.html", title='Home')

@app.route("/sessioner")
def check():
    return render_template("session.html", user_id=session['user_id'], title='Session ID')


# upload file
@app.route("/upload-file", methods=["GET", "POST"])
def upload():
    form = FileForm()
    if form.validate_on_submit():
        butunleme = form.but.data
        io_var = form.io_var.data

    if request.method == "POST":

        if request.files:
            if io_var:
                
                not_listesi = request.files["not_listesi"]
                orgun_sablon = request.files["orgun_sablon"]
                IO_sablon = request.files["IO_sablon"]
                
                if not_listesi.filename == "" or orgun_sablon.filename == "" or IO_sablon.filename == "":
                    flash('Eksik dosya yüklenmiş ya da dosya adları desteklenmiyor. Lütfen dosyaları ve dosya adlarını kontrol ediniz!!', 'danger')
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

                        # uploaded files have different shapes, columns etc.
                        # some have headers some don't
                        # so they have to be handled differently
                        # if no header and null rows, then move to next try except block

                        try:

                            print("1\n")
                            df = file_uploader(not_listesi_path)
                            print("2\n")
                            df = header_dropper(df)
                                                
                            print("3\n")
                            result = clean_na(df)
                            session['attended_count'] = str(result['attended_count'])
                            session['mean_mark'] = str(result['mean_mark'])
                            session['std_dev'] = str(result['std_dev'])
                            print("4\n")
                            
                            df = convert_datatypes(result['df'])
                            
                            print("5\n")
                            template_result = template_concat(orgun_sablon_path, IO_sablon_path, io_var)
                            session['enrolled_count'] = str(template_result['enrolled_count'])
                            
                            print("6\n")
                            
                            id_corrected = id_correct(df, template_result['template_df'])
                            df = id_corrected[0]
                            unknown_students = id_corrected[1]
                            corrected_ids = id_corrected[2]
                            
                            print("7\n")
                            
                            for i in unknown_students.index:
                                session['unknown_students'][str(unknown_students.loc[i, ['TCKimlikNo']][0])] = [str(unknown_students.loc[i, ['Adı ']][0]), str(unknown_students.loc[i, ['Soyadı']][0]), int(unknown_students.loc[i, [unknown_students.columns[-1]]][0])]

                            for z in corrected_ids.index:
                                session['corrected_ids'][str(corrected_ids.loc[z, ['TCKimlikNo']][0])] = [str(corrected_ids.loc[z, ['Adı ']][0]), str(corrected_ids.loc[z, ['Soyadı']][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-2]]][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-1]]][0]) ]

                            print("8\n")

                            filename_orgun = session['user_id'] + "_" + "orgun.xlsx"
                            filename_io = session['user_id'] + "_" + "io.xlsx"
                                                    
                            final_file = finalizer(df, template_result['template_df'], butunleme)
                            print("88\n")
                            final_file[0].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_orgun), index=False)
                            final_file[1].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_io), index=False)
                            
                            print("9\n")                        

                            
                            os.remove(not_listesi_path)
                            os.remove(orgun_sablon_path)
                            os.remove(IO_sablon_path)

                            print("10\n")                        
                            # flash('Dosyalar başarıyla yüklendi', 'success')
                            return redirect(url_for('download_page', filename1=filename_orgun, filename2=filename_io))

                        except:

                            try:
                                df1 = file_uploader(not_listesi_path)
                                print("11\n")

                                result = stats(df1)
                                session['attended_count'] = str(result['attended_count'])
                                session['mean_mark'] = str(result['mean_mark'])
                                session['std_dev'] = str(result['std_dev'])

                                print("12\n")

                                df1 = convert_datatypes(df1)

                                print("13\n")

                                template_result = template_concat(orgun_sablon_path, IO_sablon_path, io_var)
                                session['enrolled_count'] = str(template_result['enrolled_count'])
                                
                                print("14\n")

                                id_corrected = id_correct(df1, template_result['template_df'])
                                df1 = id_corrected[0]
                                unknown_students = id_corrected[1]
                                corrected_ids = id_corrected[2]

                                print("15\n")

                                for i in unknown_students.index:
                                    session['unknown_students'][str(unknown_students.loc[i, ['TCKimlikNo']][0])] = [str(unknown_students.loc[i, ['Adı ']][0]), str(unknown_students.loc[i, ['Soyadı']][0]), int(unknown_students.loc[i, [unknown_students.columns[-1]]][0])]

                                for z in corrected_ids.index:
                                    session['corrected_ids'][str(corrected_ids.loc[z, ['TCKimlikNo']][0])] = [str(corrected_ids.loc[z, ['Adı ']][0]), str(corrected_ids.loc[z, ['Soyadı']][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-2]]][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-1]]][0]) ]

                                print("16\n")

                                filename_orgun = session['user_id'] + "_" + "orgun.xlsx"
                                filename_io = session['user_id'] + "_" + "io.xlsx"
                                print(filename_orgun)
                                print(filename_io)
                                # aynı öğrenci optik tarafından iki kez okunursa
                                # burada bir yerde drop duplicates yapmak lazım sonuç dosyasına
                                # yoksa çöküyor.
                                final_file = finalizer(df1, template_result['template_df'], butunleme)
                                print("888\n")
                                final_file[0].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_orgun), index=False)
                                print("889\n")
                                final_file[1].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_io), index=False)
                                
                                print("17\n")
                                
                                os.remove(not_listesi_path)
                                os.remove(orgun_sablon_path)
                                os.remove(IO_sablon_path)

                                print("18\n")

                                # flash('Dosyalar başarıyla yüklendi', 'success')
                                return redirect(url_for('download_page', filename1=filename_orgun, filename2=filename_io))

                            except:
                                try:
                                    print("19\n")
                                    os.remove(not_listesi_path)
                                    os.remove(orgun_sablon_path)
                                    os.remove(IO_sablon_path)
                                    flash('Lütfen yüklediğiniz dosyaların orijinal şablonlar ve optik okuyucu dosyası olduğundan emin olunuz!!', 'danger')
                                    abort(404)
                                except:
                                    print("20\n")
                                    flash('Lütfen yüklediğiniz dosyaların orijinal şablonlar ve optik okuyucu dosyası olduğundan emin olunuz!!', 'danger')
                                    abort(404)
                    else:
                        session.pop('user_id', default=None)
                        flash('Dosya uzantıları xls, xlsx ya da csv olmalıdır!!', 'danger')
                        return redirect(url_for('home'))
                else:
                    session.pop('user_id', default=None)
                    flash("Dosya boyutu 1.5 megabyte'dan yüksek olamaz!!", "danger")
                    return redirect(url_for('home'))
            else:
                session['io_var'] = str(0)

                not_listesi = request.files["not_listesi"]
                orgun_sablon = request.files["orgun_sablon"]

                if not_listesi.filename == "" or orgun_sablon.filename == "":
                    flash('Eksik dosya yüklenmiş ya da dosya adları desteklenmiyor. Lütfen dosyaları ve dosya adlarını kontrol ediniz!!', 'danger')
                    session.pop('user_id', default=None)
                    return redirect(url_for('home'))

                if check_size(not_listesi) and check_size(orgun_sablon):

                    if allowed_ext(not_listesi.filename) and allowed_ext(orgun_sablon.filename):
                        
                        not_listesi_fname = secure_filename(not_listesi.filename)
                        orgun_sablon_fname = secure_filename(orgun_sablon.filename)
                        
                        not_listesi_path = os.path.join(app.config["UPLOADS"], session['user_id'] + "_" + not_listesi_fname)
                        orgun_sablon_path = os.path.join(app.config["UPLOADS"], session['user_id'] + "_" + orgun_sablon_fname)
                        
                        not_listesi.save(not_listesi_path)
                        orgun_sablon.save(orgun_sablon_path)
                        
                        try:

                            # print("1\n")
                            df = file_uploader(not_listesi_path)
                            # print("2\n")
                            df = header_dropper(df)
                                                
                            # print("3\n")
                            result = clean_na(df)
                            session['attended_count'] = str(result['attended_count'])
                            session['mean_mark'] = str(result['mean_mark'])
                            session['std_dev'] = str(result['std_dev'])
                            # print("4\n")
                            
                            df = convert_datatypes(result['df'])
                            
                            # print("5\n")
                            template_result = template_concat(orgun_sablon_path)
                            session['enrolled_count'] = str(template_result['enrolled_count'])
                            
                            # print("6\n")
                            
                            id_corrected = id_correct(df, template_result['template_df'])
                            df = id_corrected[0]
                            unknown_students = id_corrected[1]
                            corrected_ids = id_corrected[2]
                            
                            # print("7\n")
                            
                            for i in unknown_students.index:
                                session['unknown_students'][str(unknown_students.loc[i, ['TCKimlikNo']][0])] = [str(unknown_students.loc[i, ['Adı ']][0]), str(unknown_students.loc[i, ['Soyadı']][0]), int(unknown_students.loc[i, [unknown_students.columns[-1]]][0])]

                            for z in corrected_ids.index:
                                session['corrected_ids'][str(corrected_ids.loc[z, ['TCKimlikNo']][0])] = [str(corrected_ids.loc[z, ['Adı ']][0]), str(corrected_ids.loc[z, ['Soyadı']][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-2]]][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-1]]][0]) ]

                            # print("8\n")

                            filename_orgun = session['user_id'] + "_" + "orgun.xlsx"
                            filename_io = "none"
                            
                                                    
                            final_file = finalizer(df, template_result['template_df'], butunleme)
                            final_file[0].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_orgun), index=False)
                            
                            
                            # print("9\n")                        

                            
                            os.remove(not_listesi_path)
                            os.remove(orgun_sablon_path)
                            

                            # print("10\n")                        
                            # flash('Dosyalar başarıyla yüklendi', 'success')
                            return redirect(url_for('download_page', filename1=filename_orgun, filename2=filename_io))

                        except:

                            try:
                                df1 = file_uploader(not_listesi_path)
                                # print("11\n")

                                result = stats(df1)
                                session['attended_count'] = str(result['attended_count'])
                                session['mean_mark'] = str(result['mean_mark'])
                                session['std_dev'] = str(result['std_dev'])

                                # print("12\n")

                                df1 = convert_datatypes(df1)

                                # print("13\n")

                                template_result = template_concat(orgun_sablon_path)
                                session['enrolled_count'] = str(template_result['enrolled_count'])
                                

                                # print("14\n")

                                id_corrected = id_correct(df1, template_result['template_df'])
                                df1 = id_corrected[0]
                                unknown_students = id_corrected[1]
                                corrected_ids = id_corrected[2]

                                # print("15\n")                            
                                for i in unknown_students.index:
                                    session['unknown_students'][str(unknown_students.loc[i, ['TCKimlikNo']][0])] = [str(unknown_students.loc[i, ['Adı ']][0]), str(unknown_students.loc[i, ['Soyadı']][0]), int(unknown_students.loc[i, [unknown_students.columns[-1]]][0])]

                                for z in corrected_ids.index:
                                    session['corrected_ids'][str(corrected_ids.loc[z, ['TCKimlikNo']][0])] = [str(corrected_ids.loc[z, ['Adı ']][0]), str(corrected_ids.loc[z, ['Soyadı']][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-2]]][0]), int(corrected_ids.loc[z, [corrected_ids.columns[-1]]][0]) ]

                                # print("16\n")

                                filename_orgun = session['user_id'] + "_" + "orgun.xlsx"
                                filename_io = "none"

                                final_file = finalizer(df1, template_result['template_df'], butunleme)
                                final_file[0].to_excel(os.path.join(app.config['DOWNLOAD_FOLDER'], filename_orgun), index=False)
                                
                                
                                # print("17\n")


                                
                                os.remove(not_listesi_path)
                                os.remove(orgun_sablon_path)
                                

                                # print("18\n")

                                # flash('Dosyalar başarıyla yüklendi', 'success')
                                return redirect(url_for('download_page', filename1=filename_orgun, filename2=filename_io))

                            except:
                                try:
                                    os.remove(not_listesi_path)
                                    os.remove(orgun_sablon_path)
                                    flash('Lütfen yüklediğiniz dosyaların orijinal şablonlar ve optik okuyucu dosyası olduğundan emin olunuz!!', 'danger')
                                    abort(404)
                                except:
                                    flash('Lütfen yüklediğiniz dosyaların orijinal şablonlar ve optik okuyucu dosyası olduğundan emin olunuz!!', 'danger')
                                    abort(404)

                
    return render_template('upload_file.html', title='Upload File', form=form)


@app.route('/downloads/<filename1>+<filename2>')
def download_page(filename1, filename2):
    filename1 = filename1
    filename2 = filename2
    
    
    if session['io_var'] == "1":
        
        if session['user_id'] in filename1 and session['user_id'] in filename2:
            try:
                unknown_students = session['unknown_students']
                corrected_ids = session['corrected_ids']
                attended_count = session['attended_count']
                mean_mark = session['mean_mark']
                std_dev = session['std_dev']
                enrolled_count = session['enrolled_count']
                

                if len(unknown_students)>0:
                    unknowns = True
                else:
                    unknowns = False

                if len(corrected_ids)>0:
                    corrected = True
                else:
                    corrected = False

                io_var = True
                return render_template("downloads.html", filename1=filename1, filename2=filename2, 
                    unknown_students=unknown_students, unknowns=unknowns, corrected_ids=corrected_ids,
                    corrected=corrected, attended_count=attended_count,
                    mean_mark=mean_mark, std_dev=std_dev,
                    enrolled_count=enrolled_count, io_var=io_var, title='Download your files')
            except:

                flash('Bir sorun oluştu, lütfen tekrar deneyiniz!!', 'danger')
                abort(404)
        else:

            flash('Bir sorun oluştu, lütfen tekrar deneyiniz!!', 'danger')
            abort(404)
    else:

        if session['user_id'] in filename1:
            try:
                unknown_students = session['unknown_students']
                corrected_ids = session['corrected_ids']
                attended_count = session['attended_count']
                mean_mark = session['mean_mark']
                std_dev = session['std_dev']
                enrolled_count = session['enrolled_count']

                if len(unknown_students)>0:
                    unknowns = True
                else:
                    unknowns = False

                if len(corrected_ids)>0:
                    corrected = True
                else:
                    corrected = False

                filename2 = "none"
                io_var = False

                return render_template("downloads.html", filename1=filename1, filename2=filename2, 
                    unknown_students=unknown_students, unknowns=unknowns, corrected_ids=corrected_ids,
                    corrected=corrected, attended_count=attended_count,
                    mean_mark=mean_mark, std_dev=std_dev,
                    enrolled_count=enrolled_count, io_var=io_var, title='Download your files')
            except:
                flash('Bir sorun oluştu, lütfen tekrar deneyiniz!!', 'danger')
                abort(404)
        else:
            flash('Bir sorun oluştu, lütfen tekrar deneyiniz!!', 'danger')
            abort(404)

@app.route('/downloads/<path:filename>', methods=['GET', 'POST'])
def downloads(filename):
    try:
        # Appending app path to upload folder path within app root folder
        download_dir = app.config['DOWNLOAD_FOLDER']
        path_to_file = os.path.join(download_dir, filename)
        
        # this part writes the file to memory in order to delete it after sending
        return_data = io.BytesIO()
        with open(path_to_file, 'rb') as fo:
            return_data.write(fo.read())
        # (after writing, cursor will be at last byte, so move it to start)
        return_data.seek(0)

        os.remove(path_to_file)

        return send_file(return_data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         attachment_filename=session['user_id']+"_"+"download.xlsx")
    except:
        flash('Bir sorun oluştu, lütfen tekrar deneyiniz!!', 'danger')
        abort(404)
    # Returning file from appended path
    #return send_from_directory(download_dir, filename, as_attachment=True)


#invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


if __name__ == '__main__':
    app.run(debug=False)