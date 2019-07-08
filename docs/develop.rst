# 开发文档

1. 使用框架flaskappbuilder
2. 使用ansible管理主机时，master主机要安装sshpass， 以支持ssh可以通过用户名密码的方式来连接远程主机，但这种方式不安全，后期要优化
3. 项目不要部署在虚环境中，sshpass可能会出问题，（本地开发在虚环境中，在虚环境中创键了一个sshpass的软连接）ansible有可能也会出现问题
4. 使用ansible的copy模块时，被管理的主机要安装libselinux-python包
5. 数据库版本管理工具alembic
   alembic revision  --autogenerate -m ""        #生成版本文件
    alembic upgrade head
6. 日志配置：app/__init__.py     logs/
7. 项目入口文件： run.py                 本地调试 启动服务：python run.py
8. jobs.py      添加定时任务 项目中使用flask-apscheduler执行定时任务       # 项目中暂时没有定时任务 可以不用考虑
9. app/__init__.py           日志配置，app初始化
10. 英文转中文： 把需要转换的字符串写到 app/translations/zh/LC_MESSAGES/messages.po  文件中    执行：fabmanager babel-compile
11. config.py   项目的配置文件    数据库配置，app配置
12. start.sh     项目启动脚本
13. gunicorn_conf.py          gunicorn的配置文件





# 项目目前需要优化的地方
1. 远程主机执行脚本是同步任务，后期可以优化为异步任务