###
# 用于划分训练集与测试集
###
import json
import os
from sklearn.model_selection import train_test_split


def split_and_save_json(input_file, output_train_file, output_test_file, test_size=0.2, random_state=42):
    # 读取 JSON 文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 判断数据类型
    if isinstance(data, dict):
        items = list(data.items())
        train_items, test_items = train_test_split(items, test_size=test_size, random_state=random_state)
        train_data = dict(train_items)
        test_data = dict(test_items)
    elif isinstance(data, list):
        train_data, test_data = train_test_split(data, test_size=test_size, random_state=random_state)
    else:
        raise ValueError("Unsupported JSON data format. Expected a list or dict.")

    # 保存训练集和测试集为新的 JSON 文件
    with open(output_train_file, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, ensure_ascii=False, indent=4)

    with open(output_test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=4)


# 输入文件夹路径
input_folder = './FinetuningDataset'
output_folder = './split_dataset'

# 创建输出文件夹
os.makedirs(output_folder, exist_ok=True)

# 遍历文件夹中的所有 JSON 文件
for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        print(filename)
        input_file = os.path.join(input_folder, filename)
        output_train_file = os.path.join(output_folder, f'train_{filename}')
        output_test_file = os.path.join(output_folder, f'test_{filename}')

        # 调用函数进行划分和保存
        split_and_save_json(input_file, output_train_file, output_test_file)

print("数据集划分完成！")
