import mysql.connector
from mysql.connector import Error
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': "root",
    'password': "vuhoangquan2004",
    'database': 'Video_storge'
}

def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def close_connection(connection, cursor):
    """
    Đóng cursor và connection nếu chúng đang mở
    """
    if connection and connection.is_connected():
        if cursor:
            cursor.close()
        connection.close()

def create_table(): # tạo bảng videos nếu chưa tồn tại
    connection = get_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                video_Title VARCHAR(255) NOT NULL,
                path TEXT,
                upload_Date DATETIME NOT NULL,
                original_Name VARCHAR(255) NOT NULL,
                processed_Filename VARCHAR(255)
            )
        """)
        connection.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        close_connection(connection, cursor)

def insert_video(video_Title, path, upload_Date, original_Name): #Lưu dữ liệu của metadata của video gốc.
    conection = get_connection()
    if conection is None:
        return False
    try:
        cursor = conection.cursor()
        cursor.execute("""
                       INSERT INTO videos (video_Title, path, upload_Date, original_Name, processed_Filename)
                       VALUES (%s, %s, %s, %s, NULL)""",
                       (video_Title, path, upload_Date, original_Name))
        conection.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        close_connection(conection, cursor)


def get_video_path(video_Title): # lấy đường dẫn video gốc từ bảng mysql
    connection = get_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT path FROM videos WHERE video_Title = %s", (video_Title,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"Error: {e}")
        return None
    finally:
        close_connection(connection, cursor)

def get_video_info(video_Title):
    connection = get_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)  # Trả về dictionary
        cursor.execute("SELECT video_Title, processed_Filename FROM videos WHERE video_Title = %s", (video_Title,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error: {e}")
        return None
    finally:
        close_connection(connection, cursor)

def get_all_videos():# lấy danh sách video từ bảng videos
    connection = get_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM videos")
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error: {e}")
        return []
    finally:
        close_connection(connection, cursor)
        
def update_processed_filename(video_Tiltle, processed_Filename): # cập nhật tên file đã xử lý vào bảng videos
    connection = get_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE videos
            SET processed_Filename = %s
            WHERE video_Title = %s
        """, (processed_Filename, video_Tiltle))
        connection.commit()
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        close_connection(connection, cursor)

create_table() # tạo bảng videos nếu chưa tồn tại
