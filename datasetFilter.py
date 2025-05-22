###
# 未使用
# 原本用于进一步过滤翻译结果
###
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
假如你是一名资深的鸿蒙应用开发人员，你需要阅读以下内容并判断给出的鸿蒙代码是UI还是非UI代码，判断的基本依据如下：
1. 包含build(),Column(),Row(),Stack(),Flex(),RelativeContainer,GridRow/GridCol,List,Grid/GridItem,Swiper,Tabs等常见布局组件
2. 上述布局中是否包含Button,Radio,Toggle,Progress,Image,Video(内容),XComponent,Text,TextArea,TextInput,Span,RichEditor,SymbolGlyph/SymbolSpan等常见UI组件
3. 参考https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/arkui中与ArkUI相关内容
**如果是UI代码，请直接返回wrong format**,如果代码为函数，请继续以下步骤：
1. **如果鸿蒙代码不是函数，请直接返回wrong format**
2. 用户会给出3组ArkTS-Java的函数对作为翻译的参考，你需要学习其中的翻译技巧和语法，请不要直接复制粘贴
3. 理解鸿蒙函数并检查是否有返回类型，如果没有的话请为鸿蒙函数添加返回类型，例如将public add(){return 1;}修改为public add(): number{return 1;}，但是具体返回值需要你自行理解并添加。
4. 判断给出的Java函数是否和鸿蒙函数对应，**包括但不限于检查函数功能是否一致、变量名和返回类型是否一致、是否是函数对应函数等。如果不对应，请修改安卓Java函数，注意使用并保留安卓原生API并保证是函数对应函数，参数对应一致，实现功能对应一致**。如果对应则不需要修改。

最终按照EXAMPLE JSON OUTPUT的格式返回。

EXAMPLE JSON OUTPUT:
{
    "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的安卓Java函数翻译为鸿蒙ArkTS函数",
    "input": 修改后的安卓Java函数（字符串类型）,
    "output": 修改后的鸿蒙ArkTS函数（字符串类型）
}
"""

folder_path = "./Harmony2JavaFunctionPairs3"
json_output_path = "./FinetuningDataset/Pair3/"


translated = []
for root, dirs, files in os.walk(json_output_path):
    for file in files:
        translated.append(file)


for filename in os.listdir(folder_path):
    if filename in translated:
        print(filename + " has been solved, skip")
        continue
    res = []
    file_path = os.path.join(folder_path, filename)

    print("resolve file: "+file_path)

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
        similarCode = ""
        try:
            similarCode = searchSimilarCode.get_similar_code(JavaCode)
        except Exception as e:
            print(f"Error occurred while searching similar code: {e}")
            continue
        similarCode = str(similarCode)
        user_prompt = ("鸿蒙代码为" + ArkTSCode + "\n" +
                       "Java代码为" + JavaCode + "\n" +
                       "参考翻译为："+similarCode)
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
            if "wrong format"  not in response.choices[0].message.content:
                # 将结果存储到res中
                pprint(json.loads(response.choices[0].message.content))
                res.append(json.loads(response.choices[0].message.content))
        except Exception as e:
            print(f"Error occurred while translating: {e}")
    with open(json_output_path+filename, "w", encoding="utf-8") as json_file:
        json.dump(res, json_file, ensure_ascii=False, indent=4)
    print("Finished file: "+filename)
