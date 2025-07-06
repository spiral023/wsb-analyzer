"""
Modul zur Handhabung von AWS S3 Interaktionen.
Stellt Funktionen zum Hochladen, Herunterladen und Auflisten von Dateien bereit.
"""

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import logging
import os
from config import S3_CONFIG

# Konfiguriere das Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _get_bucket_name_from_arn(arn):
    """Extrahiert den Bucket-Namen aus einem S3-ARN."""
    try:
        return arn.split(':::')[1]
    except IndexError:
        logger.warning(f"Ungültiger S3-ARN: {arn}. Verwende den Wert direkt.")
        return arn

def get_s3_client():
    """Erstellt und gibt einen S3-Client zurück."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=S3_CONFIG['aws_access_key_id'],
            aws_secret_access_key=S3_CONFIG['aws_secret_access_key'],
            region_name=S3_CONFIG['region_name']
        )
        # Teste die Verbindung, indem wir die Buckets auflisten
        s3_client.list_buckets()
        return s3_client
    except (NoCredentialsError, PartialCredentialsError):
        logger.error("AWS-Anmeldeinformationen nicht gefunden. Bitte konfigurieren Sie sie.")
        return None
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == 'InvalidAccessKeyId':
            logger.error("Ungültige AWS Access Key ID. Bitte überprüfen Sie Ihre Konfiguration.")
        elif error_code == 'SignatureDoesNotMatch':
            logger.error("AWS Secret Access Key ist falsch. Bitte überprüfen Sie Ihre Konfiguration.")
        elif error_code == 'AccessDenied':
            logger.error("Zugriff auf S3 verweigert. Überprüfen Sie die IAM-Berechtigungen.")
        elif error_code == 'NoSuchBucket':
            logger.error(f"Der Bucket {S3_CONFIG.get('bucket_name')} existiert nicht.")
        else:
            logger.error(f"Ein Client-Fehler ist aufgetreten: {e}")
        return None
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist beim Verbinden mit S3 aufgetreten: {e}")
        return None

def upload_file(file_name, object_name=None):
    """
    Lädt eine Datei in einen S3-Bucket hoch.

    :param file_name: Pfad zur hochzuladenden Datei
    :param object_name: S3-Objektname. Wenn nicht angegeben, wird file_name verwendet.
    :return: True bei Erfolg, sonst False
    """
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = get_s3_client()
    if not s3_client:
        return False

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return False
    bucket_name = _get_bucket_name_from_arn(bucket_arn)

    try:
        logger.info(f"Lade {file_name} in Bucket {bucket_name} als {object_name} hoch...")
        s3_client.upload_file(file_name, bucket_name, object_name)
        logger.info(f"Upload von {file_name} erfolgreich.")
    except FileNotFoundError:
        logger.error(f"Die Datei {file_name} wurde nicht gefunden.")
        return False
    except NoCredentialsError:
        logger.error("Anmeldeinformationen nicht verfügbar.")
        return False
    except ClientError as e:
        logger.error(f"Fehler beim Hochladen der Datei: {e}")
        return False
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return False
    return True

def upload_file_obj(file_obj, object_name):
    """
    Lädt ein Datei-ähnliches Objekt in einen S3-Bucket hoch.

    :param file_obj: Das Datei-ähnliche Objekt (z.B. io.BytesIO)
    :param object_name: S3-Objektname.
    :return: True bei Erfolg, sonst False
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return False
    bucket_name = _get_bucket_name_from_arn(bucket_arn)

    try:
        logger.info(f"Lade Datei-Objekt in Bucket {bucket_name} als {object_name} hoch...")
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)
        logger.info(f"Upload des Datei-Objekts erfolgreich.")
    except NoCredentialsError:
        logger.error("Anmeldeinformationen nicht verfügbar.")
        return False
    except ClientError as e:
        logger.error(f"Fehler beim Hochladen des Datei-Objekts: {e}")
        return False
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return False
    return True


def download_file(object_name, file_name=None):
    """
    Lädt eine Datei aus einem S3-Bucket herunter.

    :param object_name: S3-Objektname
    :param file_name: Lokaler Pfad zum Speichern. Wenn nicht angegeben, wird der Basisname des Objekts verwendet.
    :return: True bei Erfolg, sonst False
    """
    if file_name is None:
        file_name = os.path.basename(object_name)
        
    s3_client = get_s3_client()
    if not s3_client:
        return False

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return False
    bucket_name = _get_bucket_name_from_arn(bucket_arn)

    try:
        logger.info(f"Lade {object_name} aus Bucket {bucket_name} nach {file_name} herunter...")
        s3_client.download_file(bucket_name, object_name, file_name)
        logger.info(f"Download von {object_name} erfolgreich.")
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            logger.error(f"Das Objekt {object_name} existiert nicht im Bucket {bucket_name}.")
        else:
            logger.error(f"Fehler beim Herunterladen der Datei: {e}")
        return False
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return False
    return True

def list_files(prefix=''):
    """
    Listet Dateien in einem S3-Bucket auf.

    :param prefix: Präfix zum Filtern der Objekte
    :return: Liste der Objektnamen oder None bei Fehler
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return None
    bucket_name = _get_bucket_name_from_arn(bucket_arn)
        
    try:
        logger.info(f"Liste Dateien im Bucket {bucket_name} mit Präfix '{prefix}' auf...")
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            files = [item['Key'] for item in response['Contents']]
            logger.info(f"{len(files)} Dateien gefunden.")
            return files
        else:
            logger.info("Keine Dateien mit diesem Präfix gefunden.")
            return []
    except ClientError as e:
        logger.error(f"Fehler beim Auflisten der Dateien: {e}")
        return None
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return None

def list_sessions(base_prefix):
    """
    Listet alle verfügbaren Session-Verzeichnisse unter einem Basis-Präfix auf.
    Ein Session-Verzeichnis hat das Format 'YYYY-MM-DD/HHMMSS/'.
    """
    s3_client = get_s3_client()
    if not s3_client:
        return []

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return []
    bucket_name = _get_bucket_name_from_arn(bucket_arn)

    sessions = set()
    
    # Liste Datum-Ordner (z.B. '2025-07-07/')
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        date_pages = paginator.paginate(Bucket=bucket_name, Prefix=base_prefix, Delimiter='/')
        
        for page in date_pages:
            if 'CommonPrefixes' in page:
                for date_prefix in page.get('CommonPrefixes', []):
                    date_path = date_prefix.get('Prefix')
                    
                    # Liste Zeit-Ordner (z.B. '210032/')
                    time_pages = paginator.paginate(Bucket=bucket_name, Prefix=date_path, Delimiter='/')
                    for time_page in time_pages:
                        if 'CommonPrefixes' in time_page:
                            for time_prefix in time_page.get('CommonPrefixes', []):
                                full_path = time_prefix.get('Prefix')
                                # Entferne das Basis-Präfix, um den relativen Session-Pfad zu erhalten
                                session_path = full_path.replace(base_prefix, '')
                                sessions.add(session_path)

    except ClientError as e:
        logger.error(f"Fehler beim Auflisten der S3-Sessions unter '{base_prefix}': {e}")
        return []

    sorted_sessions = sorted(list(sessions), reverse=True)
    logger.info(f"{len(sorted_sessions)} eindeutige Sessions gefunden.")
    return sorted_sessions

def get_file_content(object_name):
    """
    Liest den Inhalt einer Datei aus S3 als String.

    :param object_name: S3-Objektname
    :return: Dateiinhalt als String oder None bei Fehler
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None

    bucket_arn = S3_CONFIG.get('bucket_name')
    if not bucket_arn:
        logger.error("S3-Bucket-Name ist nicht konfiguriert.")
        return None
    bucket_name = _get_bucket_name_from_arn(bucket_arn)

    try:
        logger.info(f"Lese Inhalt von {object_name} aus Bucket {bucket_name}...")
        response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
        content = response['Body'].read().decode('utf-8', errors='ignore')
        logger.info(f"Inhalt von {object_name} erfolgreich gelesen.")
        return content
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            logger.error(f"Das Objekt {object_name} existiert nicht im Bucket {bucket_name}.")
        else:
            logger.error(f"Fehler beim Lesen der Datei: {e}")
        return None
    except Exception as e:
        logger.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        return None
