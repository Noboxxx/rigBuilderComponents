from __future__ import division
from maya import cmds
from maya.api import OpenMaya


class Name(object):
    default_id = 'untitled'
    default_side = 'C'
    default_index = 0
    default_type = 'unknown'

    def __init__(self, name):
        if not self.is_one(name):
            cmds.error('\'{0}\' is not a valid name.'.format(name))
        self.__name = str(name)

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    def get_name(self):
        return self.__name

    @classmethod
    def is_one(cls, name):
        name = str(name)
        name_split = name.split('_')

        if len(name_split) >= 4:
            if name_split[-2].isdigit():
                return True
        return False

    @classmethod
    def join(cls, id_, side, index, type_):
        return '{0}_{1}_{2}_{3}'.format(id_, side, index, type_)

    @classmethod
    def split(cls, name):
        name_split = name.split('_')

        type_ = name_split.pop()
        index = int(name_split.pop())
        side = name_split.pop()
        id_ = '_'.join(name_split)
        return id_, side, index, type_

    @classmethod
    def compose(cls, id_=None, side=None, index=None, type_=None):
        id_ = cls.default_id if id_ is None else str(id_)
        side = cls.default_side if side is None else str(side)
        index = cls.default_index if index is None else int(index)
        type_ = cls.default_type if type_ is None else str(type_)

        result = cls.join(id_, side, index, type_)
        return cls(result)


class Ctrl(object):
    type_ = 'ctrl'
    buffer_type = 'ctrlBuffer'

    def __init__(self, name):
        if not self.is_one(name):
            cmds.error('\'{0}\' is not a valid name.'.format(name))
        self.__name = str(name)

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    @classmethod
    def is_one(cls, name):
        name = str(name)
        if name.endswith(cls.type_):
            if cmds.objExists(name):
                if cmds.objectType(name, isAType='transform'):
                    return True
        return False

    @classmethod
    def draw_curve(cls, name, axis='x', size=1, shape=None):
        shape = Shape.square if shape is None else shape

        scaled_points = list()
        for point in shape['points']:
            result = (
                point[0] * size,
                point[1] * size,
                point[2] * size
            )
            scaled_points.append(result)

        oriented_points = list()
        for point in scaled_points:
            if axis == 'y':
                result = point
            elif axis == 'x':
                result = (
                    point[1],
                    point[2],
                    point[0],
                )
            else:
                result = (
                    point[2],
                    point[1],
                    point[0],
                )
            oriented_points.append(result)

        return cmds.curve(point=oriented_points, degree=shape['degree'], name=name)

    @classmethod
    def create(cls, id_=None, side=None, index=None, axis='x', size=1, color=None, shape=None):
        name = Name.compose(id_, side, index, cls.type_)
        buffer_name = Name.compose(id_, side, index, cls.buffer_type)

        if cmds.objExists(name):
            cmds.error('\'{0}\' already exists'.format(name))

        if cmds.objExists(buffer_name):
            cmds.error('\'{0}\' already exists'.format(buffer_name))

        buffer_ = cmds.group(name=buffer_name, empty=True)
        ctrl = cls.draw_curve(name=name, axis=axis, size=size, shape=shape)
        cmds.setAttr('{}.{}'.format(ctrl, 'v'), lock=True, keyable=False)

        cmds.parent(ctrl, buffer_)

        ctrl = cls(ctrl)

        if color is not None:
            ctrl.set_color(color=color)

        return ctrl

    def get_name(self):
        return self.__name

    def get_buffer(self):
        parents = cmds.listRelatives(self.get_name(), parent=True)

        if parents:
            parent = parents[0]
            if parent.endswith(self.buffer_type):
                return parent
        return False

    def set_color(self, color):
        color = list(color)

        for shape in self.get_shapes():
            cmds.setAttr('{}.overrideEnabled'.format(shape), True)
            cmds.setAttr('{}.overrideRGBColors'.format(shape), 1)

            cmds.setAttr('{}.overrideColorR'.format(shape), color[0])
            cmds.setAttr('{}.overrideColorG'.format(shape), color[1])
            cmds.setAttr('{}.overrideColorB'.format(shape), color[2])

    def get_shapes(self):
        return cmds.listRelatives(self.get_name(), shapes=True, type='nurbsCurve') or list()


class Matrix(object):

    def __init__(self, matrix):
        if not self.is_one(matrix):
            cmds.error('\'{}\' is not a valid matrix.')
        self.__matrix = list(matrix)

    @classmethod
    def is_one(cls, matrix):
        matrix = list(matrix)
        if len(matrix) == 16:
            for scalar in matrix:
                if not isinstance(scalar, float):
                    return False
            return True
        return False

    def get_matrix(self):
        return self.__matrix

    def __repr__(self):
        return self.get_matrix()

    def __str__(self):
        return str(self.__matrix)

    def __iter__(self):
        return iter(self.get_matrix())

    @classmethod
    def get_from_dag(cls, dag):
        matrix = cmds.xform(dag, q=True, matrix=True, worldSpace=True)
        return cls(matrix)

    @classmethod
    def get_from_transforms(cls, trs=(0, 0, 0, 0, 0, 0, 1, 1, 1), order=OpenMaya.MEulerRotation.kXYZ):
        def get_meuler_rotation_from_rotation(rotation, order_=OpenMaya.MEulerRotation.kXYZ):
            radians = [OpenMaya.MAngle(value, OpenMaya.MAngle.kDegrees).asRadians() for value in rotation]
            return OpenMaya.MEulerRotation(radians, order=order_)

        t = OpenMaya.MVector(trs[:3])
        r = get_meuler_rotation_from_rotation(trs[3:6], order_=order)
        s = trs[6:]
        mtrs_matrix = OpenMaya.MTransformationMatrix()
        mtrs_matrix.setRotation(r)
        mtrs_matrix.setTranslation(t, OpenMaya.MSpace.kWorld)
        mtrs_matrix.setScale(s, OpenMaya.MSpace.kWorld)
        mmatrix = mtrs_matrix.asMatrix()
        return cls(mmatrix)

    @classmethod
    def blend_matrices(cls, matrix_a, matrix_b, blender=.5):
        def blend_values(list_a, list_b, blender_):
            result = list()
            for a, b in zip(list_a, list_b):
                result.append((a * (1.0 - blender_)) + (b * blender_))
            return tuple(result)
        matrix_a = cls(matrix_a)
        matrix_b = cls(matrix_b)

        matrix_a_translate = matrix_a.get_translation()
        matrix_b_translate = matrix_b.get_translation()
        matrix_result_translate = blend_values(matrix_a_translate, matrix_b_translate, blender_=blender)

        matrix_a_rotation = matrix_a.get_rotation()
        matrix_b_rotation = matrix_b.get_rotation()
        matrix_result_rotation = blend_values(matrix_a_rotation, matrix_b_rotation, blender_=blender)

        matrix_a_scale = matrix_a.get_scale()
        matrix_b_scale = matrix_b.get_scale()
        matrix_result_scale = blend_values(matrix_a_scale, matrix_b_scale, blender_=blender)

        transforms = matrix_result_translate + matrix_result_rotation + matrix_result_scale
        return cls.get_from_transforms(trs=transforms)

    def get_translation(self):
        mtransform_matrix = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(self.__matrix))
        return list(mtransform_matrix.translation(OpenMaya.MSpace.kWorld))

    def get_rotation(self, radians=False):
        mtransform_matrix = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(self.__matrix))
        rotation = mtransform_matrix.rotation()
        if radians is True:
            return list(rotation)
        return [OpenMaya.MAngle(value, OpenMaya.MAngle.kRadians).asDegrees() for value in rotation]

    def get_scale(self):
        mtransform_matrix = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(self.__matrix))
        return mtransform_matrix.scale(OpenMaya.MSpace.kObject)

    def get_mirror(self):
        translation = self.get_translation()
        rotation = self.get_rotation()
        scale = self.get_scale()

        trs = (
            translation[0] * -1, translation[1], translation[2],
            180 - rotation[0], rotation[1], 180 - rotation[2],
            scale[0], scale[1] , scale[2],
        )

        return self.get_from_transforms(trs)


class Color(object):

    red = (255/255, 0, 0)
    dark_red = (128/255, 0, 0)
    light_red = (255/255, 128/255, 128/255)

    yellow = (255/255, 255/255, 0)
    dark_yellow = (204/255, 153/255, 0)
    light_yellow = (255/255, 255/255, 153/255)

    blue = (0, 0, 255/255)
    dark_blue = (0, 0, 102/255)
    light_blue = (51/255, 153/255, 255/255)

    green = (0, 255/255, 0)
    dark_green = (0, 204/255, 0)
    light_green = (153/255, 255/255, 204/255)

    pink = (255/255, 102/255, 255/255)


class Shape(object):

    square = {
        'points': ((.5, 0, .5), (-.5, 0, .5), (-.5, 0, -.5), (.5, 0, -.5), (.5, 0, .5)),
        'degree': 1,
    }
    cube = {
        'points': ((0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5)),
        'degree': 1,
    }

    # circle = {
    #     'points': ((6.78573232311e-17, 6.78573232311e-17, -1.10819418755), (-0.783611624891, 4.79823734099e-17, -0.783611624891), (-1.10819418755, 3.51773561901e-33, -5.74489823752e-17), (-0.783611624891, -4.79823734099e-17, 0.783611624891), (-1.11008569696e-16, -6.78573232311e-17, 1.10819418755), (0.783611624891, -4.79823734099e-17, 0.783611624891), (1.10819418755, -9.25367921011e-33, 1.51124050078e-16), (0.783611624891, 4.79823734099e-17, -0.783611624891), (6.78573232311e-17, 6.78573232311e-17, -1.10819418755),),
    #     'degree': 3,
    # }


class Utils(object):

    @classmethod
    def get_mfn(cls, node):
        node = str(node)
        selection_list = OpenMaya.MSelectionList()
        selection_list.add(node)
        mobject = selection_list.getDependNode(0)
        try:
            return eval('OpenMaya.MFn{0}(mobject)'.format(mobject.apiTypeStr[1:]))
        except AttributeError:
            return mobject