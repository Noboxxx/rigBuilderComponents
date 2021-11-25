from . import RParam
from maya import cmds


class Controller(object):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}.{}: {}>'.format(self.__class__.__module__, self.__class__.__name__, self.name)

    @classmethod
    def create(
            cls,
            name='ctrl#',
            color=RParam.defaultColor,
            radius=1.0,
            normalVector=RParam.xVector,
    ):
        name, = cmds.circle(
            name=name,
            constructionHistory=False,
            radius=radius,
            normal=normalVector.aslist()
        )

        cmds.controller(name)

        cmds.setAttr('{}.v'.format(name), lock=True, keyable=False)

        for shape in cmds.listRelatives(name, children=True, shapes=True):
            cmds.setAttr('{}.overrideEnabled'.format(shape), True)
            cmds.setAttr('{}.overrideRGBColors'.format(shape), True)

            cmds.setAttr('{}.overrideColorR'.format(shape), color.r / 255.0)
            cmds.setAttr('{}.overrideColorG'.format(shape), color.g / 255.0)
            cmds.setAttr('{}.overrideColorB'.format(shape), color.b / 255.0)

        return cls(name)
