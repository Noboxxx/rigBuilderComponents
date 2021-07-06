import rigBuilder
from . import componentUtils
from maya import cmds
from maya.api import OpenMaya


class MyComponent(rigBuilder.Component):
    default_side = 'C'
    default_index = 0
    type_ = 'component'

    @classmethod
    def compose_folder_name(cls, id_=None, side=None, index=None):
        id_ = cls.__name__.lower() if id_ is None else str(id_)
        side = cls.default_side if side is None else str(side)
        index = cls.default_index if index is None else int(index)

        name = componentUtils.Name.compose(id_=id_, side=side, index=index, type_=cls.type_)
        if cmds.objExists(name):
            cmds.error('\'{}\' already exists.'.format(name))

        return name, id_, side, index


class WorldLocal(MyComponent):

    local_prefix = 'local'
    world_prefix = 'world'

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()
        roots = list()
        ctrls = list()
        ends = list()
        skin_joints = list()

        world_ctrl = componentUtils.Ctrl.create(id_='{}_{}'.format(id_, cls.world_prefix), side=side, index=index, axis='y', size=size * 1.4, color=componentUtils.Color.yellow)
        local_ctrl = componentUtils.Ctrl.create(id_='{}_{}'.format(id_, cls.local_prefix), side=side, index=index, axis='y', size=size, color=componentUtils.Color.light_yellow)
        cmds.parent(local_ctrl.get_buffer(), world_ctrl)

        if add_joint:
            joint_name = componentUtils.Name.compose(id_='{}_local'.format(id_), side=side, index=index, type_='skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            cmds.parent(joint, local_ctrl)
            skin_joints.append(joint)

        dags.append(world_ctrl.get_buffer())

        if matrix:
            cmds.xform(world_ctrl.get_buffer(), matrix=list(matrix))

        roots.append(world_ctrl.get_buffer())
        ends.append(local_ctrl)

        ctrls.append(world_ctrl)
        ctrls.append(local_ctrl)

        return cls.create_folder(dags=dags, name=name, roots=roots, ctrls=ctrls, ends=ends, skin_joints=skin_joints)
    #
    # def get_local_ctrl(self):
    #     id_, side, index, type_ = componentUtils.Name.split(self.get_folder())
    #     ctrl_name = componentUtils.Name.compose('{}_{}'.format(id_, self.local_prefix), side, index, 'ctrl')
    #     return componentUtils.Ctrl(ctrl_name)
    #
    # def get_world_ctrl(self):
    #     id_, side, index, type_ = componentUtils.Name.split(self.get_folder())
    #     ctrl_name = componentUtils.Name.compose('{}_{}'.format(id_, self.world_prefix), side, index, 'ctrl')
    #     return componentUtils.Ctrl(ctrl_name)
    #
    # def connect_to_local_ctrl(self, child):
    #     self.connect(self.get_local_ctrl(), child)


class OneCtrl(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False, color=None, axis='x', lock_attrs=None):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()
        ctrls = list()
        ends = list()
        roots = list()
        skin_joints = list()

        ctrl = componentUtils.Ctrl.create(
            id_=id_,
            side=side,
            index=index,
            axis=axis,
            size=size,
            color=color
        )

        if add_joint:
            joint_name = componentUtils.Name.compose(id_=id_, side=side, index=index, type_='skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            cmds.parent(joint, ctrl)
            skin_joints.append(joint)
        
        if lock_attrs is not None:
            for lock_attr in lock_attrs:
                plug = '{}.{}'.format(ctrl, lock_attr)
                if cmds.objExists(plug):
                    cmds.setAttr(plug, lock=True, keyable=False)
        
        dags.append(ctrl.get_buffer())

        if matrix:
            cmds.xform(ctrl.get_buffer(), matrix=list(matrix))

        ctrls.append(ctrl)
        ends.append(ctrl)
        roots.append(ctrl.get_buffer())

        return cls.create_folder(dags=dags, name=name, ctrls=ctrls, ends=ends, roots=roots, skin_joints=skin_joints)
    #
    # def get_ctrl(self):
    #     id_, side, index, type_ = componentUtils.Name.split(self.get_folder())
    #     ctrl_name = componentUtils.Name.compose(id_, side, index, 'ctrl')
    #     return componentUtils.Ctrl(ctrl_name)
    #
    # def connect_to_ctrl(self, child):
    #     self.connect(self.get_ctrl(), child)


class FkChain(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrices=None, size=1, color=None, axis='x'):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()

        ctrls = list()
        for i, matrix in enumerate(matrices):
            ctrl = componentUtils.Ctrl.create(id_='{}_fk{}'.format(id_, i), side=side, index=index, axis=axis, size=size, color=color)
            joint_name = componentUtils.Name.compose('{}_fk{}'.format(id_, i), side, index, 'skin')
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
    #
    # def get_ctrls(self):
    #     id_, side, index, type_ = componentUtils.Name.split(self.get_folder())
    #     ctrls_name_pattern = componentUtils.Name.compose('{}_fk*'.format(id_), side, index, 'ctrl')
    #     ctrls = [componentUtils.Ctrl(ctrl) for ctrl in cmds.ls(ctrls_name_pattern) or list()]
    #     return ctrls


class HybridChain(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrices=None, size=1, fk_color=None, ik_color=None, axis='x'):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)
        dags = list()
        roots = list()
        ends = list()
        skin_joints = list()
        ctrls = list()

        # Create curve
        points = [matrix.get_translation() for matrix in matrices]
        curve_name = componentUtils.Name.compose(id_, side, index, 'ikCurve')
        curve = cmds.curve(point=points, name=curve_name, degree=3)
        for shape in cmds.listRelatives(curve, shapes=True):
            cmds.rename(shape, curve + 'Shape')

        dags.append(curve)

        # Create joint chain
        cmds.select(clear=True)
        mcurve = componentUtils.Utils.get_mfn(curve + 'Shape')
        joints = list()
        for i, point in enumerate(points):
            closest_point, _ = mcurve.closestPoint(OpenMaya.MPoint(point))
            joint_name = componentUtils.Name.compose('{}_{}'.format(id_, i), side, index, 'skin')
            joint = cmds.joint(p=(closest_point.x, closest_point.y, closest_point.z), name=joint_name)
            joints.append(joint)
        cmds.joint(
            joints[0],
            e=True,
            orientJoint='xyz',
            secondaryAxisOrient='zdown',
            children=True,
            zeroScaleOrient=True
        )
        for axis in ('X', 'Y', 'Z'):
            cmds.setAttr('{}.jointOrient{}'.format(joints[-1], axis), 0)

        dags.append(joints[0])
        
        # Create ik spine
        ik_handle_name = componentUtils.Name.compose(id_, side, index, 'ikHandle')
        ik_handle, _ = cmds.ikHandle(
            name=ik_handle_name,
            solver='ikSplineSolver',
            createCurve=False,
            rootOnCurve=False,
            parentCurve=False,
            startJoint=joints[0],
            endEffector=joints[-1],
            curve=curve
        )

        dags.append(ik_handle)

        # Create ik ctrls
        ik_ctrls = list()
        ik_joints = list()
        for i, joint in enumerate((joints[0], joints[-1])):
            ik_ctrl = componentUtils.Ctrl.create(
                id_='{}_ik{}'.format(id_, i),
                side=side,
                index=index,
                size=size,
                axis='y',
                color=ik_color,
            )
            # Create curve's joint
            cmds.select(clear=True)
            ik_joint = cmds.joint()
            ik_joints.append(ik_joint)
            cmds.parent(ik_joint, ik_ctrl)

            # Snap ctrl to main joint chain position
            joint_matrix = componentUtils.Matrix(cmds.xform(joint, q=True, matrix=True, worldSpace=True))
            cmds.xform(ik_ctrl.get_buffer(), translation=joint_matrix.get_translation())

            ik_ctrls.append(ik_ctrl)

        cls.connect(ik_ctrls[0], joints[0])

        # Skin the curve
        cmds.skinCluster(ik_joints, curve)

        # Create fk ctrls
        fk_ctrls = list()
        for i, joint in enumerate(joints):
            fk_ctrl = componentUtils.Ctrl.create(
                id_='{}_{}'.format(id_, i),
                side=side,
                index=index,
                color=fk_color,
                size=size
            )
            joint_matrix = cmds.xform(joint, q=True, matrix=True, worldSpace=True)
            cmds.xform(fk_ctrl.get_buffer(), matrix=joint_matrix)
            fk_ctrls.append(fk_ctrl)
            if i != 0:
                cmds.parent(fk_ctrl.get_buffer(), fk_ctrls[i - 1])

        # Like ik anf fk setup
        cmds.parent(ik_ctrls[-1].get_buffer(), fk_ctrls[-1])
        cmds.parent(fk_ctrls[0].get_buffer(), ik_ctrls[0])

        dags.append(ik_ctrls[0].get_buffer())

        roots.append(ik_ctrls[0])

        return cls.create_folder(dags=dags, name=name, skin_joints=skin_joints, ctrls=ctrls, ends=ends, roots=roots)
