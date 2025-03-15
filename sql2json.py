import os
import re
from pprint import pprint
import sqlparse
import json


def sql_to_json(sql, filename):
    parsed = sqlparse.parse(sql)
    result = []
    for statement in parsed:
        for token in statement.tokens:
            token_dict = {
                'value': str(token),
                'type': token.ttype.__str__()
            }
            if token_dict['type'] == 'None':
                result.append(token_dict)

    initialJsonData = json.dumps(result)
    jsonData = json.loads(initialJsonData)
    ColumnName = extract_columns(jsonData[0]['value'])

    ColumnValue = parse_values_clause(jsonData[1]['value'])

    jsonObject = dict(zip(ColumnName, ColumnValue))

    if ColumnName and ColumnValue:
        jsonObject["Path"] = os.path.splitext(filename)[0]

    return jsonObject


def extract_columns(sql):
    # Regular expression to match the content inside parentheses
    pattern = re.compile(r'\((.*?)\)')
    match = pattern.search(sql)
    if match:
        columns_str = match.group(1)
        # Split the columns by comma, considering possible spaces around commas
        columns = [col.strip() for col in columns_str.split(',')]
        return columns
    return []


def parse_values_clause(sql):
    """
    解析 SQL 中 VALUES 子句内的值，支持使用反引号 `...` 包围的字符串和 NULL 标识。
    示例输入:
      "VALUES (`OH_AVCapabilityFeature`, ``, `VIDEO_ENCODER_LONG_TERM_REFERENCE`, NULL, `编解码器支持长期参考帧特性，只用于视频编码场景。`)"
    返回:
      ['OH_AVCapabilityFeature', '', 'VIDEO_ENCODER_LONG_TERM_REFERENCE', None, '编解码器支持长期参考帧特性，只用于视频编码场景。']
    """
    # 提取VALUES括号内的内容
    m = re.search(r"VALUES\s*\((.*)\)", sql, re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError("输入 SQL 中没有找到 VALUES 子句。")

    content = m.group(1)

    # 定义正则：匹配以反引号包围的字符串或者 NULL，
    # 注意：这里的 (?i) 可用于不区分大小写，或者在编译时指定 re.IGNORECASE。
    pattern = r"""
        \s*                                   # 可选前置空白
        (?:                                   # 非捕获组，匹配以下两种之一
            `([^`]*)`                        # 捕获组1：反引号内的内容（即使为空）
            |                                # 或
            (NULL)                           # 捕获组2：NULL 字符串
        )
        \s*(?:,|$)                            # 后置空白和逗号或行尾
    """
    regex = re.compile(pattern, re.IGNORECASE | re.VERBOSE)
    results = []
    for match in regex.finditer(content):
        if match.group(1) is not None:
            # 匹配到反引号内的字符串
            results.append(match.group(1))
        elif match.group(2) is not None:
            # 匹配到 NULL（不区分大小写）
            results.append(None)
    return results


def read_sql_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        sql_content = file.read()

    # 使用 sqlparse 解析 SQL 文件内容
    statements = sqlparse.split(sql_content)
    return statements


if __name__ == '__main__':
    res = []
    # 示例SQL文件
    directory = "./harmony-references-V5-sql"
    res = []
    for filename in os.listdir(directory):
        if filename.endswith(".sql"):
            file_path = os.path.join(directory, filename)
            statements = read_sql_file(file_path)
            for statement in statements:
                res.append(sql_to_json(statement, filename))
    with open('NewOutput.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)

    # # 示例SQL语句
    # sql = '''
    # INSERT INTO HMFunctions (FunctionName, FunctionParameters, ReturnType, ReturnValue, FullFunctionName, RequiredPermissions, SystemCapability, ErrorCodes, Example, FunctionDescription) VALUES (`OH_AVCapability_AreProfileAndLevelSupported()`, `[{"param_name": "capability", "param_type": "编解码能力指针", "required": "true"}, {"param_name": "profile", "param_type": "编解码器档次", "required": "true"}, {"param_name": "level", "param_type": "编解码器级别", "required": "true"}]`, `bool `, `[]`, `bool OH_AVCapability_AreProfileAndLevelSupported (OH_AVCapability *capability, int32_t profile, int32_t level)`, `-`, ``, `[]`, NULL, `检查编解码器是否支持档次和级别的特定组合。`);
    # '''
    # sql_to_json(sql)
