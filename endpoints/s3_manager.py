# S3-Менеджер, работающий для того чтобы прнимать файлы  #
# api/s3/upload/file - API для загрузки в S3 Хранилеще файлы (для этого нужно подать ему значения S3) #

import config 
import boto3
from main import app
import secrets
import requests
import os
from datetime import time
from flask import Flask, render_template, json, jsonify, redirect, request
from flask_login import login_manager, login_required, logout_user
from botocore.exceptions import NoCredentialsError, ClientError
from werkzeug.utils import secure_filename


S3_URL = os.environ["S3_URL"]
S3_BUCKET = os.environ["baget_name"]
S3_ACCESS_KEY = os.environ["S3_Access_Key"]
S3_SECRET_ACCESS_KEY = os.environ["S3_Secret_Access_Key"]
S3_REGION = os.environ["reguon"]




s3_client = boto3.client(
    's3',
    endpoint_url=S3_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)


@app.route("/api/s3/upload/file", methods=["GET", "POST"])
@login_required
def api_s3_upload():
   # Проверяем есть ли в запросе KEY от S3
   if 'file' not in request.files:
       return jsonify({'error': 'Ключ "file" отсутствует в запросе'}), 400
   
   file = request.files['file']

   # Проверка на то что у нас на подачу не пустой файл #
   if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

   try: 
       # Функция очиски от опастных файлов #
       filename = secure_filename(file.filename)

       # Создаем уникальный префикс для s3 хранилищя чтобы файлы с одинаковым названием не перезаписывались
       # Например - avatar_people.png > "a1b2c3d4_secret_filename.png"
       unique_prefix = secrets.token_hex(4)
       s3_key = f"{unique_prefix}_{filename}"



      # Используя API для загрузки S3 Файлов 
       s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type  # Сохраняем корректный MIME-тип (image/png, application/pdf и т.д.)
            }
        )

       file_url = f"{S3_URL.rstrip('/')}/{S3_BUCKET}/{s3_key}"

   return jsonify({'success': True, 'message': 'Файл успешно загружен в S3', 'filename': s3_key, 'url': file_url}), 200




@app.route("/api/s3/dowlonads", methods=["POST"])
@login_required
def dowloands_api():

    # Получаем имя из параметров #
    filename = request.args.get('filename')

    if not filename:
        return jsonify({'error': 'Параметр "filename" обязателен'}), 400

      try:
        # 2. Генерируем временную (presigned) ссылку на скачивание файла
        # Ссылка будет работать напрямую с S3 в обход вашего Flask-сервера
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': filename
            },
            ExpiresIn=3600  # Время жизни ссылки в секундах (3600 сек = 1 час)
        )

        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': presigned_url,
            'expires_in_seconds': 3600
        }), 200

    except ClientError as e:
        return jsonify({'error': f'Ошибка S3 при генерации ссылки: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'})






