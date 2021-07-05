import rigBuilder
from . import rigUtils
from maya import cmds


class MyComponent(rigBuilder.Component):
    default_side = 'C'
    default_index = 0
    type_ = 'component'

    @classmethod
    def compose_folder_name(cls, id_=None, side=None, index=None):
        id_ = cls.get_default_id() if id_ is None else str(id_)
        side = cls.default_side if side is None else str(side)
        index = cls.default_index if index is None else int(index)

        name = rigUtils.Name.compose(id_=id_, side=side, index=index, type_=cls.type_)
        if cmds.objExists(name):
            cmds.error('\'{}\' already exists.'.format(name))

        return name, id_, side, index

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

    local_prefix = 'local'
    world_prefix = 'world'

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()

        world_ctrl = rigUtils.Ctrl.create(id_='{}_{}'.format(id_, cls.world_prefix), side=side, index=index, axis='y', size=size*1.4, color=rigUtils.Color.yellow)
        local_ctrl = rigUtils.Ctrl.create(id_='{}_{}'.format(id_, cls.local_prefix), side=side, index=index, axis='y', size=size, color=rigUtils.Color.light_yellow)
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

    def get_local_ctrl(self):
        id_, side, index, type_ = rigUtils.Name.split(self.get_folder())
        ctrl_name = rigUtils.Name.compose('{}_{}'.format(id_, self.local_prefix), side, index, 'ctrl')
        return rigUtils.Ctrl(ctrl_name)

    def get_world_ctrl(self):
        id_, side, index, type_ = rigUtils.Name.split(self.get_folder())
        ctrl_name = rigUtils.Name.compose('{}_{}'.format(id_, self.world_prefix), side, index, 'ctrl')
        return rigUtils.Ctrl(ctrl_name)

    def connect_to_local_ctrl(self, child):
        self.connect(self.get_local_ctrl(), child)


class OneCtrl(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False, color=None, axis='x', lock_attrs=None):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()

        ctrl = rigUtils.Ctrl.create(
            id_=id_,
            side=side,
            index=index,
            axis=axis,
            size=size,
            color=color
        )

        if add_joint:
            joint_name = rigUtils.Name.compose(id_=id_, side=side, index=index, type_='skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            cmds.parent(joint, ctrl)
        
        if lock_attrs is not None:
            for lock_attr in lock_attrs:
                plug = '{}.{}'.format(ctrl, lock_attr)
                if cmds.objExists(plug):
                    cmds.setAttr(plug, lock=True, keyable=False)
        
        dags.append(ctrl.get_buffer())

        if matrix:
            cmds.xform(ctrl.get_buffer(), matrix=list(matrix))

        return cls.create_folder(dags=dags, name=name)

    def get_ctrl(self):
        id_, side, index, type_ = rigUtils.Name.split(self.get_folder())
        ctrl_name = rigUtils.Name.compose(id_, side, index, 'ctrl')
        return rigUtils.Ctrl(ctrl_name)

    def connect_to_ctrl(self, child):
        self.connect(self.get_ctrl(), child)


class FkChain(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrices=None, size=1, color=None, axis='x'):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()

        ctrls = list()
        for i, matrix in enumerate(matrices):
            ctrl = rigUtils.Ctrl.create(id_='{}_fk{}'.format(id_, i), side=side, index=index, axis=axis, size=size, color=color)
            joint_name = rigUtils.Name.compose('{}_fk{}'.format(id_, i), side, index, 'skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            cmds.parent(joint, ctrl)
            cmds.xform(ctrl.get_buffer(), matrix=list(matrix))
            if i == 0:
                dags.append(ctrl.get_buffer())
            else:
                cmds.parent(ctrl.get_buffer(), ctrls[i-1])
            ctrls.append(ctrl)

        return cls.create_folder(dags=dags, name=name)