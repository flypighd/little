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


     # --- 3. 修改 proxy-groups (清理英韩 & 强制排除“仅海外”) ---
    TARGET_COUNTRIES = ["英国", "韩国"]
    RE_KEYWORDS_TO_REMOVE = [
        r"英国|UK|United Kingdom|伦敦|英|London|🇬🇧",
        r"广韩|韩国|韓國|KR|首尔|春川|🇰🇷|Korea"
    ]

    if 'proxy-groups' in data:
        # 1. 清理 default 锚点引用
        if 'default' in data:
            d_proxies = data['default'].get('proxies', [])
            data['default']['proxies'] = [
                p for p in d_proxies 
                if not any(country in p for country in TARGET_COUNTRIES)
            ]

        # 2. 移除独立的英韩代理组
        data['proxy-groups'] = [
            group for group in data['proxy-groups'] 
            if not any(country in group.get('name', '') for country in TARGET_COUNTRIES)
        ]
        
        # 3. 遍历并修正所有组的 filter
        for group in data['proxy-groups']:
            if 'use' in group:
                group['use'] = ['iplc']
            
            # 清理嵌套引用
            if 'proxies' in group:
                group['proxies'] = [
                    p for p in group['proxies'] 
                    if not any(country in p for country in TARGET_COUNTRIES)
                ]

            # 核心：修改 filter 逻辑
            if 'filter' in group and isinstance(group['filter'], str):
                f_str = group['filter']
                
                # A. 先清理掉英韩正则关键词
                for kw in RE_KEYWORDS_TO_REMOVE:
                    f_str = f_str.replace(kw, "").replace("||", "|")
                
                # B. 注入“排除仅海外”的断言 (?!.*仅海外)
                # 如果原有正则以 (?=.* 开始，我们在其后插入否定断言
                if f_str.startswith("(?=.*"):
                    f_str = f_str.replace("(?=.*", "(?!(.*仅海外))(?=.*", 1)
                # 如果是“其他”组那种排除式正则 ^((?!(...)).)*$
                elif f_str.startswith("^((?!( "):
                    f_str = f_str.replace("(?!(", "(?!(仅海外|", 1)
                
                # C. 修正语法痕迹
                f_str = f_str.replace("|))", "))").replace("(|", "(").replace("||", "|")
                group['filter'] = f_str


    # --- 4. 保存文件 ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    print(f"成功生成新配置：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
