###
# 原本用于检索知识库，但是后续检索结果出现较大偏差
# 已停用
###
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_milvus import Milvus
import numpy as np
from rank_bm25 import BM25Okapi

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]
MILVUS_TOKEN = os.environ["MILVUS_TOKEN"]


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
                 content_weight: float = 0.9,
                 description_weight: float = 0.05,
                 usage_weight: float = 0.05,
                 import_weight: float = 0.3,
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

    def retrieve(self, query: str, k: int = 10):
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



class BM25ReRankRetriever:
    def __init__(self, vectorstore, candidate_k=10, top_k=5,
                 content_weight=0.6, description_weight=0.2,
                 usage_weight=0.1, import_weight=0.1):
        self.vectorstore = vectorstore  # Milvus 实例
        self.candidate_k = candidate_k  # Milvus 候选数
        self.top_k = top_k              # 最终返回数
        self.content_weight = content_weight
        self.description_weight = description_weight
        self.usage_weight = usage_weight
        self.import_weight = import_weight

    def tokenize(self, text):
        # 简单英文分词；如为中文可替换为 jieba.lcut(text)
        return text.split()

    def retrieve(self, query: str):
        # 1. 候选召回（向量搜索）
        results = self.vectorstore.similarity_search_with_score(query, k=self.candidate_k)
        docs, _ = zip(*results)

        # 2. 构建 BM25 语料（四个字段）
        content_corpus = [self.tokenize(doc.page_content) for doc in docs]
        desc_corpus = [self.tokenize(doc.metadata.get("Description", "")) for doc in docs]
        usage_corpus = [self.tokenize(doc.metadata.get("Usage", "")) for doc in docs]
        import_corpus = [self.tokenize(doc.metadata.get("Import", "")) for doc in docs]

        bm25_content = BM25Okapi(content_corpus)
        bm25_desc = BM25Okapi(desc_corpus)
        bm25_usage = BM25Okapi(usage_corpus)
        bm25_import = BM25Okapi(import_corpus)

        # 3. 查询分词
        query_tokens = self.tokenize(query)

        # 4. 分字段打分
        scores_content = bm25_content.get_scores(query_tokens)
        scores_desc = bm25_desc.get_scores(query_tokens)
        scores_usage = bm25_usage.get_scores(query_tokens)
        scores_import = bm25_import.get_scores(query_tokens)

        # 5. 综合得分加权
        ranked = []
        for i in range(len(docs)):
            total_score = (self.content_weight * scores_content[i] +
                           self.description_weight * scores_desc[i] +
                           self.usage_weight * scores_usage[i] +
                           self.import_weight * scores_import[i])
            ranked.append((docs[i], total_score))

        # 6. 排序并返回
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked[:self.top_k]]



# 设置 DashScopeEmbeddings，确保提供有效的 API 密钥
embeddings = DashScopeEmbeddings(
    dashscope_api_key=DASHSCOPE_API_KEY  # 这里填入你的 API 密钥
)

# 创建 Milvus 连接，提供正确的 URI 和 Token
vector_db = Milvus(
    embedding_function=embeddings,
    collection_name='HarmonyReferences',
    connection_args={
        "host": "127.0.0.1",
        "port": "19530"
    }
)

# 定义查询
query = "Module name :@ohos.hilog (HiLog日志打印). The full name : warn"
# print(DASHSCOPE_API_KEY)
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
# 创建自定义检索器实例
retriever = CombinedEmbeddingRetriever(embedding_model=embeddings,vectorstore=vector_db)
results_combined = retriever.retrieve(query,k=5)
res = []
for i, doc in enumerate(results_combined):
    doc.metadata['Path'] = "https://developer.huawei.com/consumer/cn/doc/harmonyos-references-V5/" + doc.metadata[
        'Path']
    print(f"Top {i + 1}: {doc.page_content}")
    print("Metadata:", doc.metadata)
    # doc.metadata['Path'] = "https://developer.huawei.com/consumer/cn/doc/harmonyos-references-V5/"+doc.metadata['Path']
    print("-----")
