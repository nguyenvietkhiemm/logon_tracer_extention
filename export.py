from neo4j import GraphDatabase
import json
import csv
import requests
import os
from bs4 import BeautifulSoup


def export():
    """
    Exports node and relationship data from a Neo4j database to CSV files.
    """
    URL_DB = "bolt://localhost:7687"  # hoặc IP nếu là máy khác
    driver = GraphDatabase.driver(URL_DB, auth=("neo4j", "password"))

    def login_to_flask(server_url, username, password):
        """
        Logs in to a Flask server to obtain a session for file upload.

        Args:
            server_url (str): The URL of the Flask server.
            username (str): The username for login.
            password (str): The password for login.

        Returns:
            requests.Session: A session object if login is successful, None otherwise.
        """
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
        """
        Uploads a security EVTX file to the Flask server.

        Args:
            session (requests.Session): The session object for making the request.
            server_url (str): The URL of the Flask server.
            evtx_file_path (str): The path to the EVTX file.
            timezone (int): The timezone.
            casename (str): The case name.
            addlog (bool, optional): Whether to add log. Defaults to True.
            sigmascan (bool, optional): Whether to perform Sigma scanning. Defaults to False.

        Returns:
            tuple: A tuple containing the status ("SUCCESS" or "FAIL") and cookies.
        """
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

    def get_all_nodes(tx):
        """
        Retrieves all nodes from the Neo4j database.

        Args:
            tx (neo4j.Transaction): The Neo4j transaction.

        Returns:
            list: A list of node data.
        """
        query = "MATCH (n) RETURN n"
        result = tx.run(query)
        nodes_data = []
        for record in result:
            node = record["n"]
            properties = dict(node)
            nodes_data.append({"id": node.id, "labels": list(
                node.labels), "properties": properties})
        return nodes_data

    def get_all_relationships(tx):
        """
        Retrieves all relationships from the Neo4j database.

        Args:
            tx (neo4j.Transaction): The Neo4j transaction.

        Returns:
            list: A list of relationship data.
        """
        query = "MATCH ()-[r]->() RETURN r"
        result = tx.run(query)
        relationships_data = []
        for record in result:
            relationship = record["r"]
            relationships_data.append({
                "id": relationship.id,
                "type": relationship.type,
                "start_node_id": relationship.start_node.id,
                "end_node_id": relationship.end_node.id,
                "properties": dict(relationship)
            })
        return relationships_data

    # Flask Login and EVTX Upload
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

    # Get and Export Nodes
    with driver.session() as session:
        all_nodes = session.execute_read(get_all_nodes)
        json_output = json.dumps(all_nodes, indent=2)

        csv_file_path = "./data/nodes.csv"
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["id", "labels", "properties"]  # Xác định các cột
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for node_data in all_nodes:
                writer.writerow(node_data)
        print(f"\n Lưu data nodes vào file: {csv_file_path}")

    # Get and Export Relationships
    with driver.session() as session:
        all_relationships = session.execute_read(get_all_relationships)
        json_output = json.dumps(all_relationships, indent=2)

        csv_file_path = "./data/relationships.csv"
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["id", "type", "start_node_id",
                          "end_node_id", "properties"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for relationship_data in all_relationships:
                writer.writerow(relationship_data)
        print(f"\n Lưu data relationships vào file: {csv_file_path}")
    driver.close()


if __name__ == '__main__':
    export()
