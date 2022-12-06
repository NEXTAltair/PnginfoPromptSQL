# このスクリプトは、このスクリプトはフォルダ内の画像のExif､PngチャンクをSQLに送る
# すべての画像が PIL が読み取れるファイルとして保存されていることを前提としています。

#from データセット インポート load_dataset
import os
import argparse #コマンドライン引数を扱えるようにするやつのインポート
import glob     #ディレクトリ内の一覧を取得してくるやつのインポート
from PIL.ExifTags import TAGS
from PIL import Image, ImageFilter
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

# 画像ファイルの数を確認する
if len(image_files) == 0:
    print("指定されたディレクトリ内にJPEGまたはPNGの画像ファイルが見つかりません。")
    exit()

# メタデータを取得する
    for file_path in image_files:
    # ファイルの拡張子を取得する
        _, ext = os.path.splitext(file_path)

        # JPEGとPNGのメタデータを取得する
        file_info = {}
        if ext == ".jpg" or ext == ".jpeg":
        # JPEGの場合、PILモジュールを使ってExif情報を取得する
            with Image.open(file_path) as img:
                exif = img.getexif()
        if exif:
            file_info["jpeg_exif"] = exif
        
        # PNGの場合pngフォーマットの情報を取得する
        elif ext == ".png":
            # PNGファイルをバイナリとして読み込む
            with open(file_path, "rb") as f:
                # 最初の8バイトはPNGの署名
                png_signature = f.read(8)

            # 残りの部分は、1つ以上のチャンク
            chunks = []
            while True:
                # チャンク長を取得
                chunk_length_bytes = f.read(4)
                # チャンク長が0の場合、これ以降のチャンクは存在しない
                if chunk_length_bytes == b"\x00\x00\x00\x00":
                    break
                # チャンク長を32ビット符号付き整数として解釈する
                chunk_length = int.from_bytes(chunk_length_bytes, "big")

                # チャンク長分のデータを取得する
                chunk_data = f.read(chunk_length)

                # チャンク長を辞書に追加する
                chunks.append({"length": chunk_length, "data": chunk_data})

                # PNGフォーマットの情報をまとめる
                png_info = {"signature": png_signature, "chunks": chunks}
                file_info["png_info"] = png_info


                # SQLiteデータベースに接続
                conn = sqlite3.connect("/SQLTest.db")
                # メタデータをSQLiteデータベースに登録する
                with conn:
                # テーブルが存在しない場合は作成する
                    conn.execute("""
                    CREATE TABLE IF NOT EXISTS image_metadata (
                    ile_path TEXT PRIMARY KEY,
                    file_info TEXT
                    )
                    """)

                    # メタデータをINSERT文で登録する
                    conn.execute("""
                    INSERT OR REPLACE INTO image_metadata (file_path, file_info)
                    VALUES (?, ?)
                    """, (file_path, str(file_info)))

                    # SQLiteデータベースへの接続を閉じる
                    conn.close()