from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


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
        "service_config": {
            "client_json_file_path": "megodont-uploader-credentials.json",
        },
    }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


# from pydrive2.auth import GoogleAuth
# from pydrive2.drive import GoogleDrive
#
# gauth = GoogleAuth()
# # Create local webserver and auto handles authentication.
# #gauth.LocalWebserverAuth()
#
# gauth.LoadClientConfigFile()


gauth = login_with_service_account()
drive = GoogleDrive(gauth)

file1 = drive.CreateFile(
    {"title": "Hello2.txt"}
)  # Create GoogleDriveFile instance with title 'Hello.txt'.
file1.SetContentString("Hello World!")  # Set content of the file from given string.
file1.Upload()

# Auto-iterate through all files that matches this query
file_list = drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()
for file1 in file_list:
    print("title: %s, id: %s" % (file1["title"], file1["id"]))
