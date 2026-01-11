
import requests
from ruamel.yaml import YAML

# 配置
SOURCE_URL = "https://github.com/liandu2024/little/blob/main/yaml/clash-fallback-all.yaml"
OUTPUT_FILE = "generated-clash.yaml"

def main():
    # 1. 下载原始 YAML
    response = requests.get(SOURCE_URL)
    if response.status_code != 200:
        print("下载失败")
        return
    
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(response.text)

    # 2. 修改逻辑 (示例)
    # 假设我们要修改所有的节点名称，或者过滤掉某些节点
    if 'proxies' in data:
        for proxy in data['proxies']:
            # 示例：在所有节点名后加后缀
            proxy['name'] = proxy['name'] + " - MyCustom"
            
            # 示例：修改特定属性
            if 'udp' not in proxy:
                proxy['udp'] = True

    # 3. 添加自定义节点
    new_node = {
        'name': 'My-Custom-Node',
        'type': 'ss',
        'server': '1.2.3.4',
        'port': 443,
        'cipher': 'aes-256-gcm',
        'password': 'password'
    }
    data['proxies'].append(new_node)
    
    # 4. 更新代理组 (proxy-groups)
    # 将新节点加入到某个组中
    if 'proxy-groups' in data:
        for group in data['proxy-groups']:
            if group['name'] == 'Proxy': # 假设组名是 Proxy
                group['proxies'].append('My-Custom-Node')

    # 5. 保存新文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    print(f"新文件 {OUTPUT_FILE} 已生成")

if __name__ == "__main__":
    main()
