###
# 统计数据量
###
import os
import re

from langchain_community.document_loaders import JSONLoader


def count_code_blocks(filename):
    # 读取文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # 使用正则表达式匹配所有的代码块
    code_block_pattern = re.compile(r'```.*?```', re.DOTALL)
    code_blocks = re.findall(code_block_pattern, content)

    return len(code_blocks)


def add_code_block_count_to_file(filename):
    # 读取原始文件内容
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

    # 统计代码块的数量
    code_block_count = count_code_blocks(filename)

    # 构造新的文件内容，插入代码块数量信息
    new_content = f"## 代码块数量: {code_block_count}\n\n" + content

    # 将修改后的内容写回文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(new_content)

    print(f"已将代码块数量 {code_block_count} 添加到文件开头")


def get_filenames(directory):
    filenames = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filenames.append(file)
    return filenames


def count_JSON_data_num(filepath):
    loader = JSONLoader(
        file_path=filepath,
        jq_schema='.[]',
        text_content=False
    )

    data = loader.load()
    return len(data)


def count_num_in_folder(folder):
    num = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".json"):
                num += count_JSON_data_num(file_path)
    return num


if __name__ == '__main__':
    print(count_num_in_folder("FinetuningDataset/Pair4"))
