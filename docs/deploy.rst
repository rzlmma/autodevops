# 部署文档
1. python: 2.7              项目中使用了ansible，ansible对python3支持不太好，有很多问题
2. 项目不要部署在python的虚环境中，项目要用到sshpass，这个包只能安装到系统环境中
3. 在项目文件夹下找到requirements.txt
   pip install -r requirements.txt
4. 初始化admin用户
   cd /Prophet/prophet
   fabmanager create-admin
   一路回车，记下用户名，填入密码
5. 执行数据库更新脚本
   alembic upgrade head
6. 启动项目
    bash start.sh
7. 用supervisor管理进程