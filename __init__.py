import rigBuilder
from . import rigUtils
from maya import cmds


class MyComponent(rigBuilder.Component):
    default_side = 'C'
    default_index = 0
    type_ = 'component'

    @classmethod
    def get_all(cls):
        components = list()
        for node in cmds.ls('*_{}'.format(cls.type_)):
            if cls.is_one(node):
                components.append(cls(node))
        return components

    @classmethod
    def get_all_skin_joints(cls):
        joints = list()
        for component in cls.get_all():
            joints += component.get_skin_joints()
        return joints

    @classmethod
    def get_all_ctrls(cls):
        ctrls = list()
        for component in cls.get_all():
            ctrls += component.get_ctrls()
        return ctrls

    @classmethod
    def get_default_id(cls):
        return cls.__name__.lower()

    def get_ctrls(self):
        ctrls = list()
        for node in cmds.listRelatives(self.get_folder(), allDescendents=True):
            if rigUtils.Ctrl.is_one(node):
                ctrls.append(rigUtils.Ctrl(node))
        return ctrls

    def get_skin_joints(self):
        skin_joints = list()
        for node in cmds.listRelatives(self.get_folder(), allDescendents=True):
            if node.endswith('_skin') and cmds.objectType(node, isAType='joint'):
                skin_joints.append(node)
        return skin_joints


class WorldLocal(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False):
        id_ = cls.get_default_id() if id_ is None else str(id_)
        side = cls.default_side if side is None else str(side)
        index = cls.default_index if index is None else int(index)

        matrix = rigUtils.Matrix.get_from_transforms() if matrix is None else rigUtils.Matrix(matrix)

        dags = list()

        name = rigUtils.Name.compose(id_=id_, side=side, index=index, type_=cls.type_)
        if cmds.objExists(name):
            cmds.error('\'{}\' already exists.'.format(name))

        world_ctrl = rigUtils.Ctrl.create(id_='{}_world'.format(id_), side=side, index=index, axis='y', size=size*1.4)
        local_ctrl = rigUtils.Ctrl.create(id_='{}_local'.format(id_), side=side, index=index, axis='y', size=size)
        cmds.parent(local_ctrl.get_buffer(), world_ctrl)

        if add_joint:
            joint_name = rigUtils.Name.compose(id_='{}_local'.format(id_), side=side, index=index, type_='skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            cmds.parent(joint, local_ctrl)

        dags.append(world_ctrl.get_buffer())

        if matrix:
            cmds.xform(world_ctrl.get_buffer(), matrix=list(matrix))

        return cls.create_folder(dags=dags, name=name)