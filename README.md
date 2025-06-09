# 代码翻译任务数据构造

## 前期准备

- 运行[ReferenceJSON2DB.py](ReferenceJSON2DB.py)，将[知识库](https://box.nju.edu.cn/f/bb1b5980a9d54bc888b3/?dl=1)（请先下载）转为向量数据库。
- 运行[functonPairs2DB.py](functonPairs2DB.py)和[functionPairs2DB2.py](functionPairs2DB2.py)，将相似代码转为向量数据库，**其中的file_path需要自行修改**。
- API映射表 - [results.csv](https://box.nju.edu.cn/f/6401e6e5e2a04172a4a6/)（请先下载）

## ArkTS -> Java

代码文件：[ArkTS2Java.py](ArkTS2Java.py)

说明：

- TransArkTSFunction函数 -> 翻译单个函数
- 如需按照JSON文件来批量翻译，可在TransJSON函数中自行定义


## Java -> ArkTS

### 第一轮

代码文件：[Java2Harmony.py](Java2Harmony.py)

说明：

- 直接运行，批量翻译整个json文件，可以根据不同json格式自行修改

### 第二轮

代码文件：[Java2ArkTSPlusAPI.py](Java2ArkTSPlusAPI.py)

说明：

- 直接运行，批量翻译整个json文件，可以根据不同json格式自行修改
