from neo4j import GraphDatabase
import json
import ast
import re

URL = "bolt://localhost:7687"  # hoặc IP nếu là máy khác

driver = GraphDatabase.driver(URL, auth=("neo4j", "password"))

def get_logon_data(tx):
    query= "MATCH (n) RETURN n LIMIT 25"
    result = tx.run(query)
    
    # Chuyển đổi kết quả thành danh sách Python
    logon_data = []
    for record in result:
        logon_data.append(record["n"])
    
    return logon_data

# Chạy truy vấn và xuất kết quả ra JSON
with driver.session() as session:
    logon_data = session.read_transaction(get_logon_data)
    # Chuyển kết quả thành định dạng JSON
    json_data = json.dumps(logon_data, default=str, indent=2)

raw_nodes = json_data

parsed_nodes = []

for node_str in raw_nodes:
    # Tách phần 'properties={...}'
    match = re.search(r"properties=(\{.*\})>", node_str)
    if match:
        prop_str = match.group(1)
        try:
            # Chuyển chuỗi dict thành Python dict
            prop_dict = ast.literal_eval(prop_str)
            parsed_nodes.append(prop_dict)
        except Exception as e:
            print(f"Lỗi khi parse node: {e}")

# Chuyển sang pandas DataFrame nếu cần
import pandas as pd
df = pd.DataFrame(parsed_nodes)
print(df.head())
