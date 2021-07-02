from maya import cmds


class Name(object):
    default_id = 'untitled'
    default_side = 'C'
    default_index = 0
    default_type = 'unknown'

    def __init__(self, name):
        if not self.is_one(name):
            cmds.error('\'{0}\' is not a valid name.'.format(name))
        self.__name = name

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
        self.__name = name

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
    def draw_curve(cls, name, axis='x', size=1):
        if axis == 'x':
            normal = (1, 0, 0)
        elif axis == 'y':
            normal = (0, 1, 0)
        else:
            normal = (0, 0, 1)
        return cmds.circle(name=name, ch=False, normal=normal, radius=size)[0]

    @classmethod
    def create(cls, id_=None, side=None, index=None, axis='x', size=1):
        name = Name.compose(id_, side, index, cls.type_)
        buffer_name = Name.compose(id_, side, index, cls.buffer_type)

        if cmds.objExists(name):
            cmds.error('\'{0}\' already exists'.format(name))

        if cmds.objExists(buffer_name):
            cmds.error('\'{0}\' already exists'.format(buffer_name))

        buffer_ = cmds.group(name=buffer_name, empty=True)
        ctrl = cls.draw_curve(name=name, axis=axis, size=size)

        cmds.parent(ctrl, buffer_)

        return cls(ctrl)

    def get_name(self):
        return self.__name

    def get_buffer(self):
        parents = cmds.listRelatives(self.get_name(), parent=True)

        if parents:
            parent = parents[0]
            if parent.endswith(self.buffer_type):
                return parent
        return False

