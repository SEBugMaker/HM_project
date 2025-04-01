import json
import logging
from pprint import pprint
import os
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Milvus
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveJsonSplitter
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
DASHSCOPE_API_KEY=os.environ["DASHSCOPE_API_KEY"]
MILVUS_TOKEN=os.environ["MILVUS_TOKEN"]


# 定义元数据提取函数。
def metadata_func(record: dict, metadata: dict) -> dict:
    # print(record)

    if "source" in metadata:
        del metadata["source"]

    if "Path" in record:
        metadata["Path"] = record["Path"]

    return metadata


loader = JSONLoader(
    file_path='NewOutput.json',
    jq_schema='.[]',
    text_content=False,
    metadata_func=metadata_func
)
data = loader.load()

# 识别 data 中有几种格式的 JSON
# formats = set()
# for doc in data:
#     if doc.page_content:
#         try:
#             text_data = json.loads(doc.page_content)
#             formats.add(frozenset(text_data.keys()))
#         except json.JSONDecodeError as e:
#             print(f"解析 JSON 时出错: {e}")
#
# print(len(formats))

# format有以下几种
# frozenset({'FunctionName', 'ModuleName', 'Version', 'SystemCapability', 'ModuleConstraint', 'Tables', 'ImportModule', 'ModuleVersion', 'FullName', 'MetaAPI', 'ModuleDescription', 'FunctionDescription'}),
# frozenset({'FunctionName', 'ReturnValue', 'RequiredPermissions', 'ErrorCodes', 'ReturnType', 'FullFunctionName', 'SystemCapability', 'FunctionDescription', 'Example', 'FunctionParameters'}),
# frozenset({'Events', 'Description', 'ComponentName', 'Examples', 'Parameters', 'Attributes', 'Interfaces', 'SystemCapabilities', 'SubComponents'}),
# frozenset({'EnumValue', 'Description', 'EnumName', 'EnumValueName', 'SystemCapability'}),
# frozenset({'Module', 'Title', 'Content'}),
# frozenset({'ErrorCode', 'HandlingSteps', 'ErrorDescription', 'ErrorInfo', 'PossibleCauses'}),
# frozenset({'Description', 'TypeCategory', 'TypeName'})
# format有以下几种
formats_list = [
    frozenset(
        {'FunctionName', 'ModuleName', 'Version', 'SystemCapability', 'ModuleConstraint', 'Tables', 'ImportModule',
         'ModuleVersion', 'FullName', 'MetaAPI', 'ModuleDescription', 'FunctionDescription','Path'}),
    frozenset({'FunctionName', 'ReturnValue', 'RequiredPermissions', 'ErrorCodes', 'ReturnType', 'FullFunctionName',
               'SystemCapability', 'FunctionDescription', 'Example', 'FunctionParameters','Path'}),
    frozenset({'Events', 'Description', 'ComponentName', 'Examples', 'Parameters', 'Attributes', 'Interfaces',
               'SystemCapabilities', 'SubComponents','Path'}),
    frozenset({'EnumValue', 'Description', 'EnumName', 'EnumValueName', 'SystemCapability','Path'}),
    frozenset({'Module', 'Title', 'Content','Path'}),
    frozenset({'ErrorCode', 'HandlingSteps', 'ErrorDescription', 'ErrorInfo', 'PossibleCauses','Path'}),
    frozenset({'Description', 'TypeCategory', 'TypeName','Path'})
]

for doc in data:
    if doc.page_content == '':
        data.remove(doc)

# 筛选掉无法解析的数据
toRemoved = []
for doc in data:
    try:
        text_data = json.loads(doc.page_content)
    except json.JSONDecodeError as e:
        # print(f"解析 JSON 时出错: {e}")
        toRemoved.append(doc)

for doc in toRemoved:
    data.remove(doc)

# Update page_content to only retain the 'problem' part
for doc in data:
    try:
        text_data = json.loads(doc.page_content)  # 将 page_content 解析为 JSON

        # 判断属于哪一种format
        doc_format = frozenset(text_data.keys())

        if doc_format in formats_list:
            format_index = formats_list.index(doc_format)

            if format_index == 0:
                # frozenset({'FunctionName', 'ModuleName', 'Version', 'SystemCapability', 'ModuleConstraint', 'Tables', 'ImportModule', 'ModuleVersion', 'FullName', 'MetaAPI', 'ModuleDescription', 'FunctionDescription'}),
                # example :
                # {
                #         "ModuleName": "@ohos.util.Vector (线性容器Vector)",1
                #         "ModuleDescription": "",1
                #         "ModuleVersion": "",0
                #         "ImportModule": "import { Vector } from '@kit.ArkTS';",1
                #         "FunctionName": "",1
                #         "FullName": "Vector",1
                #         "FunctionDescription": "",1
                #         "ModuleConstraint": "",1
                #         "MetaAPI": "",
                #         "SystemCapability": "",1
                #         "Version": "",
                #         "Tables": ""
                #     },
                if text_data['FunctionName'] != "":
                    doc.page_content = (
                            'Function ' + text_data['FunctionName'] +
                            ' from module ' + text_data['ModuleName'] +
                            '. Full name of the function is ' + text_data['FullName']
                    )
                else:
                    doc.page_content = (
                            'Module name :' + text_data['ModuleName'] +
                            '. The full name : ' + text_data['FullName']
                    )

                doc.metadata.update({'Import': text_data['ImportModule']})

                doc.metadata.update({'SystemCapability': text_data['SystemCapability']})

                doc.metadata.update({'Constraint': text_data['ModuleConstraint']})

                if text_data['FunctionName'] == "":
                    doc.metadata.update({'Description': text_data['ModuleDescription']})
                else:
                    doc.metadata.update({'Description': text_data['FunctionDescription']})

                doc.metadata.update({'Usage': ("The usage of this function is: " + text_data['FunctionName'])})

            elif format_index == 1:
                # frozenset({'FunctionName', 'ReturnValue', 'RequiredPermissions', 'ErrorCodes', 'ReturnType', 'FullFunctionName', 'SystemCapability', 'FunctionDescription', 'Example', 'FunctionParameters'}),
                # example :
                # {
                #         "FunctionName": "OH_Ability_CreateNativeChildProcess",1
                #         "FunctionParameters": "[]",1
                #         "ReturnType": "int ",1
                #         "ReturnValue": "[]",
                #         "FullFunctionName": "int OH_Ability_CreateNativeChildProcess (const char *libName, OH_Ability_OnNativeChildProcessStarted onProcessStarted )",1
                #         "RequiredPermissions": "-",
                #         "SystemCapability": "",1
                #         "ErrorCodes": "[]",
                #         "Example": null,
                #         "FunctionDescription": ""1
                #     }
                doc.page_content = (
                        'Function name is ' + text_data['FunctionName']
                )

                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': text_data['SystemCapability']})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Description': (
                        'The function description : ' + text_data['FunctionDescription'] +
                        '. The full function name : ' + text_data['FullFunctionName']
                )})

                doc.metadata.update({'Usage': (
                        '. The return type is: ' + text_data['ReturnType'] +
                        '. The parameters are: ' + text_data['FunctionParameters'])}
                )
            elif format_index == 2:
                # frozenset({'Events', 'Description', 'ComponentName', 'Examples', 'Parameters', 'Attributes', 'Interfaces', 'SystemCapabilities', 'SubComponents'}),
                # example :
                # {
                #         1"ComponentName": "polyline",
                #         1"SubComponents": "子组件支持animate、animateMotion、animateTransform。 ",
                #         1"Attributes": "",
                #         1"Interfaces": "",
                #         1"SystemCapabilities": "",
                #         1"Parameters": "",
                #         "Events": "",
                #         1"Examples": "[]",
                #         1"Description": "该组件从API version 7开始支持。后续版本如有新增内容，则采用上角标单独标记该内容的起始版本。"
                #     },
                doc.page_content = (
                        'Component name is ' + text_data['ComponentName']
                )
                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': text_data['SystemCapabilities']})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Description': (
                        'The sub components description: ' + text_data['SubComponents'] +
                        '. The description is: ' + text_data['Description']
                )})

                doc.metadata.update({'Usage': (
                        'The example usage is: ' + text_data['Examples'] +
                        '. The parameters are: ' + text_data['Parameters'] +
                        '. The knowledge you may need is: ' + text_data['Attributes'] + ' and ' +
                        text_data['Interfaces'])}
                )
            elif format_index == 3:
                # frozenset({'EnumValue', 'Description', 'EnumName', 'EnumValueName', 'SystemCapability'}),
                # example :
                # {
                #         "EnumName": "EventType",
                #         "SystemCapability": "",
                #         "EnumValueName": "FAULT",
                #         "EnumValue": "1",
                #         "Description": "事件类型。"
                #     }
                doc.page_content = (
                        'Enum name is ' + text_data['EnumName']
                )

                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': text_data['SystemCapability']})

                doc.metadata.update({'Description': (
                        'The enum description is: ' + text_data['Description']
                )})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Usage': (
                        'The enum value ' + text_data['EnumValueName'] +
                        ' means ' + text_data['EnumValueName'])}
                )
            elif format_index == 4:
                # frozenset({'Module', 'Title', 'Content'}),
                #    {
                #         "Title": "CommonEventPublishData",
                #         "Module": "属性",
                #         "Content": "包含公共事件内容和属性。   本模块首批接口从API version 7开始支持。后续版本的新增接口，采用上角标单独标记接口的起始版本。 如果不加限制，任何应用都可以订阅公共事件并读取相关信息，应避免在公共事件中携带敏感信息。通过本模块的subscriberPermissions和bundleName参数，可以限制公共事件接收方的范围。  属性系统能力： 以下各项对应的系统能力均为SystemCapability.Notification.CommonEvent    []"
                #     }
                doc.page_content = ('Module name is ' + text_data['Title'])

                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': 'none'})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Description': (
                        'The module content is: ' + text_data['Content']
                )})

                doc.metadata.update({'Usage': (
                        'The module type is: ' + text_data['Module']
                )})

            elif format_index == 5:
                # frozenset({'ErrorCode', 'HandlingSteps', 'ErrorDescription', 'ErrorInfo', 'PossibleCauses'}),
                # example :
                #    {
                #         "ErrorCode": "1010710001 图片尺寸不符合要求",
                #         "ErrorInfo": "The size of the pixelmap exceeds the limit.",
                #         "ErrorDescription": "调用添加图标等接口时，传入的图标图片尺寸不符合要求。",
                #         "PossibleCauses": "[]",
                #         "HandlingSteps": "[]"
                #     },
                doc.page_content = (
                        'Error code is ' + text_data['ErrorCode']
                )

                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': 'none'})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Description': (
                        'The error description is: ' + text_data['ErrorDescription'] +
                        'The error info is: ' + text_data['ErrorInfo']
                )})

                doc.metadata.update({'Usage': (
                        '. The possible causes are: ' + text_data['PossibleCauses'] +
                        '. The handling steps are: ' + text_data['HandlingSteps']
                )})

            elif format_index == 6:
                # frozenset({'Description', 'TypeCategory', 'TypeName'})
                # example :
                # {
                #         "TypeName": "typedef struct OH_CryptoKeyPair OH_CryptoKeyPair",
                #         "TypeCategory": "struct",
                #         "Description": "定义密钥对结构体。"
                #     }
                doc.page_content = (
                        'Type name is ' + text_data['TypeName']
                )

                doc.metadata.update({'Import': 'none'})

                doc.metadata.update({'SystemCapability': 'none'})

                doc.metadata.update({'Constraint': 'none'})

                doc.metadata.update({'Description': (
                        'The type description is: ' + text_data['Description']
                )})

                doc.metadata.update({'Usage': ('The type category is: ' + text_data['TypeCategory'])})
        else:
            print("Unknown format")
    except json.JSONDecodeError as e:
        # print(f"解析 JSON 时出错: {e}")
        data.remove(doc)



# 检测是否存在数据的metadata不含Import SystemCapability Constraint Description Usage
for doc in data:
    if ('Import' not in doc.metadata
            or 'SystemCapability' not in doc.metadata
            or 'Description' not in doc.metadata
            or 'Constraint' not in doc.metadata
            or 'Usage' not in doc.metadata
    ):
        print(doc)

# 对data进行splitter
splitter = RecursiveJsonSplitter(max_chunk_size=400)

splitterData = []

for doc in data:
    split_doc = splitter.split_json(json_data=dict(doc))
    # 删除 'id' 和 'type' 字段
    for part in split_doc:
        part.pop('id', None)
        part.pop('type', None)
        # 将原始文档的 metadata 复制到分割后的每个文档中
        part['metadata'] = doc.metadata
    splitterData.append(split_doc)

documents = []

for split_docs in splitterData:
    pageContent = ""
    metaData = {}
    for doc_dict in split_docs:
        if 'page_content' in doc_dict:
            pageContent = doc_dict['page_content']
        if 'metadata' in doc_dict:
            metaData = doc_dict['metadata']
    doc = Document(page_content=pageContent, metadata=metaData)
    documents.append(doc)
pprint(documents[0])


# 检测是否存在数据的metadata不含Import SystemCapability Constraint Description Usage
for doc in documents:
    if ('Import' not in doc.metadata
            or 'SystemCapability' not in doc.metadata
            or 'Description' not in doc.metadata
            or 'Constraint' not in doc.metadata
            or 'Usage' not in doc.metadata
    ):
        pprint(doc)

embeddings = DashScopeEmbeddings(

    dashscope_api_key=DASHSCOPE_API_KEY
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 分批上传数据，每批20个
batch_size = 50
for i in range(0, len(data), batch_size):
    batch = documents[i:i + batch_size]
    try:
        vector_db = Milvus.from_documents(
            batch,
            embeddings,
            collection_name='HarmonyReferences',
            connection_args={
                "uri": "https://in03-ea0930b1d68b504.serverless.gcp-us-west1.cloud.zilliz.com",
                "token": MILVUS_TOKEN,
                "secure": True
            }
        )
        logging.info(f"Successfully uploaded batch {i // batch_size + 1} of {len(data) // batch_size + 1}")
    except Exception as e:

        logging.error(f"Error uploading batch {i // batch_size + 1}: {e}")
