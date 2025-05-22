###
# ArkTS函数翻译至Java函数
# getNaturalLanguage -> 获取自然语言描述
# TransArkTSFunction -> 翻译单个函数
###
import json
import os
from pprint import pprint

from langchain_community.document_loaders import JSONLoader
from langchain_deepseek import ChatDeepSeek
from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import ChatPromptTemplate

import searchSimilarCode

load_dotenv(find_dotenv())
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    response_format={"type": "json_object"},  # 强制返回 JSON 格式

)

def metadata_func(record: dict, metadata: dict) -> dict:
    if "source" in metadata:
        del metadata["source"]
    return metadata


def getNaturalLanguage(text):
    prompt = ChatPromptTemplate(
        [
            (
                "system",
                '''
    如果你是一名鸿蒙开发工程师，你现在需要将以下代码函数转换为对应的自然语言描述，要求如下：
    1. 请根据函数的名称、返回值、使用的函数、具体的代码逻辑推断函数的功能，并给出**详细描述**
    最终按照EXAMPLE JSON OUTPUT的格式返回。

    EXAMPLE JSON OUTPUT:
    {{
        "output": 关于该函数的自然语言描述（字符串类型）
    }}
                ''',
            ),
            ("human", "ArkTS函数为: {input}"),
        ]
    )

    chain = prompt | llm

    res = chain.invoke(
        {
            "input": text
        }
    )

    pprint(res.content)

    try:
        nl = json.loads(res.content)["output"]
        return nl
    except json.decoder.JSONDecodeError:
        return "自然语言描述出错"


def TransArkTSFunction(ArkTSCode):

    prompt = ChatPromptTemplate(
        [
            (
                "system",
                '''
    如果你是一名安卓Java工程师，你现在正在将鸿蒙ArkTS函数翻译为安卓的Java函数，下面是翻译时的要求：
    1. 现在你需要阅读以下鸿蒙的ArkTS函数，在理解函数逻辑和实现效果后将其翻译成Java函数。
    2. 翻译时会给出关于这个函数的自然语言描述{nl}，这将作为翻译的参考之一，你需要保证翻译后的Java函数尽可能与自然语言描述相匹配。**请尽可能使用安卓原生API进行翻译**，生成结果时不需要进行额外解释。
    3. 如果没有给出有效的自然语言描述，请阅读给出的鸿蒙ArkTS函数，在理解函数逻辑和实现效果后将其翻译成Java函数，你需要保证翻译后的Java函数尽可能与自然语言描述相匹配。**请尽可能使用安卓原生API进行翻译**，生成结果时不需要进行额外解释。
    3. **如果需要翻译的内容并非函数请直接返回"wrong format"**
    4. **最终翻译的Java函数需要加上使用的所有import**
    5. 如果这里的函数可能并不完整，你需要自行判断返回值。
    6. 将给出几组ArkTS-Java代码对作为翻译参考{similarCode}
    最终按照EXAMPLE JSON OUTPUT的格式返回。

    EXAMPLE JSON OUTPUT:
    {{
        "instruction": "你是一名资深的鸿蒙开发工程师，你需要将给出的安卓Java函数翻译为鸿蒙ArkTS函数",
        "input": 翻译后的安卓Java函数（字符串类型）,
        "output": 原鸿蒙ArkTS函数（字符串类型）
    }}
                ''',
            ),
            ("human", "ArkTS函数为{input}"),
        ]
    )

    chain = prompt | llm

    nl = getNaturalLanguage(ArkTSCode)

    similarCode = ""
    try:
        similarCode = searchSimilarCode.get_similar_code2(ArkTSCode)
    except Exception as e:
        print(f"Error occurred while searching similar code: {e}")
        similarCode = "没有相似代码对"

    similarCode = str(similarCode)

    res = chain.invoke(
        {
            "nl": nl,
            "input": ArkTSCode,
            "similarCode": similarCode,
        }
    )

    try:
        res1 = json.loads(res.content)
        pprint(res1)
        return res1
    except json.decoder.JSONDecodeError:
        print("error")
        return "error"

def TransJSON(filename):
    loader = JSONLoader(
        file_path=filename,
        jq_schema='.[]',
        text_content=False,
        metadata_func=metadata_func
    )

    data = loader.load()

    res = []

    for doc in data:
        try:
            text_data = json.loads(doc.page_content)
            # 根据具体json格式修改
        except json.decoder.JSONDecodeError:
            continue

if __name__ == "__main__":
    #example
    TransArkTSFunction('''
    import hilog from '@ohos.hilog';\nimport prompt from '@ohos.prompt';\n\n@Component\nstruct MyComponent {\n  @State message: string = '';\n\n  build() {\n    Column() {\n      Button('点击打印日志')\n        .onClick(() => {\n          this.message = 'click';\n          for (let i = 0; i < 10; i++) {\n            hilog.info(0x0000, 'TAG', '%{public}s', this.message);\n          }\n          prompt.showToast({\n            message: '日志已打印',\n            duration: 2000\n          });\n        })\n        .width('90%')\n        .backgroundColor(Color.Blue)\n        .fontColor(Color.White)\n        .margin({\n          top: 10\n        })\n    }\n    .justifyContent(FlexAlign.Start)\n    .alignItems(HorizontalAlign.Center)\n    .margin({\n      top: 15\n    })\n  }\n}
    ''')

