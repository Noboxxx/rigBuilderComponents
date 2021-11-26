from . import RParam
from maya import cmds


def createBuffer(obj, bufferSuffix='Buffer'):
    buffer_ = cmds.group(empty=True, name='{}{}'.format(obj, bufferSuffix))
    objMatrix = cmds.xform(obj, q=True, matrix=True, worldSpace=True)
    cmds.xform(buffer_, matrix=objMatrix)

    objParents = cmds.listRelatives(obj, parent=True)

    cmds.parent(obj, buffer_)
    if objParents:
        cmds.parent(buffer_, objParents[0])

    return buffer_


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
            color=RParam.Color(0, 0, 255),
            normal=RParam.Vector3(1.0, 0.0, 0.0),
            size=1.0,
    ):
        name, = cmds.circle(
            name=name,
            constructionHistory=False,
            radius=size,
            normal=normal.aslist(),
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
