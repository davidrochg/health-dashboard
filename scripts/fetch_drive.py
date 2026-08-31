#!/usr/bin/env python3
"""
Descarga los Excel de salud desde Google Drive usando una cuenta de servicio.
Pensado para ejecutarse dentro de GitHub Actions (en la nube).

Variables de entorno necesarias:
  GDRIVE_SA_KEY    -> contenido JSON de la llave de la cuenta de servicio (Secret)
  PESO_FILE_ID     -> ID del fichero Peso.xlsx en Drive (Variable)
  ENTRENO_FILE_ID  -> ID del fichero Entreno 2026.xlsx en Drive (Variable)

Descarga a: data_src/Peso.xlsx y data_src/Entreno.xlsx
"""
import io
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_service():
    raw = os.environ.get("GDRIVE_SA_KEY")
    if not raw:
        sys.exit("ERROR: falta GDRIVE_SA_KEY (la llave de la cuenta de servicio).")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit("ERROR: GDRIVE_SA_KEY no es un JSON válido.")
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def download(service, file_id, dest):
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    req = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with io.FileIO(dest, "wb") as buf:
        downloader = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"Descargado {dest} ({os.path.getsize(dest)} bytes)")


def main():
    service = get_service()
    peso = os.environ.get("PESO_FILE_ID")
    entreno = os.environ.get("ENTRENO_FILE_ID")
    if not peso or not entreno:
        sys.exit("ERROR: faltan PESO_FILE_ID o ENTRENO_FILE_ID.")
    download(service, peso, "data_src/Peso.xlsx")
    download(service, entreno, "data_src/Entreno.xlsx")


if __name__ == "__main__":
    main()
