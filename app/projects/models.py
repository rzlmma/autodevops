# -*- coding:utf-8 -*-
# __author__ = majing
import datetime
from flask import Markup, url_for

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table, Boolean, DateTime
from sqlalchemy.orm import relationship
from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders

from ..common.util import CustomModel


project_asset = Table('project_asset', Model.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('project_id', Integer, ForeignKey('pub_item.id')),
                                      Column('asset_id', Integer, ForeignKey('asset.id'))
)


class PubItem(CustomModel):
    id = Column(Integer, primary_key=True)
    item_name = Column(String(64), comment=u"项目名称", unique=True, nullable=False)
    item_type = Column(Integer, comment=u"项目类型 1:tomcat 2:server 3:php  4:other", default=4)

    pre_log_file_path = Column(String(128), comment=u"预发布环境日志文件的绝对路径",
                               default='info.log')

    prd_log_file_path = Column(String(128), comment=u"生产环境日志文件的绝对路径",
                               default='info.log')

    clone_path = Column(String(128), comment=u"代码克隆位置", nullable=False, default='/data/item')

    build_dir = Column(String(128), comment=u"编译目录(克隆位置+/+项目名", nullable=False,
                       default='/data/item/')

    build_command = Column(String(128), comment=u"预发布编译命令", nullable=False,
                           default='')

    pre_deploy_path = Column(String(128), comment=u"预发布环境项目部署路径", default='/home/jenkins/')

    pre_startsh = Column(String(128), comment=u"预发布启动脚本", nullable=False,
                         default='start.sh')
    prd_build_command = Column(String(128), comment=u"生产环境编译命令", nullable=False,
                               default=u'mvn clean package -Dmaven.test.skip -P production')
    prd_deploy_path = Column(String(128), comment=u"生产环境项目部署路径", default='/data/source')

    git_repo = Column(String(128), comment=u"版本库地址", nullable=False,
                      default='')

    branch = Column(String(128), comment=u"分支号(可为空)")
    deploy_time = Column(DateTime, default=datetime.datetime.now, nullable=False, comment=u"上次部署预发布时间")
    pre_hostname = Column(String(64), comment=u"预发布环境主机名")
    r = relationship('Asset', secondary=project_asset, backref='projects')
    nginx_proxy = Column(String(64), comment=u"Nginx-proxy主机名（例如:beijing,shanghai）")
    vhost_file = Column(String(128))
    prd_startsh = Column(String(128), comment=u"生产环境启动脚本", default='start.sh')
    prd_build_status = Column(String(128), comment=u"构建状态（不用填）")
    new_version = Column(String(128), comment=u"最新代码版本（不用填）")
    online_version = Column(String(128), comment=u"线上代码版本（不用填）")
    history_version = Column(Text, comment=u"历史版本（不用填）")
    branch_merge = Column(String(32), comment=u"是否合并到master（不用填）")
    is_elk = Column(Boolean, default=False, comment=u"项目是否接入到elk")
    is_pinpoint = Column(Boolean, default=False, comment=u"项目是否接入到pinpoint")
    is_disconf = Column(Boolean, default=False, comment=u"项目是否接入到disconf配置中心")
    is_docker = Column(Boolean, default=False, comment=u"项目是否有可以接入docker的配置文件")
    project_leader_email = Column(String(128), comment=u"项目负责人邮箱")
    alarm_status = Column(String(20), comment=u"告警状态", default="on")

    def __unicode__(self):
        return self.item_name

    @renders('r')
    def format_r(self):
        return ','.join([asset.name for asset in self.r])

    @renders('item_type')
    def format_item_type(self):
        info = {1:"tomcat", 2:"server", 3:"php",  4:"other"}
        return info.get(self.item_type)

    def operates(self):
        return Markup('<a href="' + url_for('ProView.this_form_get', pk=self.id) + '">Download</a>')


class Nginx(CustomModel):
    """nginx 操作"""

    id = Column(Integer, primary_key=True)
    item = Column(String(64), comment=u"项目名称", nullable=False)
    host = Column(String(64), comment=u"该项目所在的主机名", nullable=False)
    command = Column(String(256), comment=u"注释nginx的命令", nullable=False)
    command_re = Column(String(256), comment=u"取消注释Nginx的命令", nullable=False)

    def __unicode__(self):
        return self.name


class BranchTable(Model):
    """分支表"""

    id = Column(Integer, primary_key=True)
    branch_name = Column(String(64), comment=u"分支名")
    status = Column(String(64), comment=u"状态")
    create_time = Column(DateTime, default=datetime.datetime.now, comment=u"创建时间")
    remark = Column(String(128), comment=u"备注")
    create_user = Column(String(128), comment=u"创建人")
    item_obj_id = Column(Integer, ForeignKey('pub_item.id'))
    item_obj = relationship("PubItem")
    build_status = Column(String(128), comment=u"构建状态")
    task_id = Column(String(128), comment=u"任务ID")
    build_time = Column(DateTime, comment=u"上次编译时间")


class icode(Model):
    """统计代码量"""

    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    insertions = Column(Integer)
    deletions = Column(Integer)
    create_time = Column(String(64))


class Record(CustomModel):
    """
    上线记录表
    """
    id = Column(Integer, primary_key=True)
    name = Column(String(90), comment=u"项目名称")
    operate = Column(String(20), comment=u"操作 部署|上线|回滚|加入集群", default=u"部署")
    env = Column(String(20), comment=u"环境 预发布|生产", default=u"预发布")
    resource = Column(String(90), comment=u"主机或者包")
    status = Column(Boolean, comment=u"状态", default=True)
    detail = Column(Text, comment=u"错误原因")

    def __unicode__(self):
        return self.name

    @renders('status')
    def my_status(self):
        return u'成功' if self.status else u"失败"