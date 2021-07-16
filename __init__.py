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


class OneCtrl(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrix=None, size=1, add_joint=False, color=None, axis='x', lock_attrs=None, shape=None):
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
            color=color,
            shape=shape
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


class FkChain(MyComponent):

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrices=None, size=1, color=None, axis='x'):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()
        roots = list()
        ends = list()
        skin_joints = list()

        ctrls = list()
        for i, matrix in enumerate(matrices):
            ctrl = componentUtils.Ctrl.create(id_='{}_fk_{}'.format(id_, i), side=side, index=index, axis=axis, size=size, color=color)
            joint_name = componentUtils.Name.compose('{}_fk_{}'.format(id_, i), side, index, 'skin')
            cmds.select(clear=True)
            joint = cmds.joint(name=joint_name)
            skin_joints.append(joint)
            cmds.parent(joint, ctrl)
            cmds.xform(ctrl.get_buffer(), matrix=list(matrix))
            if i == 0:
                dags.append(ctrl.get_buffer())
            else:
                cmds.parent(ctrl.get_buffer(), ctrls[i-1])
            ctrls.append(ctrl)
            ends.append(ctrl)

        roots.append(ctrls[0].get_buffer())

        return cls.create_folder(dags=dags, name=name, roots=roots, ends=ends, skin_joints=skin_joints, ctrls=ctrls)


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
            skin_joints.append(joint)
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

        ends.append(joints[-1])
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
                id_='{}_ik_{}'.format(id_, i),
                side=side,
                index=index,
                size=size,
                axis='y',
                color=ik_color,
            )
            ctrls.append(ik_ctrl)
            # Create curve's joint
            cmds.select(clear=True)
            ik_joint_name = componentUtils.Name.compose('{}_ik_{}'.format(id_, i), side, index, 'jnt')
            ik_joint = cmds.joint(name=ik_joint_name)
            ik_joints.append(ik_joint)
            cmds.parent(ik_joint, ik_ctrl)

            # Snap ctrl to main joint chain position
            joint_matrix = componentUtils.Matrix(cmds.xform(joint, q=True, matrix=True, worldSpace=True))
            cmds.xform(ik_ctrl.get_buffer(), translation=joint_matrix.get_translation())

            ik_ctrls.append(ik_ctrl)

        componentUtils.Utils.matrix_constraint(ik_ctrls[0], joints[0], maintain_offset=True)

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
            ctrls.append(fk_ctrl)
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


class TwoSegmentsLimb(MyComponent):

    @classmethod
    def create_chain(cls, id_, side, index, type_, matrices):
        joints = list()
        for i, matrix in enumerate(matrices):
            cmds.select(clear=True)
            joint_name = componentUtils.Name.compose('{}_{}'.format(id_, i), side, index, type_)
            joint = cmds.joint(name=joint_name)
            cmds.xform(joint, matrix=list(matrix))
            joints.append(joint)
            if i != 0:
                cmds.parent(joint, joints[i - 1])
        cmds.makeIdentity(joints[0], apply=True, translate=False, rotate=True, scale=False, normal=False, pn=True)
        return joints

    @classmethod
    def create(cls, id_=None, side=None, index=None, matrices=None, size=1, fk_color=None, ik_color=None):
        name, id_, side, index = cls.compose_folder_name(id_=id_, side=side, index=index)

        dags = list()
        roots = list()
        ends = list()
        skin_joints = list()
        ctrls = list()

        ###
        if len(matrices) != 4:
            cmds.error('Got () matrices. Need exactly 4.'.format(len(matrices)))

        # draw skin joints
        joints = cls.create_chain(id_, side, index, 'skin', matrices)
        ik_joints = cls.create_chain('{}_{}'.format(id_, 'ik'), side, index, 'jnt', matrices)

        joints_grp_name = componentUtils.Name.compose('{}_{}'.format(id_, 'joints'), side, index, 'grp')
        joints_grp = cmds.group(empty=True, name=joints_grp_name)
        cmds.xform(joints_grp, matrix=list(matrices[0]))
        cmds.parent(joints[0], ik_joints[0], joints_grp)

        dags.append(joints_grp)
        skin_joints += joints
        ends.append(joints[-1])
        roots.append(joints_grp)

        # ik handle
        ik_handle_name = componentUtils.Name.compose(id_, side, index, 'ikHandle')
        ik_handle, _ = cmds.ikHandle(
            name=ik_handle_name,
            solver='ikRPsolver',
            startJoint=ik_joints[0],
            endEffector=ik_joints[-2],
        )

        dags.append(ik_handle)

        # ik handle hand
        ik_handle_hand_name = componentUtils.Name.compose(id_, side, index, 'ikHandle')
        ik_handle_hand, _ = cmds.ikHandle(
            name=ik_handle_hand_name,
            solver='ikSCsolver',
            startJoint=ik_joints[-2],
            endEffector=ik_joints[-1],
        )

        dags.append(ik_handle)

        # Ik arm ctrl
        ik_arm_ctrl = componentUtils.Ctrl.create(id_='{}_{}'.format(id_, 'ik'), side=side, index=index, size=size, color=ik_color, shape=componentUtils.Shape.cube)
        cmds.xform(ik_arm_ctrl.get_buffer(), matrix=list(matrices[-2]))
        componentUtils.Utils.matrix_constraint(ik_arm_ctrl, ik_handle, maintain_offset=True)
        componentUtils.Utils.matrix_constraint(ik_arm_ctrl, ik_handle_hand, maintain_offset=True)

        dags.append(ik_arm_ctrl.get_buffer())
        ctrls.append(ik_arm_ctrl)
        roots.append(ik_arm_ctrl.get_buffer())

        # Connect ik chain to skin_chain
        for ik_joint, skin_joint in zip(ik_joints, skin_joints):
            for attr in ('t', 'r', 's'):
                cmds.connectAttr('{}.{}'.format(ik_joint, attr), '{}.{}'.format(skin_joint, attr))

        ###
        return cls.create_folder(dags=dags, name=name, skin_joints=skin_joints, ctrls=ctrls, ends=ends, roots=roots)
