# Face Recognition Attendance System - Web Version

This is the browser version of the uploaded Tkinter project. The original images, face samples, classifier, labels, and main features are retained as closely as possible.

## Run
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Create a `.env` file by copying `.env.example`.
4. Put your local MySQL password in `DB_PASSWORD`. Do not share the `.env` file.
5. Install packages:
   `pip install -r requirements.txt`
6. Start:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

The MySQL database name remains `systemface attendance` to match the original project. Existing `register` and `student` tables can be used; the app creates them if they do not exist.

## Face recognition
- Existing `classifier.xml` is copied into `models/`.
- Existing face samples remain in `data/`.
- Student face samples can be captured from the browser camera.
- Train Data rebuilds the LBPH classifier from the `data/` folder.
- Face Recognition uses browser camera frames and the same LBPH + Haar Cascade approach.
- Attendance is written to `rohit.csv`, matching the original project's behavior.

## UI
The web UI uses the same project images, labels, major colors, Times New Roman styling, button names, and page concepts. Tkinter windows are replaced by browser pages because Tkinter itself cannot run inside a browser.
