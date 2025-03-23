import os
from pprint import pprint

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import Milvus
import numpy as np
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
DASHSCOPE_API_KEY=os.environ["DASHSCOPE_API_KEY"]
MILVUS_TOKEN=os.environ["MILVUS_TOKEN"]

embeddings = DashScopeEmbeddings(
    dashscope_api_key=DASHSCOPE_API_KEY  # 这里填入你的 API 密钥
)

# 创建 Milvus 连接，提供正确的 URI 和 Token
vector_db = Milvus(
    embedding_function=embeddings,
    collection_name='functionPairs',
    connection_args={
        "uri": "https://in03-ea0930b1d68b504.serverless.gcp-us-west1.cloud.zilliz.com",  # 填入你的 Milvus 服务 URI
        "token": MILVUS_TOKEN,  # 填入你的 Milvus 服务 Token
        "secure": True  # 根据你的服务配置，确定是否需要使用 HTTPS
    }
)


def get_similar_code(query):
    res = vector_db.similarity_search(query, k=5)
    data = []
    for doc in res:
        tmp = {
            "Java": doc.page_content,
            "ArkTS": doc.metadata.get("TranslatedCode", "")
        }
        data.append(tmp)
    return data