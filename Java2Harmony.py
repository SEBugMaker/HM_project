import json
import os
from pprint import pprint

from langchain_community.document_loaders import JSONLoader
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

import searchSimilarCode

load_dotenv(find_dotenv())
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

# 用于过滤和进一步完善大模型翻译的代码对数据集
# 同时转为训练用数据集


system_prompt = """
假如你是一名资深的鸿蒙应用开发人员，你现在需要将给出的安卓的Java翻译成鸿蒙的ArkTS函数。请注意以下几点：
1. 用户会给出3组ArkTS-Java的函数对作为翻译的参考，你需要学习其中的语法等知识，请不要直接复制粘贴
2. 不一定是一句一句翻译，也可以按照实现功能一致，变量名和返回类型一致的要求翻译，**请注意一定是函数对应函数**
3. 如果安卓函数涉及到R类等这种无法有效翻译到鸿蒙函数的内容，请直接返回"wrong format"

最终按照EXAMPLE JSON OUTPUT的格式返回。

EXAMPLE JSON OUTPUT:
{
    "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的安卓Java函数翻译为鸿蒙ArkTS函数",
    "input": 给出的安卓Java函数（字符串类型）,
    "output": 翻译后的鸿蒙ArkTS函数（字符串类型）
}
"""

folder_path = "./functions"
json_output_dir = "./Harmony2JavaFunctionPairs4"

filenames = []
for root, dirs, files in os.walk(json_output_dir):
    for file in files:
        filenames.append(file)

for filename in os.listdir(folder_path):
    res = []
    if filename in filenames:
        print(filename + " has been translated, skip")
        continue
    file_path = os.path.join(folder_path, filename)

    print("Translating file: " + file_path)

    loader = JSONLoader(
        file_path=file_path,
        jq_schema='.[]',
        text_content=False
    )

    data = loader.load()
    for doc in data:
        text_data1 = json.loads(doc.page_content)
        for text in text_data1:
            JavaCode = text

            similarCode = ""
            try:
                similarCode = searchSimilarCode.get_similar_code(JavaCode)
            except Exception as e:
                similarCode = "无相似代码"
                print(f"Error occurred while searching similar code: {e}")
            similarCode = str(similarCode)
            user_prompt = (
                    "Java代码为" + JavaCode + "\n" +
                    "参考翻译为：" + similarCode
            )
            messages = [{"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}]
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    response_format={
                        'type': 'json_object'
                    }
                )
                if "wrong format" not in response.choices[0].message.content:
                    # 将结果存储到res中
                    pprint(json.loads(response.choices[0].message.content))
                    res.append(json.loads(response.choices[0].message.content))
            except Exception as e:
                print(f"Error occurred while translating: {e}")
    with open(json_output_dir+ "/" + filename, "w", encoding="utf-8") as json_file:
        json.dump(res, json_file, ensure_ascii=False, indent=4)
    print("Translation completed for file: " + filename)
    print("**************************************************")
