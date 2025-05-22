# 获取相似代码
# get_similar_code  -> use java search similar code
# get_similar_code2 -> use arkts search similar code
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

vector_db2 = Milvus(
    embedding_function=embeddings,
    collection_name='functionPairs2',
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

def get_similar_code2(query):
    res = vector_db2.similarity_search(query, k=3)
    data = []
    for doc in res:
        tmp = {
            "ArkTS": doc.page_content,
            "Java": doc.metadata.get("TranslatedCode", "")
        }
        data.append(tmp)
    return data


if __name__ == "__main__":
    pprint(get_similar_code(
        '''
        import android.hardware.Sensor;\nimport android.hardware.SensorEvent;\nimport android.hardware.SensorEventListener;\nimport android.hardware.SensorManager;\nimport android.content.Context;\nimport java.util.concurrent.CompletableFuture;\n\npublic class GravitySensorManager implements SensorEventListener {\n\n    private final SensorManager sensorManager;\n    private final Sensor gravitySensor;\n    private final Sensor accelerometerSensor;\n    private boolean isSupported = false;\n\n    public GravitySensorManager(Context context) {\n        sensorManager = (SensorManager) context.getSystemService(Context.SENSOR_SERVICE);\n        gravitySensor = sensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY);\n        accelerometerSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);\n    }\n\n    public double getRealData(SensorEvent event) {\n        float x = event.values[0];\n        float y = event.values[1];\n        float z = event.values[2];\n\n        if (((x * x + y * y) * 3) < (z * z)) {\n            return 0;\n        } else {\n            double sd = Math.atan2(y, -x);\n            double sc = Math.round(sd / 3.141592653589 * 180);\n            double getDeviceDegree = 90 - sc;\n            getDeviceDegree = getDeviceDegree >= 0 ? getDeviceDegree % 360 : getDeviceDegree % 360 + 360;\n            return getDeviceDegree;\n        }\n    }\n\n    public CompletableFuture<Double> getGravity() {\n        if (gravitySensor != null) {\n            isSupported = true;\n        }\n\n        CompletableFuture<Double> future = new CompletableFuture<>();\n        if (isSupported && gravitySensor != null) {\n            sensorManager.registerListener(this, gravitySensor, SensorManager.SENSOR_DELAY_NORMAL);\n        } else if (accelerometerSensor != null) {\n            sensorManager.registerListener(this, accelerometerSensor, SensorManager.SENSOR_DELAY_NORMAL);\n        } else {\n            future.completeExceptionally(new UnsupportedOperationException(\"Gravity or Accelerometer sensor not supported\"));\n        }\n\n        return future;\n    }\n\n    @Override\n    public void onSensorChanged(SensorEvent event) {\n        if (event.sensor.getType() == Sensor.TYPE_GRAVITY || event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {\n            double result = getRealData(event);\n            sensorManager.unregisterListener(this);\n            ((CompletableFuture<Double>) getGravity()).complete(result);\n        }\n    }\n\n    @Override\n    public void onAccuracyChanged(Sensor sensor, int accuracy) {\n        // Not used\n    }\n}
        '''
    ))