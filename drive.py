#!/usr/bin/env python


import base64
import datetime
import os
import subprocess

import click
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
            settings["service_config"]["client_json_file_path"] = defaults.creds_file
        else:
            raise ValueError(f"Couldn't find creds in env var '${defaults.creds_env_var}' nor in file '{defaults.creds_file}'")

    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--file",
    default=defaults.outfile,
    show_default=True,
    help="File to upload",
)
def upload(file):
    gauth = login_with_service_account()
    drive = GoogleDrive(gauth)

    with open(file) as ff:
        contents = ff.read()

    commit = subprocess.run("git rev-parse HEAD".split(), stdout=subprocess.PIPE).stdout.decode('utf-8')[:6]
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d-%H%M%S")
    title = f"{".".join(file.split('.')[:-1])} {timestamp}-{commit}.csv"
    upload_me = drive.CreateFile({
        "title": title,
        "parents": [{"id": defaults.folder}],
        #"mimeType": "application/vnd.google-apps.spreadsheet",
        "mimeType": "text/csv",
    })
    upload_me.SetContentString(contents)
    upload_me.Upload()
    print(f"Uploaded {title}")


@cli.command()
def show():
    gauth = login_with_service_account()
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({"q": f"'{defaults.folder}' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        print("title: %s, id: %s" % (file1["title"], file1["id"]))


if __name__ == "__main__":
    cli()
