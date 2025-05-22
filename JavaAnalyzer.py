###
# 分析import
###
import os
import javalang


def get_base_type(type_node):
    """解析类型节点的基础类型"""
    if isinstance(type_node, javalang.tree.ReferenceType):
        return type_node.name
    return None


def find_android_imports(tree):
    imports = {}
    for imp in tree.imports:
        if is_android_api(imp.path):
            class_name = imp.path.split('.')[-1]
            imports[class_name] = imp.path
    return imports


def build_variable_mapping(tree, imports):
    variable_map = {}

    # 处理字段声明
    for _, node in tree.filter(javalang.tree.FieldDeclaration):
        base_type = get_base_type(node.type)
        if not base_type:
            continue

        full_class = resolve_qualified_name(base_type, imports)
        if not is_android_api(full_class):
            continue

        for declarator in node.declarators:
            variable_map[declarator.name] = full_class

    # 处理局部变量声明
    for _, node in tree.filter(javalang.tree.LocalVariableDeclaration):
        base_type = get_base_type(node.type)
        if not base_type:
            continue

        full_class = resolve_qualified_name(base_type, imports)
        if not is_android_api(full_class):
            continue

        for declarator in node.declarators:
            variable_map[declarator.name] = full_class

    # 处理函数参数声明
    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        for param in node.parameters:
            base_type = get_base_type(param.type)
            if not base_type:
                continue

            full_class = resolve_qualified_name(base_type, imports)
            if not is_android_api(full_class):
                continue

            variable_map[param.name] = full_class

    return variable_map


def find_android_method_calls(file_path):
    with open(file_path, 'r') as f:
        code = f.read()

    try:
        tree = javalang.parse.parse(code)
    except javalang.parser.JavaSyntaxError:
        return []

    imports = find_android_imports(tree)
    variable_map = build_variable_mapping(tree, imports)
    results = []

    for _, node in tree.filter(javalang.tree.MethodInvocation):
        qualifier = node.qualifier
        method_name = node.member
        line = node.position.line if node.position else 0

        # 解析类名
        class_name = None
        if qualifier:
            # 优先检查变量映射
            if qualifier in variable_map:
                class_name = variable_map[qualifier]
            else:
                # 尝试解析为直接类名
                class_name = resolve_qualified_name(qualifier, imports)

        if class_name and is_android_api(class_name):
            results.append({
                "class": class_name,
                "method": method_name,
                "line": line,
                "file": file_path
            })

    return results


def resolve_qualified_name(qualifier, imports):
    return imports.get(qualifier, qualifier)


def is_android_api(class_name: str) -> bool:
    return class_name.startswith(('android.', 'androidx.'))
    # return True

def traverse_android_project(root_path):
    all_results = []
    for subdir, _, files in os.walk(root_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(subdir, file)
                results = find_android_method_calls(file_path)
                all_results.extend(results)
    return all_results

if __name__ == '__main__':
    # todo: implements 解析

    project_path = './test.java'
    # results = traverse_android_project(project_path)
    # for r in results:
    #     relative_path = os.path.relpath(r['file'], project_path)
    #     print(f"Class: {r['class']}, Method: {r['method']}, Line: {r['line']}, File: {relative_path}")

    # project_path = '/Users/daniel/Desktop/Projects/HMDataAugmentation/JavaAnalyzer/ActivityLifecycleManager.java'
    res = find_android_method_calls(project_path)
    for r in res:
        print(r)
