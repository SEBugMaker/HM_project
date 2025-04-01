import json
import os
from pprint import pprint

from langchain_community.document_loaders import JSONLoader
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv



load_dotenv(find_dotenv())
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

# 用于过滤和进一步完善大模型翻译的代码对数据集
# 同时转为训练用数据集


system_prompt = """
假如你是一名资深的鸿蒙应用开发人员，你需要阅读以下内容并判断给出的鸿蒙代码是UI还是非UI代码，
**如果是UI代码，请直接返回wrong format**,如果代码为函数，请继续以下步骤：
1. **如果鸿蒙代码不是函数，请直接返回wrong format**
1. 理解鸿蒙函数并检查是否有返回类型，如果没有的话请为鸿蒙函数添加返回类型，例如将public add(){return 1;}修改为public add(): number{return 1;}，但是具体返回值需要你自行理解并添加。
2. 判断给出的Java函数是否和鸿蒙函数对应，包括但不限于检查函数功能是否一致、变量名和返回类型是否一致、是否是函数对应函数等。如果不对应，请进行修改，注意使用安卓原生API并保证是函数对应函数。如果对应则不需要修改。
最终按照EXAMPLE JSON OUTPUT的格式返回。

EXAMPLE JSON OUTPUT:
{
    "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的鸿蒙函数翻译为安卓的Java函数",
    "input": 修改后的安卓Java函数,
    "output": 修改后的鸿蒙ArkTS函数
}
"""

folder_path = "./Harmony2JavaFunctionPairs"

res=[]

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    print(file_path)

    loader = JSONLoader(
        file_path=file_path,
        jq_schema='.[]',
        text_content=False
    )

    data = loader.load()
    for doc in data:
        text_data1 = json.loads(doc.page_content)
        JavaCode = text_data1["JavaCode"]
        ArkTSCode = text_data1["ArkTSCode"]
        user_prompt = ("鸿蒙代码为" + ArkTSCode + "\n" +
                       "Java代码为" + JavaCode + "\n")
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
            if "wrong format" in response.choices[0].message.content:
                continue
            else:
                # 将结果存储到res中
                pprint(json.loads(response.choices[0].message.content))
                res.append(json.loads(response.choices[0].message.content))
        except Exception as e:
            print(f"Error occurred while translating: {e}")

json_output_path = "dataset1.json"
with open(json_output_path, "w", encoding="utf-8") as json_file:
    json.dump(res, json_file, ensure_ascii=False, indent=4)

