from . import RParam
from maya import cmds


def createMatrixConstraint(parents, child, interface=None):
    return cmds.parentConstraint(parents, child, mo=True)
    if interface is None:
        interface = child

    # for parent in parents:
    multMatrix = cmds.createNode('multMatrix')
    decomposeMatrix = cmds.createNode('decomposeMatrix')
    cmds.connectAttr('{}.worldMatrix[0]'.format(parents[0]), '{}.matrixIn[1]'.format(multMatrix))
    cmds.connectAttr('{}.matrixSum'.format(multMatrix), '{}.inputMatrix'.format(decomposeMatrix))

    parentInverseWorldMatrix = RParam.Matrix(*cmds.getAttr('{}.worldInverseMatrix[0]'.format(parents[0])))
    childWorldMatrix = RParam.Matrix(*cmds.getAttr('{}.worldMatrix[0]'.format(child)))

    childLMatrix = parentInverseWorldMatrix * childWorldMatrix

    cmds.setAttr(
        '{}.matrixIn[0]'.format(multMatrix),
        childLMatrix.aslist(),
        type='matrix'
    )

    for attr in ('translate', 'rotate', 'scale', 'shear'):
        cmds.connectAttr(
            '{}.output{}'.format(decomposeMatrix, attr.title()),
            '{}.{}'.format(child, attr)
        )


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
        color = RParam.Color(*color)
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
