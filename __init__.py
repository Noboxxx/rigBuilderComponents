import rigBuilder
from maya import cmds
from . import RParam, RObj


class RMayaComponent(rigBuilder.RBaseComponent):
    # name pattern
    objNamePattern = '{name}_{side}_{index}_{objType}'

    # types
    controllerTypeStr = 'ctl'
    skinJointTypeStr = 'skn'
    componentTypeStr = 'cmp'

    # sides
    leftSide = 'L'
    rightSide = 'R'
    centerSide = 'C'

    # colors
    specialColor = RParam.Color(166, 220, 237)

    # defaults
    defaultName = 'untitled'
    defaultSide = centerSide
    defaultIndex = 0
    defaultCtrlSize = 1.0
    defaultCtrlNormal = RParam.Vector3(1.0, 0.0, 0.0)

    @property
    def defaultColor(self):
        return self.sideColorTable[self.side]

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
            self.leftSide: RParam.Color(0, 255, 0),
            self.rightSide: RParam.Color(255, 0, 0),
            self.centerSide: RParam.Color(255, 255, 0),
        }

    def __init__(self, name=None, side=None, index=None, ctrlColor=None, ctrlSize=None, ctrlNormal=None):
        # type: (str, str, int, RParam.Color, float, RParam.Vector3) -> None
        super(RMayaComponent, self).__init__()

        # naming parameters
        self.name = str(name) if name is not None else self.defaultName
        self.side = str(side) if side is not None else self.defaultSide
        self.index = max(0, int(index)) if index is not None else self.defaultIndex

        # display parameters
        self.ctrlColor = RParam.Color(*ctrlColor) if ctrlColor is not None else self.defaultColor
        self.ctrlSize = max(0.0, float(ctrlSize)) if ctrlSize is not None else self.defaultCtrlSize
        self.ctrlNormal = RParam.Vector3(*ctrlNormal) if ctrlNormal is not None else self.defaultCtrlNormal

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

    defaultName = 'ctrl'
    defaultMatrix = RParam.Matrix()

    def __init__(self, matrix=None, **kwargs):
        # type: (RParam.Matrix, ...) -> None
        super(RCtrlComponent, self).__init__(**kwargs)

        self.matrix = RParam.Matrix(*matrix) if matrix is not None else self.defaultMatrix

        self.output = rigBuilder.ROutput()
        self.input = rigBuilder.RInput()

    def _doCreation(self):
        ctrl = RObj.Controller.create(
            name=self.composeObjName(self.controllerTypeStr),
            color=self.ctrlColor,
            normal=self.ctrlNormal,
            size=self.ctrlSize
        )
        joint = cmds.joint(name=self.composeObjName(self.skinJointTypeStr))
        ctrlBuffer = RObj.createBuffer(ctrl)

        cmds.xform(ctrlBuffer, matrix=self.matrix.aslist())

        self.input.obj = ctrlBuffer
        self.output.obj = ctrl

        self.controllers.append(ctrl)
        self.skinJoints.append(joint)
        self.rootDags.append(ctrlBuffer)

    def asdict(self):  # type: () -> dict
        data = super(RCtrlComponent, self).asdict()
        data['matrix'] = self.matrix
        data['ctrlNormal'] = self.ctrlNormal
        return data

    def asmirroreddict(self, mirrorAxis='x'):  # type: (basestring) -> dict
        data = super(RCtrlComponent, self).asmirroreddict()
        data['matrix'] = self.matrix.mirrored(mirrorAxis)
        data['ctrlNormal'] = self.ctrlNormal.mirrored(mirrorAxis)
        return data


class RBaseComponent(RMayaComponent):

    worldName = 'world'
    localName = 'local'

    defaultName = 'base'
    defaultCtrlNormal = RParam.Vector3(0.0, 1.0, 0.0)

    def __init__(self, **kwargs):
        super(RBaseComponent, self).__init__(**kwargs)

        self.worldOutput = rigBuilder.ROutput()
        self.localOutput = rigBuilder.ROutput()
        self.input = rigBuilder.RInput()

    def _doCreation(self):
        worldCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra=self.worldName, objType=self.controllerTypeStr),
            color=self.ctrlColor,
            normal=self.ctrlNormal,
            size=self.ctrlSize,
        )
        worldJoint = cmds.joint(name=self.composeObjName(nameExtra=self.worldName, objType=self.skinJointTypeStr))
        worldBuffer = RObj.createBuffer(worldCtrl)

        localCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra='local', objType=self.controllerTypeStr),
            color=self.ctrlColor + 100,
            normal=self.ctrlNormal,
            size=self.ctrlSize * .9,
        )
        localJoint = cmds.joint(name=self.composeObjName(nameExtra='local', objType=self.skinJointTypeStr))
        localBuffer = RObj.createBuffer(localCtrl)

        cmds.parent(localBuffer, worldCtrl)

        # self.inputs.append(worldBuffer)
        self.input.obj = worldBuffer

        self.rootDags.append(worldBuffer)

        self.controllers.append(worldCtrl)
        self.controllers.append(localCtrl)

        self.worldOutput.obj = worldCtrl
        self.localOutput.obj = localCtrl

        # self.outputs.append(worldCtrl)
        # self.outputs.append(localCtrl)

        self.skinJoints.append(worldJoint)
        self.skinJoints.append(localJoint)


class RMayaRig(rigBuilder.RBaseRig):
    defaultName = 'rig'

    def __init__(self, name=None):
        super(RMayaRig, self).__init__()
        self.name = str(name) if name is not None else self.defaultName
        self.folder = None

    def create(self):
        self.folder = cmds.group(empty=True, name=self.name)

        super(RMayaRig, self).create()

        for component in self.components:
            cmds.parent(component.folder, self.folder)


def test():
    cmds.file(new=True, force=True)

    # matrices
    ctrlMatrix = RParam.Matrix(
        px=10, py=10, pz=10,
        xx=0,  xy=0,  xz=-1,
        yx=0,  yy=1,  yz=0,
        zx=1,  zy=0,  zz=0
    )

    # instantiate the components
    baseComponent = RBaseComponent(ctrlSize=10)
    l_ctrlComp = RCtrlComponent(side=RCtrlComponent.leftSide, matrix=ctrlMatrix)

    connections = Connections()

    # register connections
    baseComponent.worldOutput.connect(l_ctrlComp.input)

    # r_ctrlComp = l_ctrlComp.mirrored()

    # Create the rig
    rig = RMayaRig()
    # rig.components += [baseComponent, l_ctrlComp, r_ctrlComp]
    rig.components += [baseComponent, l_ctrlComp]
    rig.create()

    # connections
    # r_ctrlComp.output.connect(baseComponent.input)
    # l_ctrlComp.output.connect(baseComponent.input)

    # clear sel
    cmds.select(clear=True)
