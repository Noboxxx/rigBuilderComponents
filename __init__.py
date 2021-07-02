import rigBuilder
from . import rigUtils
from maya import cmds


class WorldLocal(rigBuilder.Component):

    @classmethod
    def create(cls, id_=None, side='C', index=0, matrix=None, size=1):
        id_ = cls.__name__.lower() if id_ is None else str(id_)
        side = str(side)
        index = int(index)

        dags = list()

        name = rigUtils.Name.compose(id_=id_, side=side, index=index, type_='component')
        if cmds.objExists(name):
            cmds.error('\'{}\' already exists.'.format(name))

        world_ctrl = rigUtils.Ctrl.create(id_='{}_world'.format(id_), side=side, index=index, axis='y', size=size*1.4)
        local_ctrl = rigUtils.Ctrl.create(id_='{}_local'.format(id_), side=side, index=index, axis='y', size=size)
        cmds.parent(local_ctrl.get_buffer(), world_ctrl)

        dags.append(world_ctrl.get_buffer())

        if matrix:
            matrix.apply(world_ctrl.get_buffer())

        return cls.create_folder(dags=dags, name=name)