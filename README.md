因mac系统配置问题，使用python3.7，按照以下操作安装环境后能正常运行
    
    >>> conda create -n AI python=3.7
    >>> conda activate AI
    >>> pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=100 -r requirements.txt
    >>> python bot.py

该项目是q-learning的试验项目，最好的参数在log_c10中能够百轮内就到1800多分，但时间原因没有更多尝试。