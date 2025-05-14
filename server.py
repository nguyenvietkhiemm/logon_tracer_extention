from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import time
from flask import Flask, send_file

#### export #####

from neo4j import GraphDatabase
import json
import csv
import requests
from bs4 import BeautifulSoup


def export():
    URL_DB = "bolt://localhost:7687"  # hoặc IP nếu là máy khác
    driver = GraphDatabase.driver(URL_DB, auth=("neo4j", "password"))

    def login_to_flask(server_url, username, password):
        login_url = f"{server_url}/login"
        try:
            # 1. Lấy CSRF Token
            client = requests.session()  # Sử dụng session để giữ cookie
            response = client.get(login_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token = soup.find('input', {'id': 'csrf_token'})['value']

            # 2. Gửi yêu cầu POST để đăng nhập
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token,
                'remember': 'y'  # Thêm 'remember' nếu có
            }
            response = client.post(login_url, data=login_data)

            # 3. Kiểm tra đăng nhập thành công
            if response.status_code == 200 and "Invalid username or password" not in response.text:
                print("Đăng nhập thành công!")
                return client  # Trả về đối tượng session
            else:
                print("Đăng nhập thất bại. Kiểm tra username/password/CSRF token.")
                return None

        except Exception as e:
            print(f"Lỗi: {e}")
            return None

    def upload_security_evtx(session, server_url, evtx_file_path, timezone, casename, addlog=True, sigmascan=False):
        try:
            if not os.path.exists(evtx_file_path):
                print(f"Lỗi: File EVTX không tồn tại tại {evtx_file_path}")
                return "FAIL", {}

            files = {'file0': open(evtx_file_path, 'rb')}
            data = {
                'timezone': timezone,
                'logtype': 'EVTX',
                'addlog': 'true' if addlog else 'false',
                'sigmascan': 'true' if sigmascan else 'false',
                'casename': casename,
            }

            response = session.post(
                f"{server_url}/upload", files=files, data=data)
            cookies = response.cookies.get_dict()

            print(response.text)

            if response.text == "SUCCESS":
                return "SUCCESS", cookies
            else:
                print(f"Lỗi từ server: {response.text}")
                return "FAIL", {}

        except Exception as e:
            print(f"Lỗi: {e}")
            return "FAIL", {}

    server_url = "http://localhost:8080"
    username = "neo4j"
    password = "password"
    session = login_to_flask(server_url, username, password)
    if session:
        uploads_folder = r"D:\\_test\\logon_tracer\\extend\\uploads"  # đường dẫn uploads
        timezone = 7
        casename = "neo4j"
        for filename in os.listdir(uploads_folder):
            if filename.lower().endswith(".evtx"):
                evtx_file = os.path.join(uploads_folder, filename)
                result, cookies = upload_security_evtx(
                    session, server_url, evtx_file, timezone, casename)
                print(
                    f"Tải lên {filename}: {result}, vui lòng chờ backend xử lý 😾")
    else:
        print("Không thể đăng nhập.")

################


app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
CORS(app)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
client_states = {}
PING = 10


@app.route('/ping', methods=['GET'])
def ping():
    client_name = request.args.get('client_name')
    if not client_name:
        return jsonify({'error': 'Missing client_name'}), 400

    # Lưu thời điểm kết nối đầu tiên của client
    if client_name not in client_states:
        client_states[client_name] = 0

    request_data = False
    if client_states[client_name] >= PING:
        request_data = True
        # client_states[client_name] = 0

    if (client_states[client_name] < PING):
        client_states[client_name] += 1

    print(client_states)
    return jsonify({'request_data': request_data})


@app.route('/upload', methods=['POST'])
def upload_file():
    client_name = request.args.get('client_name')
    if not client_name:
        return jsonify({'error': 'Missing client_name'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = os.path.join(
            app.config['UPLOAD_FOLDER'], f"{client_name}_{file.filename}")
        file.save(filename)

        # Reset sau khi upload xong
        client_states[client_name] = 0

        return jsonify({'message': f"Đã nhận file '{file.filename}' từ client '{client_name}'"}), 200
    return jsonify({'error': 'Something went wrong'}), 500


@app.route('/', methods=['GET'])
def server_info():
    return send_file('./fe/index.html')


@app.route('/clients', methods=['GET'])
def get_clients():
    return jsonify(client_states)


@app.route('/export', methods=['GET'])
def do_export():
    export()
    return jsonify("oke")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
