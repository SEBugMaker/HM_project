###
# Java -> ArkTS 第二轮翻译
# 通过Java的import检索API映射表，然后进一步翻译
###
import csv
import json
import os
from pprint import pprint

from langchain_community.document_loaders import JSONLoader
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv
from sqlalchemy.sql.sqltypes import NULLTYPE

import searchSimilarCode

load_dotenv(find_dotenv())
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

java_to_harmony_api_map = {}


def search_in_csv(file_path, column_name, search_value):
    results = []
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # 检查指定列是否包含目标值
            if search_value == row[column_name]:
                results.append(row)
    return results

def search_in_csv2(file_path, column_name, search_value):
    results = []
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # 检查指定列是否包含目标值
            if search_value in row[column_name]:
                results.append(row)
    return results

def get_API(javaCode):
    system_prompt = """
    你是一名专业的安卓开发工程师，你现在需要将一段安卓代码中的所有引用提取出来，请注意以下要求：
    1. 如果给出的代码存在import语句，可以作为后续参考，如果不存在import语句，需要自行阅读理解代码，并总结所有可能涉及到的import语句，请**保证使用安卓或者Java的原生API**，尽量不要使用第三方库
    2. 总结出所有涉及到的import后，为每一个import寻找函数中涉及到的该import类所调用到的方法，例如import android.content.ContentValues;，那么需要找到在我给出的代码中所有使用到的ContentValues类下的方法,请记住**只需要方法名，不需要后续的小括号与参数**
    3. 如果import的类只是用于创建对象，并未调用任何方法，则返回[]


    最终按照EXAMPLE JSON OUTPUT的格式返回。

    EXAMPLE JSON OUTPUT:
    {
        "output": dict类型，格式为<import语句（字符串），该import在这段代码中涉及到的方法调用（List）>
    }
    """
    res = ""

    user_prompt = "安卓代码为" + javaCode
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format={
            'type': 'json_object'
        }
    )
    try:
        import_messages = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        import_messages = {"output": {}}
    pprint(import_messages)

    # 读取csv文件
    file_path = 'results.csv'
    column_name = 'source_id'  # 替换为目标列名

    for key, value in import_messages["output"].items():
        # print(f"Import: {key}")
        if value == []:
            import_class = (key.split(".")[-1]).split(";")[0]
            toSearch = "android::" + import_class
            print(f"待检索内容{toSearch}")
            matches = search_in_csv2(file_path, column_name, toSearch)
            sorted_matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)[:5]
            res = res + "Java代码中import " + key + " 在翻译中可能用到的鸿蒙API有:\n"
            harmony_apis = []
            for match in sorted_matches:
                # print(match)
                res += "鸿蒙API: " + match["import_from"] + " 涉及到的方法描述为: " + match["target_text"] + "\n"
                harmony_apis.append(match["import_from"])
            # 更新全局映射字典
            java_to_harmony_api_map[key] = harmony_apis
        else:
            for method in value:
                import_class = (key.split(".")[-1]).split(";")[0]
                toSearch = "android::" + import_class + "." + method
                print(f"待检索内容{toSearch}")
                matches = search_in_csv(file_path, column_name, toSearch)
                sorted_matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)[:5]
                res = res + "Java代码中import " + key + " 涉及到的方法 "+ method +" 在翻译中可能用到的鸿蒙API有:\n"
                harmony_apis = []
                for match in sorted_matches:
                    # print(match)
                    res += "鸿蒙API: " + match["import_from"] + " 涉及到的方法描述为: " + match["target_text"] + "\n"
                    harmony_apis.append(match["import_from"])
                # 更新全局映射字典
                java_to_harmony_api_map[f"{key}.{method}"] = harmony_apis

    return res



system_prompt_translation = """
假如你是一名资深的鸿蒙应用开发人员，现在你将阅读一段安卓Java函数和初步翻译过的一版鸿蒙ArkTS函数，你需要对初步翻译进一步完善和改正。请注意以下几点：
1. 请判断给出的安卓函数是否是Java语言实现，如果是Kotlin请直接返回"kotlin function"
2. 请判断给出的Java代码是否是一个函数，**如果不是函数，返回"wrong format"**
3. 会给出3组ArkTS-Java的函数对作为翻译时的参考，你需要学习其中的语法等知识，请不要直接复制粘贴
4. 不一定是一句一句翻译，也可以按照实现功能一致，变量名和返回类型一致的要求翻译，**请注意一定是函数对应函数，能够保证实现功能效果一致**
5. 如果安卓函数涉及到R类等这种无法有效翻译到鸿蒙函数的内容，请直接返回"wrong format"
6. 会给出Java代码中涉及到的API和在翻译时可能用到的对应鸿蒙API的知识，你可以作为翻译润色时的参考
7. **请为最后结果中的Java代码和ArkTS代码都加上你润色时用到的import语句**
最终按照EXAMPLE JSON OUTPUT的格式返回。

EXAMPLE JSON OUTPUT:
{
    "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的安卓Java函数翻译为鸿蒙ArkTS函数",
    "input": 给出的安卓Java函数（字符串类型）,
    "output": 翻译润色后的鸿蒙ArkTS函数（字符串类型）
}
"""

folder_path = "./Harmony2JavaFunctionPairs4"
json_output_dir = "./FinetuningDataset/Pair4/"

filenames = []
for root, dirs, files in os.walk(json_output_dir):
    for file in files:
        filenames.append(file)

for filename in os.listdir(folder_path):
    res = []
    flag = True
    if filename == '.DS_Store':
        continue
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
        if flag == False:
            break
        text_data1 = json.loads(doc.page_content)
        JavaCode = text_data1["input"]
        ArkTSCode = text_data1["output"]
        similarCode = ""
        try:
            similarCode = searchSimilarCode.get_similar_code(JavaCode)
        except Exception as e:
            print(f"Error occurred while searching similar code: {e}")
            continue
        similarCode = str(similarCode)

        APIReference = get_API(JavaCode)

        user_prompt = ("鸿蒙代码为" + ArkTSCode + "\n" +
                       "Java代码为" + JavaCode + "\n" +
                       "参考翻译为: " + similarCode+
                       "API映射参考为: "+APIReference)
        messages = [{"role": "system", "content": system_prompt_translation},
                    {"role": "user", "content": user_prompt}]
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                response_format={
                    'type': 'json_object'
                }
            )
            if "kotlin function" in response.choices[0].message.content:
                # 如果检测到是kotlin函数，结束这个文档的翻译
                print("Detected Kotlin function, skipping this document.")
                flag = False
                break
            if "wrong format"  not in response.choices[0].message.content:
                # 将结果存储到res中
                result = json.loads(response.choices[0].message.content)
                # 添加 api_map 字段
                result["api_map"] = java_to_harmony_api_map.copy()
                pprint(result)
                res.append(result)
        except Exception as e:
            print(f"Error occurred while translating: {e}")
        finally:
            java_to_harmony_api_map.clear()
    with open(json_output_dir+filename, "w", encoding="utf-8") as json_file:
        json.dump(res, json_file, ensure_ascii=False, indent=4)
    print("Finished file: "+filename)
