###
# 将已有数据调整为微调数据集格式
###
import json
import os

from langchain_community.document_loaders import JSONLoader

entries = []

folder_path = "./function_pairs/TS-Java"

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    arkts_code = None
    java_code = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("```ArkTS") or line.startswith("```ts") or line.startswith("```TS"):
            arkts_code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                arkts_code.append(lines[i].rstrip())
                i += 1
            arkts_code = "\n".join(arkts_code)

        elif line.startswith("```Java") or line.startswith("```java") or line.startswith("```JAVA"):
            java_code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                java_code.append(lines[i].rstrip())
                i += 1
            java_code = "\n".join(java_code)

        if arkts_code and java_code:
            entries.append({
                "instruction": "你是一名鸿蒙开发工程师，擅长将安卓的Java函数翻译为鸿蒙的ArkTS函数",
                "input": java_code,
                "output": arkts_code
            })
            arkts_code = None
            java_code = None

        i += 1



file_path = "./function_pairs/merged_function_pairs.json"
loader = JSONLoader(
    file_path=file_path,
    jq_schema='.[]',
    text_content=False
)
data = loader.load()
for entry in data:
    text_data = json.loads(entry.page_content)
    entries.append({
        "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的鸿蒙函数翻译为安卓的Java函数",
        "input": text_data["JavaCode"],
        "output": text_data["TranslatedCode"]
    })


# 生成 JSON 文件
json_output_path = "./dataset_parallel.json"
with open(json_output_path, "w", encoding="utf-8") as json_file:
    json.dump(entries, json_file, ensure_ascii=False, indent=4)


loader = JSONLoader(
    file_path='./dataset_parallel.json',
    jq_schema='.[]',
    text_content=False
)

data = loader.load()

print(len(data))