"""
   Copyright 2025 Timandes White

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import yaml
import os

def load_config(config_path='config.yaml'):
    """加载YAML配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} doesnot exist")
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config
