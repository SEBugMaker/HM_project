###
# 抽样
###
import os
import json
import random

def sample_total_from_json(folder_path, total_sample=200, seed=711, output_file="./sampled_total.json"):
    random.seed(seed)
    all_data = []

    # 遍历所有 json 文件，读取数据并合并
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        print(f"⚠️ 文件 {filename} 不是数组格式，已跳过")
            except Exception as e:
                print(f"⚠️ 文件 {filename} 读取失败：{e}")

    print(f"📊 总数据条数：{len(all_data)}")

    if len(all_data) < total_sample:
        print(f"⚠️ 总数据不足 {total_sample} 条，仅有 {len(all_data)} 条，全部输出")
        sampled = all_data
    else:
        sampled = random.sample(all_data, total_sample)

    # 输出结果
    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump(sampled, out_f, ensure_ascii=False, indent=2)

    print(f"✅ 已抽样 {len(sampled)} 条，保存为 {output_file}")

# 示例调用
sample_total_from_json("FinetuningDataset/Pair4", total_sample=200, seed=711)
