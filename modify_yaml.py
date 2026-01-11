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
    for key in ['external-controller', 'external-ui', 'external-ui-name', 'external-ui-url', 'secret']:
        if key in data:
            del data[key]
# --- 1. 外部控制与 UI 配置 ---
    data['external-controller'] = '0.0.0.0:9091'
    data['external-ui'] = 'ui'
    data['external-ui-name'] = 'zashboard'
    data['external-ui-url'] = 'https://ghfast.top/https://github.com/Zephyruso/zashboard/archive/refs/heads/gh-pages.zip'
    data['secret'] = '123456'

    
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
    # 原文件里的代理组引用的是旧的 provider 名字，如果不改，代理组会失效
    if 'proxy-groups' in data:
        for group in data['proxy-groups']:
            # 如果该组使用了 'use' 关键字（引用 provider）
            if 'use' in group:
                # 将该组引用的 provider 全部替换为你的 'iplc'
                group['use'] = ['iplc']
            
            # 如果该组原本手动写了 proxies 列表，建议清空或保留
            # group['proxies'] = ['DIRECT'] # 示例：保留直连节点

    # --- 4. 保存文件 ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    print(f"成功生成新配置：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
