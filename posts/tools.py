import os


def save_file_to_disk(file_data):
    # Generate a unique filename
    file_name = file_data.name

    # Specify the directory where you want to save the uploaded files
    upload_dir = '../media/files/'



    # Define the file path
    file_path = os.path.join(upload_dir, file_name)

    # Open the file and write the uploaded data to it
    with open(file_path, 'wb') as destination:
        for chunk in file_data.chunks():
            destination.write(chunk)

    return file_path