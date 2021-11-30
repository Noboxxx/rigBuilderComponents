from . import RObj
import rigBuilder as RBuild, RComp
from maya import cmds


class RRig(object):

    defaultName = 'rig'

    def __init__(self, name=None, components=None, connections=None):
        self.components = list(RBuild.get(components, list()))
        self.connections = list(RBuild.get(connections, list()))

        self.name = str(RBuild.get(name, self.defaultName))

        self.folder = None

    def create(self):
        # create folder
        self.folder = cmds.group(name=self.name, empty=True)

        # Create and parent components
        for component in self.components:
            component.create()
            cmds.parent(component.folder, self.folder)

        # Connect components
        for parentComponent, inputIndex, childComponent, outputIndex in self.connections:
            try:
                RObj.createMatrixConstraint((parentComponent.outputs[inputIndex],), childComponent.inputs[outputIndex])
            except IndexError:
                msg = 'impossible to make the connection: {}.outputs[{}] -> {}.inputs[{}]'.format(
                    parentComponent.folder,
                    inputIndex,
                    childComponent.folder,
                    outputIndex
                )
                raise IndexError(msg)
