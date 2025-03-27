import os
import cv2
import face_recognition # type: ignore
import shutil
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def group_photos_by_faces(input_path, output_folder, known_faces):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Initialize face_count from known_faces instead of 0
    face_count = len(known_faces)
    logging.info(f"Starting with face_count: {face_count}")

    # Check if the input path is a file or a directory
    if os.path.isfile(input_path):
        # If it's a single file, process it
        image_files = [input_path]
    elif os.path.isdir(input_path):
        # If it's a directory, get all image files
        image_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
    else:
        logging.error("Invalid input path. Please provide a valid file or directory.")
        return 0, known_faces  # Return 0 if the input path is invalid

    logging.info(f"Processing the following images: {image_files}")

    # Load known face encodings and their corresponding folder names
    known_face_encodings = list(known_faces.keys())
    known_face_folders = list(known_faces.values())

    # Iterate through all images
    for image_path in image_files:
        image = face_recognition.load_image_file(image_path)

        # Find all face locations and encodings in the image using the 'hog' model for faster processing
        face_locations = face_recognition.face_locations(image, model='hog')
        face_encodings = face_recognition.face_encodings(image, face_locations)

        # Define the central region of the image
        height, width, _ = image.shape
        central_region = (int(width * 0.25), int(height * 0.25), int(width * 0.75), int(height * 0.75))

        # Calculate average size of faces in the central region
        central_faces = []
        for (top, right, bottom, left) in face_locations:
            if (left >= central_region[0] and right <= central_region[2] and
                    top >= central_region[1] and bottom <= central_region[3]):
                central_faces.append((right - left, bottom - top))  # width, height

        # Initialize minimum acceptable size
        min_acceptable_size = (0, 0)  # Default to (0, 0) if no central faces are found
        avg_width = 0
        avg_height = 0

        # Calculate average size if there are central faces
        if central_faces:
            avg_width = np.mean([size[0] for size in central_faces])
            avg_height = np.mean([size[1] for size in central_faces])
            min_acceptable_size = (avg_width * 0.6, avg_height * 0.6)

        # Filter faces based on the calculated average size
        for i, (top, right, bottom, left) in enumerate(face_locations):
            face_width = right - left
            face_height = bottom - top

            # If no central faces were found, allow all detected faces to be processed
            if (not central_faces) or \
               (face_width >= avg_width and face_height >= avg_height) or \
               (face_width >= min_acceptable_size[0] and face_height >= min_acceptable_size[1]):
                # Check if the face is already known
                face_encoding = face_encodings[i]
                
                if known_face_encodings:
                    # Calculate face distances to all known faces
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    
                    # Use a threshold to determine if it's a match (0.6 is a good starting point)
                    if face_distances[best_match_index] < 0.6:
                        face_folder = known_face_folders[best_match_index]
                    else:
                        # Create new folder for unmatched face
                        face_count += 1
                        face_folder = os.path.join(output_folder, f'face_{face_count}')
                        known_faces[tuple(face_encoding)] = face_folder
                        known_face_encodings.append(tuple(face_encoding))
                        known_face_folders.append(face_folder)
                        os.makedirs(face_folder, exist_ok=True)
                else:
                    # Handle the first face when no known faces exist
                    face_count += 1
                    face_folder = os.path.join(output_folder, f'face_{face_count}')
                    known_faces[tuple(face_encoding)] = face_folder
                    known_face_encodings.append(tuple(face_encoding))
                    known_face_folders.append(face_folder)
                    os.makedirs(face_folder, exist_ok=True)

                # Save a sample face image in the respective folder
                face_image = image[top:bottom, left:right]
                sample_face_path = os.path.join(face_folder, 'sample_face.jpg')
                cv2.imwrite(sample_face_path, face_image)
                print('image saved for ', i)

                # Copy the original image to the respective folder
                shutil.copy(image_path, os.path.join(face_folder, os.path.basename(image_path)))

    logging.info(f"Total faces detected and segregated: {face_count}")
    return face_count, known_faces  # Return both the face count and updated known_faces dictionary

# Example usage
# source_folder = '/mnt/c/Users/anand/OneDrive - International Institute of Information Technology/Pictures/JasmhedpurTrip/IMG-20241212-WA0037.jpg'
# output_folder = '/mnt/c/Users/anand/OneDrive/Documents/Ideas/PicSeg/output4'
# group_photos_by_faces(source_folder, output_folder)