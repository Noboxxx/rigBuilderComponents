import rigBuilder
from maya import cmds
from . import RParam, RObj


class RMayaComponent(rigBuilder.RBaseComponent):
    folderNamePattern = '{name}_{side}_{index}_{shortType}'

    def __init__(
            self,
            name='untitled',
            side=RParam.centerSide,
            index=RParam.Index(0),
            color=None,
            size=1.0,
    ):
        # type: (str, RParam.Side, RParam.Index, RParam.Color or None, float) -> None
        super(RMayaComponent, self).__init__()

        # naming parameters
        self.name = name
        self.side = side
        self.index = index

        # display parameters
        self.color = color if color is not None else RParam.sideColorTable[side]
        self.size = size

        # internal objects
        self.folder = None
        self.rootDags = list()
        self.skinJoints = list()

    def composeObjName(self, shortType, nameExtra=None):
        name = '{}_{}'.format(self.name, nameExtra) if nameExtra else self.name
        return self.folderNamePattern.format(
            name=name,
            side=self.side,
            index=self.index,
            shortType=shortType
        )

    def asdict(self):  # type: () -> dict
        data = super(RMayaComponent, self).asdict()
        data['name'] = self.name
        data['side'] = self.side
        data['index'] = self.index
        return data

    def asmirroreddict(self):  # type: () -> dict
        data = super(RMayaComponent, self).asmirroreddict()
        data['side'] = RParam.sideMirrorTable.get(data['side'], None)
        return data

    def _initializeCreation(self):
        folderName = self.composeObjName(RParam.ShortType.component)

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


class ROneCtrl(RMayaComponent):

    def __init__(self, matrix=RParam.Matrix(), **kwargs):  # type: (RParam.Matrix, ...) -> None
        self.matrix = matrix
        super(ROneCtrl, self).__init__(**kwargs)

    def _doCreation(self):
        ctrl = RObj.Controller.create(
            name=self.composeObjName(RParam.ShortType.ctrl),
            color=self.color
        )
        ctrlBuffer = cmds.group(empty=True)
        joint = cmds.joint(name=self.composeObjName(RParam.ShortType.skinJoint))
        cmds.parent(ctrl, ctrlBuffer)
        cmds.parent(joint, ctrl)

        cmds.xform(ctrlBuffer, matrix=self.matrix.aslist())

        self.controllers.append(ctrl)
        self.skinJoints.append(joint)
        self.outputs.append(joint)
        self.inputs.append(ctrlBuffer)
        self.rootDags.append(ctrlBuffer)

    def asdict(self):  # type: () -> dict
        data = super(ROneCtrl, self).asdict()
        data['matrix'] = self.matrix
        return data

    def asmirroreddict(self, mirrorAxis=RParam.xAxis):  # type: (RParam.Axis) -> dict
        data = super(ROneCtrl, self).asmirroreddict()
        data['matrix'] = self.matrix.mirror(mirrorAxis)
        return data


def test():
    from . import RParam, RObj
    reload(RParam)
    reload(RObj)

    cmds.file(new=True, force=True)

    # Instantiate the components
    component = ROneCtrl(
        side=RParam.leftSide,
        matrix=RParam.Matrix(position=RParam.Vector3(10, 10, 10)),
    )
    mirroredComponent = component.mirror(RParam.xAxis)

    #
    print component
    print mirroredComponent

    # Create the components
    component.create()
    mirroredComponent.create()

    cmds.select(clear=True)
