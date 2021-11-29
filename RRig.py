from . import RObj
import rigBuilder as RBuild, RComp
from maya import cmds


class RRig(object):

    defaultName = 'rig'

    def __init__(self, name=None, matrixData=None):
        self.components = list()
        self.connections = list()

        self.name = str(RBuild.get(name, self.defaultName))
        self.matrixData = dict(RBuild.get(matrixData, dict()))

        self.folder = None

    def _initializeCreation(self):
        self.folder = cmds.group(name=self.name, empty=True)

    def _doCreation(self):
        pass

    def _finalizeCreation(self):
        # Create and parent components
        for component in self.components:
            component.create()
            cmds.parent(component.folder, self.folder)

        # Connect components
        for parentComponent, inputIndex, childComponent, outputIndex in self.connections:
            RObj.createMatrixConstraint((parentComponent.outputs[inputIndex],), childComponent.inputs[outputIndex])

    def create(self):
        self._initializeCreation()
        self._doCreation()
        self._finalizeCreation()


class RBaseRig(RRig):

    def __init__(self, **kwargs):
        super(RBaseRig, self).__init__(**kwargs)

        self.baseComponent = RComp.RBaseComponent()
        self.components.append(self.baseComponent)
