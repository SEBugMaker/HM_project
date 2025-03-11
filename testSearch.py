from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import Milvus
from sqlalchemy.testing.suite.test_reflection import metadata

# 设置 DashScopeEmbeddings，确保提供有效的 API 密钥
embeddings = DashScopeEmbeddings(
    dashscope_api_key='sk-f0906d78e9284119a711c29e127f9788'  # 这里填入你的 API 密钥
)

# 创建 Milvus 连接，提供正确的 URI 和 Token
vector_db = Milvus(
    embedding_function=embeddings,
    collection_name='HarmonyReferences',
    connection_args={
        "uri": "https://in03-ea0930b1d68b504.serverless.gcp-us-west1.cloud.zilliz.com",  # 填入你的 Milvus 服务 URI
        "token": "13d4fb4e41587949aa55472de51cd6161deda8b0e694eff69fc6cc9165bf897a8609ed8d572bc57a10b4c12f33288079d1e725f3",  # 填入你的 Milvus 服务 Token
        "secure": True  # 根据你的服务配置，确定是否需要使用 HTTPS
    }
)

# 定义查询
query = "UIExtensionAbility .onForeground()"

# 执行相似性搜索
docs = vector_db.similarity_search(query, k=20)  # k=5 可以返回前5个最相关的文档

# 打印搜索结果
for doc in docs:
    print(doc)

