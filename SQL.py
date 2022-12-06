# このスクリプトは、このスクリプトはフォルダ内の画像のExif､PngチャンクをSQLに送る
# すべての画像が PIL が読み取れるファイルとして保存されていることを前提としています。

#from データセット インポート load_dataset
import os
import argparse #コマンドライン引数を扱えるようにするやつのインポート
import glob     #ディレクトリ内の一覧を取得してくるやつのインポート
from PIL import Image, ImageFilter #JPEGのExif用
from PIL.ExifTags import TAGS
import png #Pngチャンク用
import sqlite3
# パーサー オブジェクトを作成する
parser = argparse.ArgumentParser(description= "ExifToSQL")
# --dir_path 引数をパーサーに追加します
parser.add_argument("--dir_path", type=str, required=True)
# 引数を解析する
args = parser.parse_args()  


# 引数からディレクトリのパスを取得する
dir_path = args.dir_path

# 指定されたディレクトリ内にあるJPEGとPNGの画像ファイルを取得する
image_files = []
for root, dirs, files in os.walk(dir_path):
    for file in files:
        _, ext = os.path.splitext(file)
        if ext == ".jpg" or ext == ".jpeg" or ext == ".png":
            file_path = os.path.join(root, file)
            image_files.append(file_path)

# 指定されたディレクトリ内に画像ファイルが存在するかどうかを確認し、存在しない場合はプログラムを終了
if len(image_files) == 0:
    print("指定されたディレクトリ内にJPEGまたはPNGの画像ファイルが見つかりません。")
    exit()

# Exifを取得する
for file_path in image_files:
    file_info = {}
    if ext == ".jpg" or ext == ".jpeg":
    # JPEGの場合、PILモジュールを使ってExif情報を取得する
            with Image.open(file_path) as img:
                exif = img.getexif()
    if exif:
            file_info["jpeg_exif"] = exif
        
        # PNGの場合、pngモジュールを使ってPNGのチャンクを取得する
    elif ext == ".png":
                # PNGファイルをバイナリとして読み込む
                with open(file_path, "rb") as f:
                    # png.Readerクラスを使って、PNGファイルを読み込む
                    png_reader = png.Reader(file=f)
                # png.Readerクラスのchunks()メソッドで、PNGのチャンクを取得する
                chunks = png_reader.chunks()

                # 取得したチャンクを辞書に追加する
                file_info["png_chunks"] = list(chunks)

    # PNGフォーマットの情報をまとめる
                png_info = {"chunks": chunks}
                file_info["png_info"] = png_info


    # SQLiteデータベースに接続
    try:
        conn = sqlite3.connect("H:/Git/PnginfoPromptSQL/sql_test.db")
    except sqlite3.Error as e:
            print("データベースに接続できませんでした。")
            print(e)
            exit()

    # メタデータをSQLiteデータベースに登録する
    with conn:
            # sd_pnginfoテーブルが存在するかどうかを取得する
                cursor = conn.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'sd_pnginfo'
                """)
                # sd_pnginfoテーブルが存在しない場合
                if not cursor.fetchone():
                    # sd_pnginfoテーブルを作成する
                    conn.execute("""
                    CREATE TABLE sd_pnginfo (
                        file_path TEXT PRIMARY KEY,
                        file_info TEXT
                    )
                    """)

                # テーブルが存在しない場合は作成する
                try:
                    conn.execute("""
                        CREATE TABLE sd_pnginfo (
                            file_path TEXT PRIMARY KEY,
                            file_info TEXT
                        )
                    """)
                except sqlite3.Error as e:
                    print("テーブルの作成に失敗しました。")
                    print(e)
                    exit()


            # メタデータをINSERT文で登録する
                conn.execute("""
                    INSERT OR REPLACE INTO sd_pnginfo (file_path, file_info)
                    VALUES (?, ?)
                    """, (file_path, str(file_info)))

# SQLiteデータベースへの接続を閉じる
conn.close()