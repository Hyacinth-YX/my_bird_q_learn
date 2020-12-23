因mac系统配置问题，尝试将版本改成了python3.7，按照以下操作安装环境后能正常运行
    
    >>> conda create -n AI python=3.7
    >>> conda activate AI
    >>> pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=100 -r requirements.txt
    >>> python bot.py