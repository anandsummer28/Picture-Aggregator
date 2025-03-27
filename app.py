from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify  # type: ignore
import os
import shutil
import time  # Import time module
from face_grouper import group_photos_by_faces  # Import the function from your face_grouper.py


print('starting the application')
app = Flask(__name__)

# Set the upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

# Create the upload and output folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global variable to store known faces
known_faces = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    global known_faces
    if 'files[]' not in request.files:
        return redirect(request.url)
    
    total_face_count = 0
    new_faces_detected = 0
    files = request.files.getlist('files[]')
    
    for file in files:
        if file.filename == '':
            continue
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the uploaded file
        initial_faces = len(known_faces)
        face_count, known_faces = group_photos_by_faces(file_path, OUTPUT_FOLDER, known_faces)
        new_faces = len(known_faces) - initial_faces
        new_faces_detected += new_faces
        total_face_count += face_count

        # Delete the processed file from the upload folder
        os.remove(file_path)

    return render_template('index.html', 
                         message=f"Files uploaded and processed successfully! "
                                f"New faces detected: {new_faces_detected}, "
                                f"Total faces processed: {total_face_count}")

@app.route('/process_folder', methods=['POST'])
def process_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    global known_faces
    folder_path = request.form['folder_path']
    if os.path.isdir(folder_path):
        face_count, known_faces = group_photos_by_faces(folder_path, OUTPUT_FOLDER, known_faces)
        return render_template('index.html', message=f"Folder processed successfully! Total New faces detected: {face_count}")
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():

    # Clear the upload folder
    shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)  # Recreate the upload folder

    # Rename the output folder with a timestamp
    if os.path.exists(OUTPUT_FOLDER):
        timestamp = int(time.time())  # Get the current time in epoch format
        new_output_folder = f"{OUTPUT_FOLDER}_old_{timestamp}"
        os.rename(OUTPUT_FOLDER, new_output_folder)
    global known_faces
    known_faces = {}
    return redirect(url_for('index'))

@app.route('/output')
def output():
    # List the output folders
    output_folders = [f for f in os.listdir(OUTPUT_FOLDER) if os.path.isdir(os.path.join(OUTPUT_FOLDER, f))]
    return render_template('output.html', output_folders=output_folders)

@app.route('/output/<folder_name>/<filename>')
def send_output_file(folder_name, filename):
    return send_from_directory(os.path.join(OUTPUT_FOLDER, folder_name), filename)

@app.route('/rename_folder', methods=['POST'])
def rename_folder():
    old_name = request.form['old_name']
    new_name = request.form['new_name']
    old_path = os.path.join(OUTPUT_FOLDER, old_name)
    new_path = os.path.join(OUTPUT_FOLDER, new_name)
    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
    return redirect(url_for('output'))

@app.route('/get_folder_images/<folder_name>')
def get_folder_images(folder_name):
    folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
    images = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
    return jsonify(images)

if __name__ == '__main__':
    app.run(debug=True)
