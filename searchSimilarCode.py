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
        "host":"127.0.0.1",
        "port":"19530"
    }
)


def get_similar_code(query):
    res = vector_db.similarity_search(query, k=3)
    data = []
    for doc in res:
        tmp = {
            "Java": doc.page_content,
            "ArkTS": doc.metadata.get("TranslatedCode", "")
        }
        data.append(tmp)
    return data