# -*- coding:utf-8 -*-
# __author__ = majing

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table, Boolean
from sqlalchemy.orm import relationship
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import FileColumn
from flask_appbuilder.models.decorators import renders
from ..common.util import CustomModel


script_task_asset = Table('script_task_asset', Model.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('task_id', Integer, ForeignKey('script_task.id')),
                                      Column('asset_id', Integer, ForeignKey('asset.id'))
)


class ScriptTask(CustomModel):
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, comment=u"任务的名字")
    assets = relationship('Asset', secondary=script_task_asset, backref='tasks')
    status = Column(Boolean, default=False, comment=u"任务是否执行结束")
    detail = Column(Text, comment=u"错误原因")
    asset_detail = Column(Text)
    asset_num = Column(Integer, default=0, comment=u"任务关联的主机个数")

    @renders('asset_detail')
    def asset_detail(self):
        return ','.join([asset.name for asset in self.assets])

    @renders('asset_num')
    def asset_num(self):
        return len(self.assets)


class Script(CustomModel):
    """
    shell 脚本
    """
    id = Column(Integer, primary_key=True)
    name = Column(String(60), unique=True, nullable=False, comment=u"脚本名字")
    creator = Column(String(60), nullable=False, comment=u"脚本的写作者")
    comment = Column(Text, comment=u"脚本描述")
    file_path = Column(FileColumn, nullable=False)
    category = Column(String(10), nullable=False, default='shell', comment=u"脚本类型")

    def __unicode__(self):
        return self.name


assoc_script_asset = Table('script_asset', Model.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('script_id', Integer, ForeignKey('script.id')),
                                      Column('asset_id', Integer, ForeignKey('asset.id'))
)

assoc_script_db = Table('script_dbmodel', Model.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('script_id', Integer, ForeignKey('script.id')),
                                      Column('db_id', Integer, ForeignKey('db_model.id'))
)


class Asset(CustomModel):
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False, unique=True, comment=u"主机名字")
    ip = Column(String(20), nullable=False, unique=True, comment=u"主机IP")
    username = Column(String(60), nullable=False, comment=u"用户名")
    password = Column(String(255), nullable=False, comment=u"用户密码")
    script = relationship('Script', secondary=assoc_script_asset, backref='assets')
    script_num = Column(Integer, default=0, comment=u"主机关联的脚本数")
    port = Column(Integer, default=22, comment=u"端口号")

    def __unicode__(self):
        return self.name

    @renders('script_num')
    def script_num(self):
        return len(self.script)


class DbModel(CustomModel):
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False, comment=u"名字")
    host = Column(String(100), nullable=False, comment=u"数据库地址")
    port = Column(Integer, nullable=False, comment=u"端口")
    db_name = Column(String(60), nullable=False, comment=u"数据库名字")
    db_user = Column(String(60), nullable=False, comment=u"数据库用户名")
    db_passwd = Column(String(255), nullable=False, comment=u"数据库密码")
    script = Column(FileColumn, comment=u"上传要执行的脚本")

