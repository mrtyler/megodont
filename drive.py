import base64
import os

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

import defaults


def login_with_service_account():
    """
    Google Drive service with a service account.
    note: for the service account to work, you need to share the folder or
    files with the service account email.

    :return: google auth
    """
    # Define the settings dict to use a service account
    # We also can use all options available for the settings dict like
    # oauth_scope,save_credentials,etc.
    settings = {
        "client_config_backend": "service",
        "service_config": {},
    }
    creds = os.getenv(defaults.creds_env_var)
    if creds:
        settings["service_config"]["client_json"] = base64.b64decode(creds)
    else:
        if os.path.exists(defaults.creds_file):
            settings["service_config"]["client_json_file_path"] = creds_file
        else:
            raise ValueError(f"Couldn't find creds in env var '$MEGODONT_UPLOADER_CREDS' nor in '{creds_file}'")

    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


gauth = login_with_service_account()
drive = GoogleDrive(gauth)

folder = "1Cy_tDSCjugdh-Eg8Ds5-a1F3XF9JQ1R5"

upload_me = drive.CreateFile({
    "title": "Hello-megodont.txt",
    "parents": [{"id": folder}],
})
import datetime
upload_me.SetContentString(f"Hello World! {datetime.datetime.now().isoformat()}")  # Set content of the file from given string.
upload_me.Upload()

# Auto-iterate through all files that matches this query
print(f"### FOLDER {folder} LIST ###")
file_list = drive.ListFile({"q": f"'{folder}' in parents and trashed=false"}).GetList()
for file1 in file_list:
    print("title: %s, id: %s" % (file1["title"], file1["id"]))
