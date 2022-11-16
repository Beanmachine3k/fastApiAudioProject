from fastapi import FastAPI, UploadFile, File, Request, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates

from pydub import AudioSegment
from pydub.utils import which

import shutil
from typing import Optional

# from tortoise import fields
# from tortoise.models import Model
# from tortoise.contrib.fastapi import register_tortoise

AudioSegment.converter = which("ffmpeg")
app = FastAPI()

templates = Jinja2Templates(directory="html")
oauth2 = OAuth2PasswordBearer(tokenUrl='token')

# Experimenting with user class for security and logins
# class User(Model):
#     """Class for users in our system"""
#     num = fields.IntField(pk=True)
#     username = fields.CharField(25, unique=False)
#     password_hash = fields.CharField(50)


class AudioFile:
    """Class to represent audio files and their metadata in the system"""

    def __init__(self, duration, file_name, file, file_type=None):
        self.duration = duration
        self.fileName = file_name
        self.file = file
        self.fileType = file_type

    duration: float
    fileName: str
    file: UploadFile
    fileType: Optional[str] = None  # Type of file (wav, mp3, etc)


# All audio data in the system
audio_data = \
    {
    }


@app.post('/token')
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Token page"""
    return {"Access with token" : form_data.username + 'user'}


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """The home page"""
    req = {"request": request}
    return templates.TemplateResponse("homep.html", req)


@app.get("/list", response_class=HTMLResponse)
def list_files(request: Request, minduration: Optional[float] = None, maxduration:
        Optional[float] = None, duration: Optional[float] = None, file_type: Optional[str] = None, ):
    """Return list of audio files, allow user to filter based on certain factors. """

    # If no parameters just return all existing audio files.
    if minduration is None and maxduration is None and duration is None and file_type is None:
        req = {"request": request, "files": audio_data}
        return templates.TemplateResponse("info.html", req)

    # Ensure the duration parameters are valid numbers.
    if minduration is not None:
        if minduration <= 0:
            req = {"request": request, "Error": "Min duration cannot be negative or 0."}
            return templates.TemplateResponse("info.html", req)

    if maxduration is not None:
        if maxduration <= 0:
            req = {"request": request, "Error": "Max duration cannot be negative or 0."}
            return templates.TemplateResponse("info.html", req)

    if duration is not None:
        if duration <= 0:
            req = {"request": request, "Error": "Duration cannot be negative or 0."}
            return templates.TemplateResponse("info.html", req)

    # Loop through all audio files and see if any fit our parameters.
    valid_files = {}
    for filename in audio_data:
        if audio_data[filename].duration == duration:
            valid_files[filename] = (audio_data[filename])

        if audio_data[filename].fileType == file_type:
            valid_files[filename] = (audio_data[filename])

        if minduration is not None and maxduration is not None:

            if minduration <= audio_data[filename].duration <= maxduration:
                valid_files[filename] = (audio_data[filename])

        elif minduration is not None:

            if audio_data[filename].duration >= minduration:
                valid_files[filename] = (audio_data[filename])

        elif maxduration is not None:

            if audio_data[filename].duration <= maxduration:
                valid_files[filename] = (audio_data[filename])

    # If parameters were given and none fit them, display to user no valid files
    if len(valid_files) == 0:
        req = {"request": request, "Error": "No files fit given parameters."}
        return templates.TemplateResponse("info.html", req)

    else:
        req = {"request": request, "files": valid_files}
        return templates.TemplateResponse("info.html", req)


@app.post("/post")
def post_audio(token: str = Depends(oauth2), file: UploadFile = File(...)):
    """ Post an audio file to the system and stores it."""

    if file.filename in audio_data:
        return {"Error:": "Audio file already exists."}

    # Error check to ensure data valid
    if file.filename[-3:] != "wav":
        return {"Error": "Invalid file type."}

    # Store the file on our system
    with open(f'{file.filename}', 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Turn file into an audio segment to get certain data about it
    audio = AudioSegment.from_file(file=file.file, format=file.filename[-3:])

    # Create the file and pass key information: Duration, filename, the file, file type
    audio_file = AudioFile((round(audio.duration_seconds, 2)), file.filename, file, file.filename[-3:])

    audio_data[file.filename] = audio_file
    return {"Success:": "Audio file " + file.filename + " has been stored."}


@app.get("/info")
def audio_file_info(filename: str, token: str = Depends(oauth2)):
    """ Get all or specific info about certain audio file. """
    if filename not in audio_data:
        return {"Error:": " No such audio file exists. "}

    return audio_data[filename]


@app.get("/download")
def download_audio(filename: str, token: str = Depends(oauth2)):
    """ Download audio file provided it exists in the system. """
    if filename not in audio_data:
        return {"Error:": " No such audio file exists."}

    # Open in read mode to copy the file
    with open(audio_data[filename].fileName, "rb") as f:
        contents = f.read()

    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return Response(contents, headers=headers, media_type='audio/wav')


@app.put("/delete")
def delete_audio(filename: str, token: str = Depends(oauth2)):
    """Delete given audio file from the system"""
    if filename not in audio_data:
        return {"Error:": " No such audio file exists."}

    del audio_data[filename]
    return {"Success: ": " Audio file successfully deleted."}


# Experimenting with database.
# register_tortoise(
#     app, db_url='sqlite://db.test1',
#     modules={'models': ['main']}, generate_schemas=True,
# )