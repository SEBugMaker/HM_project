from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import Milvus
import numpy as np
from sqlalchemy.testing.suite.test_reflection import metadata

# --- 策略一：仅基于 page_content 的向量相似度检索 ---
class BasicVectorRetriever:
    def __init__(self, vectorstore, embedding_model):
        self.vectorstore = vectorstore
        self.embedding_model = embedding_model

    def retrieve(self, query: str, k: int = 10):
        return self.vectorstore.similarity_search(query, k=k)

# --- 策略二：在基础向量检索结果上，根据 metadata 字段关键词加权重排序 ---
class MetadataBoostRetriever:
    def __init__(self, vectorstore, embedding_model, boost_weight: float = 0.1):
        self.vectorstore = vectorstore
        self.embedding_model = embedding_model
        self.boost_weight = boost_weight

    def retrieve(self, query: str, k: int = 10, candidate_k: int = 30):
        # 使用 similarity_search_with_score 获取候选结果（返回 (doc, score)）
        candidates = self.vectorstore.similarity_search_with_score(query, k=candidate_k)
        query_lower = query.lower()
        ranked = []
        for doc, base_score in candidates:
            boost = 0
            # 对 Description 与 Usage 字段进行简单关键词匹配加权
            for key in ['Description', 'Usage']:
                if key in doc.metadata and query_lower in doc.metadata[key].lower():
                    boost += self.boost_weight
            new_score = base_score + boost
            ranked.append((doc, new_score))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked][:k]

# --- 策略三：结合 page_content 与 metadata 的嵌入相似度综合排序 ---
class CombinedEmbeddingRetriever:
    def __init__(self, vectorstore, embedding_model,
                 content_weight: float = 0.55,
                 description_weight: float = 0.1,
                 usage_weight: float = 0.15,
                 import_weight: float = 0.2,
                 candidate_k: int = 10):
        """
        :param vectorstore: Milvus 向量数据库对象
        :param embedding_model: 用于计算文本嵌入的模型
        :param content_weight: page_content 的相似度权重
        :param description_weight: metadata 中 Description 的相似度权重
        :param usage_weight: metadata 中 Usage 的相似度权重
        :param import_weight: metadata 中 Import 字段的相似度权重
        :param candidate_k: 初步候选文档数
        """
        self.vectorstore = vectorstore
        self.embedding_model = embedding_model
        self.content_weight = content_weight
        self.description_weight = description_weight
        self.usage_weight = usage_weight
        self.import_weight = import_weight
        self.candidate_k = candidate_k

    def cosine_similarity(self, vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-10)

    def retrieve(self, query: str, k: int = 3):
        # 计算查询嵌入向量
        query_embedding = np.array(self.embedding_model.embed_query(query))
        # 利用 Milvus 获取候选文档
        candidates = self.vectorstore.similarity_search_with_score(query, k=self.candidate_k)
        ranked = []
        for doc, base_score in candidates:
            # 计算 page_content 的相似度
            content_embedding = np.array(self.embedding_model.embed_query(doc.page_content))
            content_sim = self.cosine_similarity(query_embedding, content_embedding)
            # 计算 metadata 中 Description 的相似度（如果存在）
            desc_sim = 0
            if 'Description' in doc.metadata:
                desc_embedding = np.array(self.embedding_model.embed_query(doc.metadata['Description']))
                desc_sim = self.cosine_similarity(query_embedding, desc_embedding)
            # 计算 metadata 中 Usage 的相似度（如果存在）
            usage_sim = 0
            if 'Usage' in doc.metadata:
                usage_embedding = np.array(self.embedding_model.embed_query(doc.metadata['Usage']))
                usage_sim = self.cosine_similarity(query_embedding, usage_embedding)
            # 计算 metadata 中 Import 的相似度（如果存在）
            import_sim = 0
            if 'Import' in doc.metadata:
                import_embedding = np.array(self.embedding_model.embed_query(doc.metadata['Import']))
                import_sim = self.cosine_similarity(query_embedding, import_embedding)
            # 综合得分
            combined_score = (self.content_weight * content_sim +
                              self.description_weight * desc_sim +
                              self.usage_weight * usage_sim +
                              self.import_weight * import_sim)
            ranked.append((doc, combined_score))
        # 按综合得分降序排序
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked][:k]


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
query = "Vector.tostring()"

# print("=== BasicVectorRetriever 结果 ===")
# basic_retriever = BasicVectorRetriever(vector_db, embeddings)
# results_basic = basic_retriever.retrieve(query, k=10)
# for i, doc in enumerate(results_basic):
#     print(f"Top {i+1}: {doc.page_content}")
#     print("Metadata:", doc.metadata)
#     print("-----")
#
# print("\n=== MetadataBoostRetriever 结果 ===")
# boost_retriever = MetadataBoostRetriever(vector_db, embeddings, boost_weight=0.1)
# results_boost = boost_retriever.retrieve(query, k=10)
# for i, doc in enumerate(results_boost):
#     print(f"Top {i+1}: {doc.page_content}")
#     print("Metadata:", doc.metadata)
#     print("-----")

print("\n=== CombinedEmbeddingRetriever 结果 ===")
combined_retriever = CombinedEmbeddingRetriever(vector_db, embeddings)
results_combined = combined_retriever.retrieve(query, k=10)
res = []
for i, doc in enumerate(results_combined):
    doc.metadata['Path'] = "https://developer.huawei.com/consumer/cn/doc/harmonyos-references-V5/" + doc.metadata['Path']
    print(f"Top {i+1}: {doc.page_content}")
    print("Metadata:", doc.metadata)
    # doc.metadata['Path'] = "https://developer.huawei.com/consumer/cn/doc/harmonyos-references-V5/"+doc.metadata['Path']
    print("-----")

