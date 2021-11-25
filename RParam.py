import math


class ShortType(object):

    skinJoint = 'skn'
    ctrl = 'ctl'
    component = 'cmp'


class Side(object):

    def __init__(self, name):
        self.name = str(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}.{}: {}>'.format(self.__class__.__module__, self.__class__.__name__, self.name)


leftSide = Side('L')
rightSide = Side('R')
centerSide = Side('C')

sideMirrorTable = {
    leftSide: rightSide,
    rightSide: leftSide,
    centerSide: None
}


class Axis(object):

    def __init__(self, name):
        self.name = str(name)

    def __eq__(self, other):
        if isinstance(self, Axis):
            return self.name == other.name
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}.{}: {}>'.format(self.__class__.__module__, self.__class__.__name__, self.name)


xAxis = Axis('x')
yAxis = Axis('y')
zAxis = Axis('z')


class Index(object):

    def __init__(self, value):  # type: (int) -> None
        value = int(value)

        if value < 0:
            raise ValueError('Index should be positive -> {}'.format(value))

        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '<{}.{}: {}>'.format(self.__class__.__module__, self.__class__.__name__, self.value)


class Vector3(object):

    def __init__(self, x=0.0, y=0.0, z=0.0):  # type: (float, float, float) -> None
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self):
        return '<{}.{}: {}, {}, {}>'.format(self.__class__.__module__, self.__class__.__name__, self.x, self.y, self.z)

    def aslist(self):
        return [self.x, self.y, self.z]

    def magnitude(self):
        return math.sqrt(self.x ** 2.0 + self.y ** 2.0 + self.z ** 2.0)


class Matrix(object):

    def __init__(
            self,
            vectorX=Vector3(1.0, 0.0, 0.0),
            vectorY=Vector3(0.0, 1.0, 0.0),
            vectorZ=Vector3(0.0, 0.0, 1.0),
            position=Vector3(0.0, 0.0, 0.0),
    ):  # type: (Vector3, Vector3, Vector3, Vector3) -> None
        self.vectorX = vectorX
        self.vectorY = vectorY
        self.vectorZ = vectorZ
        self.position = position

    def __repr__(self):
        return '<{}.{}: {}, {}, {}, {}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.vectorX,
            self.vectorY,
            self.vectorZ,
            self.position
        )

    def aslist(self):
        ls = self.vectorX.aslist()
        ls.append(0.0)
        ls += self.vectorY.aslist()
        ls.append(0.0)
        ls += self.vectorZ.aslist()
        ls.append(0.0)
        ls += self.position.aslist()
        ls.append(1.0)
        return ls

    def mirror(self, mirrorAxis=xAxis):  # type: (Axis) -> Matrix
        vectorP = Vector3(*self.position.aslist())
        if mirrorAxis == xAxis:
            vectorP.x *= -1
        elif mirrorAxis == yAxis:
            vectorP.y *= -1
        elif mirrorAxis == zAxis:
            vectorP.z *= -1

        print vectorP
        return self.__class__(
            self.vectorX,
            self.vectorY,
            self.vectorZ,
            vectorP,
        )


class Color(object):

    def __init__(self, r, g, b):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)

    def aslist(self):
        return [
            self.r,
            self.g,
            self.b,
        ]


defaultColor = Color(0, 0, 255)

centerColor = Color(255, 255, 0)
leftColor = Color(0, 255, 0)
rightColor = Color(255, 0, 0)

sideColorTable = {
    leftSide: leftColor,
    rightSide: rightColor,
    centerSide: centerColor,
}