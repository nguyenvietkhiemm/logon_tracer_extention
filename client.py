import requests
import os
import sys
import time
import threading

CLIENT_NAME_FILE = './client_name.txt'
PING_INTERVAL = 3  # Thời gian ping (giây)
# SERVER_URL = 'http://26.35.184.44:5000'  # Địa chỉ máy chủ
SERVER_URL = 'http://localhost:5000'

PING_ENDPOINT = '/ping'
UPLOAD_ENDPOINT = '/upload'
PATH = "C:\Windows\System32\winevt\Logs\\"
DATA_FILE = 'Security.evtx'

client_name = ""
has_admin_rights = False


def is_admin():
    try:
        return os.geteuid() == 0  # For Linux/macOS
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # For Windows


def run_as_admin():
    global has_admin_rights
    if sys.platform == "win32":
        if not is_admin():
            import ctypes
            print("Yêu cầu quyền admin để đọc file nhật ký...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
        else:
            print("Đã có quyền admin.")
            has_admin_rights = True
    else:
        has_admin_rights = True


if os.path.exists(CLIENT_NAME_FILE):
    with open(CLIENT_NAME_FILE, 'r') as f:
        client_name = f.readline().strip()
    print(f"Đã đọc tên client từ file: {client_name}")
else:
    client_name = input("Vui lòng nhập tên client: ")
    with open(CLIENT_NAME_FILE, 'w') as f:
        f.write(client_name + '\n')
    print(f"Đã lưu tên client '{client_name}' vào file.")


def ping_server():
    """Gửi ping lên máy chủ."""
    ping_url = f"{SERVER_URL}{PING_ENDPOINT}"
    try:
        response = requests.get(ping_url, params={'client_name': client_name})
        response.raise_for_status()
        data = response.json()
        if data.get('request_data'):
            print("Máy chủ yêu cầu dữ liệu!")
            send_data()
        else:
            print(
                f"Đã ping máy chủ. Yêu cầu dữ liệu: {data.get('request_data')}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi ping máy chủ: {e}")
    except Exception as e:
        print(f"Lỗi không xác định khi ping: {e}")
    finally:
        threading.Timer(PING_INTERVAL, ping_server).start()


def send_data():
    """Gửi dữ liệu lên máy chủ."""
    upload_url = f"{SERVER_URL}{UPLOAD_ENDPOINT}"
    base_name, ext = os.path.splitext(DATA_FILE)
    new_file_name = f"{base_name}_{client_name}{ext}"

    if os.path.exists(PATH + DATA_FILE):
        try:
            with open(PATH + DATA_FILE, 'rb') as f:
                print("Đang truyền dữ liệu lên máy chủ...")
                files = {'file': (new_file_name, f)}
                response = requests.post(upload_url, files=files, params={
                                         'client_name': client_name})
                response.raise_for_status()
                data = response.json()
                print(f"Máy chủ phản hồi: {data.get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi gửi dữ liệu: {e}")
        except Exception as e:
            print(f"Lỗi không xác định khi gửi dữ liệu: {e}")
    else:
        print(f"Không tìm thấy file dữ liệu: {DATA_FILE}")


if __name__ == "__main__":

    run_as_admin()

    if not has_admin_rights and sys.platform == "win32":
        print("Không thể tiếp tục nếu không có quyền admin để đọc dữ liệu.")
        sys.exit(1)
    print(f"Client '{client_name}' đã khởi động.")
    # Bắt đầu tiến trình ping định kỳ
    ping_server()

    # Giữ cho chương trình chính tiếp tục chạy để thread ping hoạt động
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client đã dừng.")
