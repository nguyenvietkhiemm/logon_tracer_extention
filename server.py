from flask import Flask, request, jsonify
import os
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'

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
        client_states[client_name] = 0
        
    client_states[client_name]+=1
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

        return jsonify({'message': f"Đã nhận file '{file.filename}' từ client '{client_name}'"}), 200
    return jsonify({'error': 'Something went wrong'}), 500


@app.route('/', methods=['GET'])
def server_info():
    return "Đây là địa chỉ máy chủ. Chỉ có thể gửi dữ liệu thôi 🌼🌼🌼😼😼😼"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
