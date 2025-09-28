import face_recognition
import pickle
from database import Person, Photo, Session



session = Session()

TOLERANCE = [0.45,0.5,0.55,0.6]  # Tolerance level for face similarity

def detect_and_group_faces(image_path):
    # Load image and detect faces
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image,model="cnn")
    face_encodings = face_recognition.face_encodings(image, face_locations)

    # List to keep track of the new face groups
    face_groups = []

    # Iterate through each encoding to find a matching person or create a new group
    for encoding in face_encodings:
        person = find_matching_person(encoding)

        if person is None:
            person = Person(name=f"Person {session.query(Person).count() + 1}")
            session.add(person)
            session.commit()
        
        # Save photo with associated person and encoding
        new_photo = Photo(path=image_path, person_id=person.id, encoding=pickle.dumps(encoding))
        session.add(new_photo)

        # Add this face encoding to the face group for later reference
        face_groups.append((encoding, person))

    session.commit()
    
    # Now, group faces that are similar together
    group_similar_faces(face_groups)

def group_similar_faces(face_groups):
    grouped_people = []  # To store final grouped people

    for encoding, person in face_groups:
        matched_group = None
        # Try to find an existing group that contains similar faces
        for group in grouped_people:
            group_encodings = [face[0] for face in group]
            matches = face_recognition.compare_faces(group_encodings, encoding, tolerance=TOLERANCE)
            if any(matches):  # If any encoding matches, this face belongs to this group
                matched_group = group
                break
        
        if matched_group is None:
            matched_group = [(encoding, person)]
            grouped_people.append(matched_group)
        else:
            matched_group.append((encoding, person))
    
    # Update the person records to reflect the groupings
    for group in grouped_people:
        first_encoding, first_person = group[0]
        for encoding, _ in group[1:]:
            for photo in session.query(Photo).filter_by(person_id=first_person.id):
                photo.person_id = first_person.id
                session.commit()

def find_matching_person(face_encoding, tolerance=TOLERANCE):
    all_people = session.query(Person).all()
    for person in all_people:
        for photo in person.photos:
            saved_encoding = pickle.loads(photo.encoding)
            match = face_recognition.compare_faces([saved_encoding], face_encoding, tolerance=tolerance)
            if match[0]:
                return person
    return None
