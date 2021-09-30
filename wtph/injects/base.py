# -*- coding: utf-8 -*-
# @Time: 2021/9/30 22:04

class BaseAppTypeHint(object):
    def __new__(cls, *args, **kwargs):
        raise TypeError("Can't create FlaskTypeHint object")
