import rigBuilder
from . import rigUtils
from maya import cmds


class WorldLocal(rigBuilder.Component):

    @classmethod
    def create(cls, id_=None, side='C', index=0):
        dags = list()

        name = rigUtils.Name.compose(id_=id_, side=side, index=index, type_='component')
        if cmds.objExists(name):
            cmds.error('\'{}\' already exists.'.format(name))

        world_ctrl = rigUtils.Ctrl.create(id_='world', side=side, index=index)
        return cls.create_folder(dags=dags, name=name, parent=parent)