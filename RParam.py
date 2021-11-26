import math


class Position3(object):

    def __init__(self, x=0.0, y=0.0, z=0.0):  # type: (float, float, float) -> None
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self):
        return '<{}.{}: {}, {}, {}>'.format(self.__class__.__module__, self.__class__.__name__, self.x, self.y, self.z)

    def __iter__(self):
        return iter(self.aslist())

    def aslist(self):
        return [self.x, self.y, self.z]

    def copy(self):
        return self.__class__(self.x, self.y, self.z)

    def mirrored(self, mirrorAxis='x'):
        vectorCopy = self.copy()
        vectorCopy.mirror(mirrorAxis)
        return vectorCopy

    def mirror(self, mirrorAxis='x'):
        if mirrorAxis == 'x':
            self.x *= -1
        elif mirrorAxis == 'y':
            self.y *= -1
        elif mirrorAxis == 'z':
            self.z *= -1
        else:
            raise ValueError('Unrecognized axis -> {}'.format(mirrorAxis))


class Vector3(Position3):

    def __init__(self, x=0.0, y=0.0, z=0.0):
        super(Vector3, self).__init__(x, y, z)

        magnitude = self.magnitude()
        if magnitude <= 0.0:
            raise ValueError('magnitude is equal or less than 0.0 -> {}'.format(magnitude))

    def magnitude(self):
        return math.sqrt(self.x ** 2.0 + self.y ** 2.0 + self.z ** 2.0)

    def normalized(self):
        vectorCopy = self.copy()
        vectorCopy.normalize()
        return vectorCopy

    def normalize(self):
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude
        self.z /= magnitude


class Matrix(object):

    def __init__(
            self,
            vectorX=Vector3(1.0, 0.0, 0.0),
            vectorY=Vector3(0.0, 1.0, 0.0),
            vectorZ=Vector3(0.0, 0.0, 1.0),
            position=Position3(0.0, 0.0, 0.0),
    ):  # type: (Vector3, Vector3, Vector3, Position3) -> None
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

    def __iter__(self):
        return iter(
            (
                self.vectorX,
                self.vectorY,
                self.vectorZ,
                self.position,
            )
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

    def copy(self):
        return self.__class__(
            self.vectorX.copy(),
            self.vectorY.copy(),
            self.vectorZ.copy(),
            self.position.copy()
        )

    def mirrored(self, mirrorAxis='x'):  # type: (basestring) -> Matrix
        matrixCopy = self.copy()
        matrixCopy.mirror(mirrorAxis)
        return matrixCopy

    def mirror(self, mirrorAxis='x'):  # type: (basestring) -> None
        self.vectorX = self.vectorX.mirrored(mirrorAxis)
        self.vectorY = self.vectorY.mirrored(mirrorAxis)
        self.vectorZ = self.vectorZ.mirrored(mirrorAxis)
        self.position = self.position.mirrored(mirrorAxis)

    def normalized(self):
        matrixCopy = self.copy()
        matrixCopy.normalize()
        return matrixCopy

    def normalize(self):
        self.vectorX = self.vectorX.normalized()
        self.vectorY = self.vectorY.normalized()
        self.vectorZ = self.vectorZ.normalized()


class Color(object):

    @classmethod
    def clamp(cls, mini, value, maxi):
        return max(mini, min(maxi, value))

    def __init__(self, r, g, b):
        self.r = self.clamp(0, int(r), 255)
        self.g = self.clamp(0, int(g), 255)
        self.b = self.clamp(0, int(b), 255)

    def aslist(self):
        return [self.r, self.g, self.b]

    def __iter__(self):
        return iter(self.aslist())

    def __add__(self, other):
        return self._operation(other, '+')

    def __mul__(self, other):
        return self._operation(other, '*')

    def __div__(self, other):
        return self._operation(other, '/')

    def __sub__(self, other):
        return self._operation(other, '-')

    def _operation(self, other, operator):
        if isinstance(other, (int, float, long)):
            r = eval('self.r {} other'.format(operator))
            g = eval('self.g {} other'.format(operator))
            b = eval('self.b {} other'.format(operator))
            return self.__class__(r, g, b)
        elif isinstance(other, Color):
            r = eval('self.r {} other.r'.format(operator))
            g = eval('self.g {} other.g'.format(operator))
            b = eval('self.b {} other.b'.format(operator))
            return self.__class__(r, g, b)
        raise TypeError(
            'cannot do \'{}\' {} \'{}\''.format(
                str(self.__class__),
                operator,
                str(type(other)),
            )
        )
