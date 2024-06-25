from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO, emit
from datetime import datetime
from flask_mysqldb import MySQL
import time
import re
import pytz
import pymysql



app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'mqtt.flespi.io'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'hds7ZvnDXPNfUMKKOh7mZmOwOP5RAvgIywDlRPOCupFe2fNEnIPcUrwx6pevKk36'
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

mqtt = Mqtt(app)
socketio = SocketIO(app)

def create_connection():
    """ Tạo kết nối đến cơ sở dữ liệu MySQL. """
    try:
        connection = pymysql.connect(
            host='localhost',    # Địa chỉ máy chủ MySQL
            user='root',         # Tên người dùng
            password='',         # Mật khẩu, để trống nếu không có mật khẩu
            db='data_abc',  # Tên cơ sở dữ liệu
            charset='utf8mb4',   # Bộ mã hóa ký tự
            cursorclass=pymysql.cursors.DictCursor  # Dùng DictCursor để dữ liệu trả về dưới dạng dictionary
        )
        return connection
    except Exception as e:
        print(f"An error occurred when connecting to the database: {e}")
        return None

def fetch_data(connection, formatted_time, humidity, temperature):
    try:
        with connection.cursor() as cursor:
            # sql = "INSERT INTO data (humidity, temperature ) VALUES (%s, %s)"
            # sql = "SELECT * FROM data3"
            sql = "INSERT INTO data3 (date, humidity, temperature) VALUES (%s, %s, %s)"
            cursor.execute(sql, (formatted_time, humidity, temperature))
            connection.commit()
            for databases in cursor:
                print(databases)
    except Exception as e:
        print(f"An error occurred when fetching data: {e}")
# Use lists to store all received data
received_data = []


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('TEST1')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    payload = message.payload.decode()
    match = re.match(r'(\d+)%?, (\d+\.\d+)\s*°C', payload)
    if match:
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        humidity = int(match.group(1))
        temperature = float(match.group(2)) 
        data = {
            'time': formatted_time,
            'temperature': temperature,
            'humidity': humidity
        }
        received_data.append(data)
        socketio.emit('mqtt_message', data)
        connection = create_connection()
        #if connection:
        fetch_data(connection, formatted_time, humidity, temperature)
        
        connection.close()

@app.route('/')
def index():
    return render_template('index.html', data=received_data)

if __name__ == '__main__':
    socketio.run(app, debug=True)

