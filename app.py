from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from database import Session, Person
from database import Photo
from face_utils import detect_and_group_faces

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'



session = Session()

def convert_to_url_path(path):
    return path.replace('\\', '/')

@app.route('/')
def index():
    people = session.query(Person).all()
    gallery_images = session.query(Photo).all()  # Fetch all photos
    return render_template('index.html', people=people, gallery_images=gallery_images)


@app.route('/static', methods=['POST'])
def upload_photo():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    files = request.files.getlist('photo')
    if not files or all(file.filename == '' for file in files):
        return redirect(url_for('index'))
    
    for file in files:
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = convert_to_url_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file.save(file_path)

            # Detect and group faces in each uploaded photo
            detect_and_group_faces(file_path)
    
    return redirect(url_for('index'))


@app.route('/edit/<int:person_id>', methods=['GET', 'POST'])
def edit_person(person_id):
    # Fetch the person to edit
    person = session.query(Person).get(person_id)
    
    if not person:
        return redirect(url_for('index'))  # Redirect to index if person not found
    
    if request.method == 'POST':
        new_name = request.form['name']
        
        if new_name:
            person.name = new_name  # Update the name in the database
            session.commit()  # Commit the changes to the database
            return redirect(url_for('view_person', person_id=person.id))  # Redirect to the person's page
        
        # If name is empty or invalid, re-render the form with a message
        return render_template('edit_person.html', person=person, error="Name cannot be empty.")
    
    return render_template('edit_person.html', person=person)

@app.route('/<int:person_id>')
def view_person(person_id):
    person = session.query(Person).get(person_id)
    if not person:
        return redirect(url_for('index'))
    return render_template('person.html', person=person)


@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    photo = session.query(Photo).get(photo_id)
    if photo:
        # Get the full path of the photo
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.path)
        
        # Delete the file from the file system
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove the photo from the database
        session.delete(photo)
        session.commit()
    
    return redirect(url_for('view_person', person_id=photo.person_id))


@app.route('/delete_person/<int:person_id>', methods=['POST'])
def delete_person(person_id):
    person = session.query(Person).get(person_id)
    if person:
        # Delete all photos associated with this person
        for photo in person.photos:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.path)
            if os.path.exists(file_path):
                os.remove(file_path)
            session.delete(photo)
        
        # Remove the person record from the database
        session.delete(person)
        session.commit()
    
    return redirect(url_for('index'))





if __name__ == '__main__':
    app.run(debug=True)


