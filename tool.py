import json
import os
import re
##一些用到的小工具


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

findFunctionInFolder("./functions", "compositeOverlay")
