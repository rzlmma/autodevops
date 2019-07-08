# -*- coding:utf-8 -*-
# __author__ = majing
from flask import redirect
from flask_appbuilder import ModelView
from flask_appbuilder.actions import action
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
import sqlalchemy.types as types


class CustomModelView(ModelView):
    base_order = ('changed_on', 'desc')
    show_columns = ['created_by', 'created_on', 'changed_by', 'changed_on']

    @action("multidelete", u"批量删除", u"确定要删除所选的资源?", "fa-eraser")
    def multi_delete(self, items):
        """
        删除多个 
        """
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())


class CustomModel(Model, AuditMixin):

    __abstract__ = True

    @classmethod
    def get_lable_columns(self):
        rest = dict()
        for field in self.__mapper__.c.keys():
            col = getattr(self, field)
            rest[field] = col.comment
        return rest


class ChoiceType(types.TypeDecorator):

    impl = types.Integer

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.iteritems() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]
