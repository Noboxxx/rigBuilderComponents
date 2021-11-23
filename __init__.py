import rigBuilder
from maya import cmds

# Parameters #


class ShortType(object):

    skinJoint = 'skn'
    joint = 'jnt'
    ctrl = 'ctl'
    ctrlBuffer = 'ctrlBuffer'
    buffer = 'rst'
    component = 'cmp'


class Side(object):

    left = 'L'
    right = 'R'
    center = 'C'

    mirrorTable = {
        left: right,
        right: left,
        center: None,
    }

    def __init__(self, name):
        name = str(name)

        if name not in self.mirrorTable.keys():
            raise ValueError('name not in {} -> {}'.format(self.mirrorTable.keys(), name))

        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return repr(self.name)

    def __mirror__(self):  # type: () -> None or Side
        return self.__class__(self.mirrorTable[self.name])


class Index(object):

    def __init__(self, value):
        value = int(value)

        if value < 0:
            raise ValueError('Index should be positive -> {}'.format(value))

        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)


class Vector(object):

    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def aslist(self):
        return [self.x, self.y, self.z, self.w]


class Matrix(object):

    def __init__(
            self,
            vectorX=Vector(1.0, 0.0, 0.0, 0.0),
            vectorY=Vector(0.0, 1.0, 0.0, 0.0),
            vectorZ=Vector(0.0, 0.0, 1.0, 0.0),
            vectorP=Vector(0.0, 0.0, 0.0, 1.0),
            mirrorAxis='x'
    ):
        self.vectorX = vectorX
        self.vectorY = vectorY
        self.vectorZ = vectorZ
        self.vectorP = vectorP

        self.mirrorAxis = mirrorAxis

    def aslist(self):
        return self.vectorX.aslist() + self.vectorY.aslist() + self.vectorZ.aslist() + self.vectorP.aslist()

    def __mirror__(self):
        vectorP = Vector(*self.vectorP.aslist())
        vectorP.x *= -1
        return self.__class__(
            self.vectorX,
            self.vectorY,
            self.vectorZ,
            vectorP,
            self.mirrorAxis
        )


# Components #


class RMayaComponent(rigBuilder.RBaseComponent):
    folderNamePattern = '{name}_{side}_{index}_{shortType}'

    def __init__(self, name='untitled', side=Side('C'), index=Index(0)):  # type: (str, Side, Index) -> None
        super(RMayaComponent, self).__init__()

        self.name = name
        self.side = side
        self.index = index

        self.folder = None
        self.rootDags = list()
        self.skinJoints = list()

    def composeName(self, shortType, nameExtra=None):
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

    def _initializeCreation(self):
        folderName = self.composeName(ShortType.component)

        if cmds.objExists(folderName):
            raise RuntimeError('Component already exists -> {}'.format(folderName))

        self.folder = cmds.group(empty=True, name=folderName)

    def _doCreation(self):
        pass

    def _finalizeCreation(self):
        if self.rootDags:
            cmds.parent(self.rootDags, self.folder)

    def create(self):  # type: () -> None
        self._initializeCreation()
        self._doCreation()
        self._finalizeCreation()


class ROneCtrl(RMayaComponent):

    def __init__(self, matrix=Matrix(), **kwargs):
        self.matrix = matrix
        super(ROneCtrl, self).__init__(**kwargs)

    def _doCreation(self):
        ctrl, = cmds.circle(constructionHistory=False, name=self.composeName(ShortType.ctrl))
        ctrlBuffer = cmds.group(empty=True, name=self.composeName(ShortType.ctrlBuffer))
        joint = cmds.joint(name=self.composeName(ShortType.joint))
        cmds.parent(ctrl, ctrlBuffer)
        cmds.parent(joint, ctrl)

        print self.matrix
        cmds.xform(ctrlBuffer, matrix=self.matrix.aslist())

        self.skinJoints.append(joint)
        self.rootDags.append(ctrlBuffer)

    def asdict(self):  # type: () -> dict
        data = super(ROneCtrl, self).asdict()
        data['matrix'] = self.matrix
        return data


def test():

    cmds.file(new=True, force=True)

    # Instantiate the components
    component = ROneCtrl(side=Side('L'), matrix=Matrix(vectorP=Vector(10, 10, 10)))
    mirroredComponent = rigBuilder.mirror(component)

    #
    print component
    print mirroredComponent

    # Create the components
    component.create()
    mirroredComponent.create()
