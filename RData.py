import rigBuilder
from maya import cmds


class MatrixFile(rigBuilder.JsonFile):

    def export(self, objs, force=False):
        data = dict()
        for obj in objs:
            data[obj] = cmds.xform(obj, q=True, matrix=True, worldSpace=True)

        self.dump(data, force=force)

    def import_(self):
        for name, matrix in self.load().items():
            locator = cmds.spaceLocator(name=name)
            cmds.xform(locator, matrix=matrix)
