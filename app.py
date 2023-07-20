import os
from PIL import Image
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import myModel


MYDIR = os.path.dirname(__file__)
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(MYDIR + "/" +
                  app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('get_text', filename=filename))
        
    else:
        flash('Allowed image types are jpg and jpeg')
        return redirect(request.url)


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/get_text', methods=['GET', 'POST'])
def get_text():
    filename = request.args.get('filename')
    result=""
    text=""
    if request.method == 'POST':
        text = request.form.get('input_text')
        image = Image.open('static/uploads/' + filename).convert('RGB')

        blip_vqa = myModel.BLIP_VQA(vision_model=myModel.model.vision_model,
                            text_encoder=myModel.model.text_encoder,
                            text_decoder=myModel.model.text_decoder,
                            processor=myModel.processor)

        result=blip_vqa.get_answer(image, text)
        
    return render_template('get_text.html', filename=filename, result=result, text=text)


if __name__ == "__main__":
    app.run(debug=True)
