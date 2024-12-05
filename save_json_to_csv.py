import json
import pandas as pd

# JSON data
file_path = 'output_0905.json'
with open(file_path, 'r', encoding='utf-8') as file:
    json_data = file.read()

data = json.loads(json_data)

def process_conductivity_data(data):
    new_data = {}

    for url, entries in data.items():
        new_entries = []
        for entry in entries:
            if isinstance(entry, dict):
                # 提取除 Conductivity 外的所有键值对
                base_record = {k: v for k, v in entry.items() if k != "Conductivity"}

                if "Conductivity" in entry and entry["Conductivity"]:
                    for conductivity in entry["Conductivity"]:
                        # 创建一个新的记录，包含 base_record 的所有数据以及当前的 Conductivity 数据
                        new_record = base_record.copy()
                        new_record["Conductivity"] = conductivity
                        new_entries.append(new_record)
                else:
                    new_entries.append(base_record)
            else:
                # 如果 entry 不是字典，直接添加到新条目中
                new_entries.append(entry)
        
        new_data[url] = new_entries
    
    return new_data


def json_to_csv_recursive(data):
    rows = []
    columns = set()

    def flatten_dict(d, parent_key='', sep='.'):
        if not isinstance(d, dict):
            return {parent_key: d}
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v, start=1):
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, f"{new_key}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)

    ordered_columns = ["url"]

    for url, entries in data.items():
        for entry in entries:
            row = {"url": url}
            flat_entry = flatten_dict(entry)

            for k, v in flat_entry.items():
                if k not in columns:
                    columns.add(k)
                    ordered_columns.append(k)
                row[k] = v

            rows.append(row)

    df = pd.DataFrame(rows)
    df = df.reindex(columns=ordered_columns)
    
    return df


processed_data = process_conductivity_data(data)
df = json_to_csv_recursive(processed_data)
csv_file_path = "output_data.csv"
df.to_csv(csv_file_path, index=False,encoding='utf-8')

csv_file_path