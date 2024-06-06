import os
import configparser

def load_language_config(lang):
    """加载语言配置文件"""
    config = configparser.ConfigParser()
    config_file = os.path.join('Config', 'Language', f'messages_{lang}.cfg')
    if os.path.exists(config_file):
        config.read(config_file)
        return config['Messages']
    else:
        raise FileNotFoundError(f"语言文件 {config_file} 未找到。")

def get_messages(lang):
    """获取消息字典"""
    messages = load_language_config(lang)
    return messages
