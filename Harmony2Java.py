import json
import os
from pprint import pprint

from dotenv import find_dotenv, load_dotenv
from langchain_community.document_loaders import JSONLoader

import searchSimilarCode

load_dotenv(find_dotenv())
DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]
from langchain_community.llms import Tongyi
from langchain.prompts import PromptTemplate

codeToTranslate = '''
    '''


# 定义元数据提取函数。
def metadata_func(record: dict, metadata: dict) -> dict:
    if "source" in metadata:
        del metadata["source"]
    return metadata


def translate_code_from_file(filepath):
    llm = Tongyi(temperature=1)
    template = '''
    如果你是一名安卓Java工程师，你现在正在将鸿蒙ArkTS函数翻译为安卓的Java函数，现在你需要阅读以下鸿蒙的ArkTS函数和与之有关的描述，并将其翻译成Java函数。
    生成结果时不需要进行额外解释，请尽可能使用安卓原生API进行翻译。
    **如果需要翻译的内容并非函数请直接返回"wrong format"，最终结果有且仅需要按照函数加上函数涉及到的安卓import的格式返回，不需要任何其他形式的文字解释**。
    请翻译以下函数:{code}。以下是关于函数的描述:{context}。
    '''
    prompt = PromptTemplate(
        template=template,
        input_variables=["code", "context"]
    )

    # Create a RunnableSequence with the prompt and llm
    chain = prompt | llm

    loader = JSONLoader(
        file_path=filepath,
        jq_schema='.[]',
        text_content=False,
        metadata_func=metadata_func
    )

    data = loader.load()

    res = []

    for doc in data:
        try:
            text_data = json.loads(doc.page_content)  # 将 page_content 解析为 JSON
            if "context" in text_data and "code" in text_data:
                try:
                    codeToTranslate = text_data["code"]
                    TranslatedCode = chain.invoke({"code": codeToTranslate,
                                                   "context": text_data["context"]})
                    if "wrong format" not in TranslatedCode:
                        tmp = {
                            "JavaCode": TranslatedCode,
                            "ArkTSCode": codeToTranslate
                        }
                        res.append(tmp)
                        print(TranslatedCode)
                        print("----------")
                except Exception as e:
                    print(f"Error occurred while translating: {e}")
            else:
                for item in text_data:

                    try:
                        codeToTranslate = item.get('content')
                        TranslatedCode = chain.invoke({"code": codeToTranslate,
                                                       "context": "无描述，请自行理解"})
                        if "wrong format" not in TranslatedCode:
                            tmp = {
                                "JavaCode": TranslatedCode,
                                "ArkTSCode": codeToTranslate
                            }
                            res.append(tmp)
                            print(TranslatedCode)
                            print("----------")
                    except Exception as e:
                        print(f"Error occurred while translating: {e}")
        except Exception as e2:
            print(f"Error processing item: {e2}")

    filePaths = filepath.split("/")

    storagePath = "./Harmony2JavaFunctionPairs2/" + filePaths[-1]

    # 将 res 存储到文件
    with open(storagePath, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


def get_filenames(directory):
    filenames = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filenames.append(file)
    return filenames


if __name__ == "__main__":
    # 遍历best_analysis_results下所有文件，获取文件名
    directory = './guide_analysis_results_02'
    filenames = get_filenames(directory)
    print(filenames)
    for file in filenames:
        filePath = directory + "/" + file
        print("Translating file: " + filePath)
        translate_code_from_file(filePath)
        print("--" * 10)

# 2378对函数
