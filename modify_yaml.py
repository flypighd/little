import requests
from ruamel.yaml import YAML
import sys

# 原始文件地址
SOURCE_URL = "https://raw.githubusercontent.com/flypighd/little/main/yaml/clash-fallback-all.yaml"
OUTPUT_FILE = "generated-clash.yaml"
# 你的机场订阅地址
MY_SUBSCRIPTION_URL = "这里填入你的机场订阅链接"

def main():
    response = requests.get(SOURCE_URL)
    if response.status_code != 200:
        print("下载失败")
        return

    yaml = YAML()
    yaml.preserve_quotes = True # 保留引号格式
    yaml.width = 4096 # 禁止自动折行，这样 URL 就不会断开了
    data = yaml.load(response.text)

    # --- 1. 修改 proxy-providers ---
    # 定义你想要的配置结构
    new_iplc_provider = {
        'url': MY_SUBSCRIPTION_URL,
        'type': 'http',
        'interval': 86400,
        'health-check': {
            'enable': True,
            'url': 'https://www.gstatic.com/generate_204',
            'interval': 300
        },
        'proxy': '直连',
   
    }

    # 重置并设置新的 provider
    data['proxy-providers'] = {
        'iplc': new_iplc_provider
    }
    # --- 强制重写并激活外部控制配置 ---
    # 先删除可能存在的旧配置（包括注释掉的），确保新配置生效
    ui_configs = [
        ('external-controller', '0.0.0.0:9091'),
        ('external-ui', 'ui'),
        ('external-ui-name', 'zashboard'),
        ('external-ui-url', 'https://ghfast.top/https://github.com/Zephyruso/zashboard/archive/refs/heads/gh-pages.zip'),
        ('secret', '123456')
    ]
   
      
    # 1. 尝试获取 external-controller 原本所在的索引位置
    try:
        keys_list = list(data.keys())
        if 'external-controller' in keys_list:
            target_index = keys_list.index('external-controller')
        else:
            target_index = 0
    except Exception:
        target_index = 0

    # 2. 先彻底删除这些 key（包括残留的旧注释），防止重复或位置混乱
    for item in ui_configs:
        key = item[0] # 取出 key，例如 'external-ui'
        if key in data:
            del data[key]
        if hasattr(data, 'ca') and key in data.ca.items:
            data.ca.items.pop(key, None)

    # 3. 按照索引位置依次插入新配置，确保它们排在一起且在正确位置
    for i, item in enumerate(ui_configs):
        key, value = item[0], item[1]
        data.insert(target_index + i, key, value)
    
    data['dns'] = {
        'enable': True,
        'listen': '0.0.0.0:7874',
        'ipv6': True,
        'enhanced-mode': 'fake-ip',
        'fake-ip-range': '198.20.0.1/16',
        'nameserver': ['223.5.5.5', '114.114.114.114'],
        'fake-ip-filter-mode': 'blacklist',
        'fake-ip-filter': [
            '+.lan', 
            '+.local', 
            'geosite:cn',
            '+.yingyi.me',
            '+.yingyi.men',
            '+.chdbits.xyz',
            '+.ptchdbits.co',
            'tracker.*'  # 脚本会自动处理引号
        ]
    }
    # --- 2. 插入直连规则到 Rules 部分 ---
    # 定义你要新增的直连规则
    new_direct_rules = [
        'DOMAIN-SUFFIX,yingyi.me,DIRECT',
        'DOMAIN-SUFFIX,yingyi.men,DIRECT',
        'DOMAIN-SUFFIX,chdbits.co,DIRECT',
        'DOMAIN-SUFFIX,chdbits.xyz,DIRECT',
        'DOMAIN-SUFFIX,ptchdbits.co,DIRECT',
        'DOMAIN-KEYWORD,tracker,DIRECT'
    ]

    if 'rules' in data:
        # 使用列表拼接：新规则在前，旧规则在后
        # 这样可以确保这些特定域名优先直连
        data['rules'] = new_direct_rules + list(data['rules'])
    # --- 3. 修改 proxy-groups (非常重要) ---

    # --- 3. 修改 proxy-groups (包含锚点清理) ---
    if 'proxy-groups' in data:
        # 1. 清理 default 锚点中的“英国-故转”
        if 'default' in data:
            d_proxies = data['default'].get('proxies', [])
            data['default']['proxies'] = [p for p in d_proxies if p != '英国-故转']

        # 2. 过滤掉所有包含“英国”字样的代理组定义
        data['proxy-groups'] = [
            group for group in data['proxy-groups'] 
            if "英国" not in group.get('name', '')
        ]
        
        # 3. 处理剩余组的引用关系
        for group in data['proxy-groups']:
            # 替换资源引用
            if 'use' in group:
                group['use'] = ['iplc']
            
            # 清理剩余组中可能存在的“英国-故转”列表项
            if 'proxies' in group:
                group['proxies'] = [p for p in group['proxies'] if p != '英国-故转']


    # --- 4. 保存文件 ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    print(f"成功生成新配置：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
