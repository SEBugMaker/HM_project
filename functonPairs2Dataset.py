import json
import logging
import os
from pprint import pprint

from langchain_community.document_loaders import JSONLoader

from dotenv import find_dotenv, load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Milvus

load_dotenv(find_dotenv())
DASHSCOPE_API_KEY=os.environ["DASHSCOPE_API_KEY"]
MILVUS_TOKEN=os.environ["MILVUS_TOKEN"]

# 定义元数据提取函数。
def metadata_func(record: dict, metadata: dict) -> dict:
    if "source" in metadata:
        del metadata["source"]
    if "TranslatedCode" in record:
        metadata["TranslatedCode"] = record["TranslatedCode"]
    if "Language" in record:
        metadata["Language"] = record["Language"]
    return metadata

loader = JSONLoader(
    file_path='./function_pairs/merged_function_pairs.json',
    jq_schema='.[]',
    text_content=False,
    metadata_func=metadata_func
)
data = loader.load()

for doc in data:
    text_data = json.loads(doc.page_content)  # 将 page_content 解析为 JSON
    doc.page_content = text_data["JavaCode"]

print(len(data))

embeddings = DashScopeEmbeddings(

    dashscope_api_key=DASHSCOPE_API_KEY
)
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 分批上传数据，每批20个
batch_size = 1
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    try:
        vector_db = Milvus.from_documents(
            batch,
            embeddings,
            collection_name='functionPairs',
            connection_args={
                "uri": "https://in03-ea0930b1d68b504.serverless.gcp-us-west1.cloud.zilliz.com",
                "token": MILVUS_TOKEN,
                "secure": True
            }
        )
        logging.info(f"Successfully uploaded batch {i // batch_size + 1} of {len(data) // batch_size + 1}")
    except Exception as e:

        logging.error(f"Error uploading batch {i // batch_size + 1}: {e}")

