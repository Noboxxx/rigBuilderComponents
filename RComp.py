from maya import cmds
from . import RParam, RObj
import rigBuilder as RBuild


class Config(object):
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

    sideMirrorTable = {
        leftSide: rightSide,
        rightSide: leftSide,
        centerSide: None,
    }

    # colors
    leftColor = 0, 255, 0
    rightColor = 255, 0, 0
    centerColor = 255, 255, 0

    sideColorTable = {
        leftSide: leftColor,
        rightSide: rightColor,
        centerSide: centerColor,
    }


# Base #


class RMayaComponent(RBuild.RBaseComponent):

    # defaults
    defaultName = 'component'
    defaultSide = Config.centerSide
    defaultIndex = 0
    defaultCtrlSize = 1.0
    defaultCtrlNormal = 1.0, 0.0, 0.0
    defaultColor = 127, 127, 127

    def __init__(self, name=None, side=None, index=None, ctrlColor=None, ctrlSize=None, ctrlNormal=None):
        # type: (str, str, int, RParam.Color, float, RParam.Vector3) -> None
        super(RMayaComponent, self).__init__()

        # naming parameters
        self.name = str(RBuild.get(name, self.defaultName))
        self.side = str(RBuild.get(side, self.defaultSide))
        self.index = max(0, int(RBuild.get(index, self.defaultIndex)))

        # display parameters
        defaultColor = Config.sideColorTable.get(self.side, self.defaultColor)
        self.ctrlColor = RParam.Color(*RBuild.get(ctrlColor, defaultColor))
        self.ctrlSize = max(0.0, float(RBuild.get(ctrlSize, self.defaultCtrlSize)))
        self.ctrlNormal = RParam.Vector3(*RBuild.get(ctrlNormal, self.defaultCtrlNormal))

        # internal objects
        self.folder = None
        self.rootDags = list()
        self.skinJoints = list()

    def composeObjName(self, objType, nameExtra=None):
        name = '{}_{}'.format(self.name, nameExtra) if nameExtra is not None else self.name
        return Config.objNamePattern.format(
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
        data['side'] = Config.sideMirrorTable.get(data['side'], None)
        return data

    def _initializeCreation(self):
        folderName = self.composeObjName(Config.componentTypeStr)

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

    def create(self):
        self._initializeCreation()
        self._doCreation()
        self._finalizeCreation()


# Components #


class RCtrlComponent(RMayaComponent):

    defaultName = 'oneCtrl'
    defaultMatrix = RParam.Matrix()

    def __init__(self, matrix=None, **kwargs):
        # type: (RParam.Matrix, ...) -> None
        super(RCtrlComponent, self).__init__(**kwargs)

        self.matrix = RParam.Matrix(*RBuild.get(matrix, self.defaultMatrix))

    def _doCreation(self):
        ctrl = RObj.Controller.create(
            name=self.composeObjName(Config.controllerTypeStr),
            color=self.ctrlColor,
            normal=self.ctrlNormal,
            size=self.ctrlSize
        )
        joint = cmds.joint(name=self.composeObjName(Config.skinJointTypeStr))
        ctrlBuffer = RObj.createBuffer(ctrl)

        cmds.xform(ctrlBuffer, matrix=self.matrix.aslist())

        self.inputs.append(ctrlBuffer)
        self.outputs.append(ctrl)

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
    defaultCtrlNormal = 0.0, 1.0, 0.0

    def _doCreation(self):
        worldCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra=self.worldName, objType=Config.controllerTypeStr),
            color=self.ctrlColor,
            normal=self.ctrlNormal,
            size=self.ctrlSize,
        )
        worldJoint = cmds.joint(name=self.composeObjName(nameExtra=self.worldName, objType=Config.skinJointTypeStr))
        worldBuffer = RObj.createBuffer(worldCtrl)

        localCtrl = RObj.Controller.create(
            name=self.composeObjName(nameExtra='local', objType=Config.controllerTypeStr),
            color=self.ctrlColor + 100,
            normal=self.ctrlNormal,
            size=self.ctrlSize * .9,
        )
        localJoint = cmds.joint(name=self.composeObjName(nameExtra='local', objType=Config.skinJointTypeStr))
        localBuffer = RObj.createBuffer(localCtrl)

        cmds.parent(localBuffer, worldCtrl)

        self.inputs.append(worldBuffer)

        self.rootDags.append(worldBuffer)

        self.controllers.append(worldCtrl)
        self.controllers.append(localCtrl)

        self.outputs.append(worldCtrl)
        self.outputs.append(localCtrl)

        self.skinJoints.append(worldJoint)
        self.skinJoints.append(localJoint)


class RFkChainComponent(RMayaComponent):

    defaultName = 'fkChain'

    defaultMatrices = (
        (
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            1.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ),
        (
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            1.0, 0.0, 0.0, 0.0,
            0.0, 10.0, 0.0, 1.0
        ),
        (
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            1.0, 0.0, 0.0, 0.0,
            0.0, 20.0, 0.0, 1.0
        ),
    )

    def __init__(self, matrices=None, **kwargs):
        super(RFkChainComponent, self).__init__(**kwargs)

        self.matrices = [RParam.Matrix(*m) for m in RBuild.get(matrices, self.defaultMatrices)]

    def _doCreation(self):
        ctrls = list()
        for index, matrix in enumerate(self.matrices):
            ctrl = RObj.Controller.create(
                name=self.composeObjName(objType=Config.controllerTypeStr, nameExtra=index),
                color=self.ctrlColor,
                normal=self.ctrlNormal,
                size=self.ctrlSize,
            )
            skinJoint = cmds.joint(name=self.composeObjName(objType=Config.skinJointTypeStr, nameExtra=index))
            self.skinJoints.append(skinJoint)

            ctrlBuffer = RObj.createBuffer(ctrl)
            cmds.xform(ctrlBuffer, matrix=matrix.aslist())

            if index > 0:
                cmds.parent(ctrlBuffer, ctrls[-1])
            else:
                self.inputs.append(ctrlBuffer)
                self.rootDags.append(ctrlBuffer)
            ctrls.append(ctrl)

        self.controllers += ctrls
        self.outputs += ctrls

    def asdict(self):  # type: () -> dict
        data = super(RFkChainComponent, self).asdict()
        data['matrices'] = self.matrices
        return data

    def asmirroreddict(self, mirrorAxis='x'):  # type: (str) -> dict
        data = super(RFkChainComponent, self).asmirroreddict()
        matrices = data['matrices']
        data['matrices'] = [matrix.mirrored(mirrorAxis=mirrorAxis) for matrix in matrices]
        return data
