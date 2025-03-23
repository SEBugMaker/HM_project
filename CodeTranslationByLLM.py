import json
import os
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
            你是一名华为移动端开发专家，你使用的开发语言为ArkTS，现在你需要阅读以下安卓的Java函数，并将其翻译成ArkTS语言。
            生成结果时不需要进行额外解释，如果遇到可能涉及到非系统自带的类或者方法的调用，只需要保留调用。
            **最终结果有且仅需要按照一个函数的格式返回，不需要任何其他形式的文字解释，如果需要翻译的内容并非一个完整函数，仅返回null字符串**。
            请翻译以下函数：{code},下面是几个可以参考的Java函数翻译到ArkTS函数的例子:{related_code}
        '''
    prompt = PromptTemplate(
        template=template,
        input_variables=["code", "related_code", "filename"]
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
        text_data = json.loads(doc.page_content)  # 将 page_content 解析为 JSON
        for item in text_data:
            try:
                codeToTranslate = item
                relatedCode = searchSimilarCode.get_similar_code(codeToTranslate)
                TranslatedCode = chain.invoke({"code": codeToTranslate,
                                               "related_code": relatedCode})
                if TranslatedCode != "null":
                    tmp = {
                        "JavaCode": codeToTranslate,
                        "TranslatedCode": TranslatedCode,
                        "Language": "ArkTS"
                    }
                    res.append(tmp)
                    print(TranslatedCode)
                    print("----------")
            except Exception as e:
                print(f"Error processing item: {e}")

    filePaths = filepath.split("/")

    storagePath = "./TranslatedFunctions/" + filePaths[-1]

    # 将 res 存储到文件
    with open(storagePath, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    translate_code_from_file("./functions/android-chips.json")
