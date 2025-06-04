##一些小工具
import csv
import json
import os
import re
from pprint import pprint

def findFunctionInFolder(folder, functionName):
    ## 查找指定文件夹下的文件中是否含有functionName
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Open and read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if the function name exists in the file
                    if functionName in content:
                        print(f"Function '{functionName}' found in: {file_path}")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

def enforce_str_types(file_path, output_file):
    ## 将指定文件中的input和output字段强制转换为字符串类型
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for obj in data:
        if 'input' in obj:
            obj['input'] = str(obj['input'])
        if 'output' in obj:
            obj['output'] = str(obj['output'])

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)



def process_json_files(input_folder, output_file):
    # 用于存储所有处理后的数据
    aggregated_data = []

    # 遍历文件夹中的所有文件
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.json'):  # 只处理 .json 文件
                file_path = os.path.join(root, file)
                try:
                    # 读取 JSON 文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 处理 JSON 数据
                    for item in data:
                        processed_item = {
                            "instruction": item.get("instruction", ""),
                            "input": str(item.get("input", "")),  # 强制转换为字符串
                            "output": str(item.get("output", ""))  # 强制转换为字符串
                        }
                        aggregated_data.append(processed_item)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")

    # 将汇总数据写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, ensure_ascii=False, indent=4)
        print(f"Processed data has been saved to {output_file}")
    except Exception as e:
        print(f"Error writing to output file {output_file}: {e}")

import json

def validate_json(file_path: str) -> bool:
    """
    验证指定路径的 JSON 文件格式是否正确。
    成功返回 True，失败时打印错误并返回 False。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)  # 如果格式错误，这里会抛出 JSONDecodeError
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误：{e}")
        return False

def search_in_csv(file_path, column_name, search_value):
    results = []
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # 检查指定列是否包含目标值
            if search_value in row[column_name]:
                results.append(row)
    return results


if __name__ == "__main__":
    # findFunctionInFolder("Harmony2JavaFunctionPairs4","SchemeRainbow")
    process_json_files("FinetuningDataset/Pair4","FinetuningDataset/dataset_java2arkts_new.json")