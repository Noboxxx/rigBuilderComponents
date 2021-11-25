import rigBuilder
from maya import cmds
from . import RParam, RObj


class RMayaComponent(rigBuilder.RBaseComponent):
    # name pattern
    objNamePattern = '{name}_{side}_{index}_{objType}'

    # default component name
    defaultComponentName = 'component'

    # types
    controllerTypeStr = 'ctl'
    skinJointTypeStr = 'skn'
    componentTypeStr = 'cmp'

    leftSide = 'L'
    rightSide = 'R'
    centerSide = 'C'

    # colors
    centerColor = RParam.Color(255, 255, 0)
    leftColor = RParam.Color(0, 255, 0)
    rightColor = RParam.Color(255, 0, 0)

    @property
    def sideMirrorTable(self):
        return {
            self.leftSide: self.rightSide,
            self.rightSide: self.leftSide,
            self.centerSide: None
        }

    @property
    def sideColorTable(self):
        return {
            self.leftSide: self.leftColor,
            self.rightSide: self.rightColor,
            self.centerSide: self.centerColor
        }

    def __init__(
            self,
            name=None,
            side=centerSide,
            index=0,
            color=None,
            size=1.0,
    ):
        super(RMayaComponent, self).__init__()

        # check index
        index = int(index)
        if index < 0:
            raise ValueError('index should be positive -> {}'.format(index))

        # naming parameters
        self.name = str(name) if name is not None else self.defaultComponentName
        self.side = str(side)
        self.index = index

        # display parameters
        self.color = color if color is not None else self.sideColorTable[side]
        self.size = abs(float(size))

        # internal objects
        self.folder = None
        self.rootDags = list()
        self.skinJoints = list()

    def composeObjName(self, objType, nameExtra=None):
        name = '{}_{}'.format(self.name, nameExtra) if nameExtra else self.name
        return self.objNamePattern.format(
            name=name,
            side=self.side,
            index=self.index,
            objType=objType
        )

    def asdict(self):  # type: () -> dict
        data = super(RMayaComponent, self).asdict()
        data['name'] = self.name
        data['side'] = self.side
        data['index'] = self.index
        return data

    def asmirroreddict(self):  # type: () -> dict
        data = super(RMayaComponent, self).asmirroreddict()
        data['side'] = self.sideMirrorTable.get(data['side'], None)
        return data

    def _initializeCreation(self):
        folderName = self.composeObjName(self.componentTypeStr)

        if cmds.objExists(folderName):
            raise RuntimeError('Component already exists -> {}'.format(folderName))

        self.folder = cmds.group(empty=True, name=folderName)

    def _doCreation(self):
        pass

    def _finalizeCreation(self):
        if self.rootDags:
            cmds.parent(self.rootDags, self.folder)

        data = (
            ('skinJoints', self.skinJoints),
            ('inputs', self.inputs),
            ('outputs', self.outputs),
            ('controllers', self.controllers)
        )

        for key, items in data:
            folderMessagePlug = '{}.{}'.format(self.folder, key)
            cmds.addAttr(self.folder, longName=key, attributeType='message')

            for item in items:
                itemMessagePlug = '{}.{}'.format(item, key)
                cmds.addAttr(item, longName=key, attributeType='message')
                cmds.connectAttr(folderMessagePlug, itemMessagePlug)

    def create(self):  # type: () -> None
        self._initializeCreation()
        self._doCreation()
        self._finalizeCreation()


class RCtrlComponent(RMayaComponent):

    defaultComponentName = 'ctrl'

    def __init__(self, matrix=RParam.Matrix(), normalVector=RParam.Vector3(1.0, 0.0, 0.0), **kwargs):
        # type: (RParam.Matrix, RParam.Vector3, ...) -> None
        self.matrix = matrix
        self.normalVector = normalVector
        super(RCtrlComponent, self).__init__(**kwargs)

    def _doCreation(self):
        ctrl = RObj.Controller.create(
            name=self.composeObjName(self.controllerTypeStr),
            color=self.color,
            normalVector=self.normalVector,
        )
        ctrlBuffer = cmds.group(empty=True)
        joint = cmds.joint(name=self.composeObjName(self.skinJointTypeStr))
        cmds.parent(ctrl, ctrlBuffer)
        cmds.parent(joint, ctrl)

        cmds.xform(ctrlBuffer, matrix=self.matrix.aslist())

        self.controllers.append(ctrl)
        self.skinJoints.append(joint)
        self.outputs.append(ctrl)
        self.inputs.append(ctrlBuffer)
        self.rootDags.append(ctrlBuffer)

    def asdict(self):  # type: () -> dict
        data = super(RCtrlComponent, self).asdict()
        data['matrix'] = self.matrix
        data['normalVector'] = self.normalVector
        return data

    def asmirroreddict(self, mirrorAxis='x'):  # type: (basestring) -> dict
        data = super(RCtrlComponent, self).asmirroreddict()
        data['matrix'] = self.matrix.mirrored(mirrorAxis)
        data['normalVector'] = self.normalVector.mirrored(mirrorAxis)
        return data


class RBaseComponent(RCtrlComponent):

    defaultComponentName = 'base'

    def __init__(self, normalVector=RParam.Vector3(0.0, 1.0, 0.0), **kwargs):
        super(RBaseComponent, self).__init__(normalVector=normalVector, **kwargs)

    def _doCreation(self):
        worldBuffer = cmds.group(empty=True)
        worldCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra='world', objType=self.controllerTypeStr),
            color=self.color,
            normalVector=self.normalVector,
        )

        worldJoint = cmds.joint(name=self.composeObjName(nameExtra='world', objType=self.skinJointTypeStr))

        localBuffer = cmds.group(empty=True)
        localCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra='local', objType=self.controllerTypeStr),
            color=self.color,
            normalVector=self.normalVector,
        )

        localJoint = cmds.joint(name=self.composeObjName(nameExtra='local', objType=self.skinJointTypeStr))

        cmds.parent(worldCtrl, worldBuffer)
        cmds.parent(localCtrl, localBuffer)

        cmds.parent(localBuffer, worldCtrl)

        self.inputs.append(worldBuffer)

        self.rootDags.append(worldBuffer)

        self.controllers.append(worldCtrl)
        self.controllers.append(localCtrl)

        self.outputs.append(worldCtrl)
        self.outputs.append(localCtrl)

        self.skinJoints.append(worldJoint)
        self.skinJoints.append(localJoint)


def test():

    cmds.file(new=True, force=True)

    # Instantiate the components
    component = RCtrlComponent(
        side=RCtrlComponent.leftSide,
        matrix=RParam.Matrix(
            vectorX=RParam.Vector3(0, 0, -1),
            vectorY=RParam.Vector3(0, 1, 0),
            vectorZ=RParam.Vector3(1, 0, 0),
            position=RParam.Position3(10, 10, 10)
        ),
    )
    baseComponent = RBaseComponent()

    mirroredComponent = component.mirrored('x')

    #
    print component
    print mirroredComponent
    print baseComponent

    # Create the components
    component.create()
    mirroredComponent.create()
    baseComponent.create()

    cmds.select(clear=True)
