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
            xx=1.0, xy=0.0, xz=0.0, xw=0.0,
            yx=0.0, yy=1.0, yz=0.0, yw=0.0,
            zx=0.0, zy=0.0, zz=1.0, zw=0.0,
            px=0.0, py=0.0, pz=0.0, pw=1.0,
    ):
        self.xx = float(xx)
        self.xy = float(xy)
        self.xz = float(xz)
        self.xw = float(xw)

        self.yx = float(yx)
        self.yy = float(yy)
        self.yz = float(yz)
        self.yw = float(yw)

        self.zx = float(zx)
        self.zy = float(zy)
        self.zz = float(zz)
        self.zw = float(zw)

        self.px = float(px)
        self.py = float(py)
        self.pz = float(pz)
        self.pw = float(pw)

    def __repr__(self):
        return '<{}.{}: {}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.aslist(),
        )

    def __iter__(self):
        return iter(self.aslist())

    def aslist(self):
        return (
            self.xx,
            self.xy,
            self.xz,
            self.xw,
            self.yx,
            self.yy,
            self.yz,
            self.yw,
            self.zx,
            self.zy,
            self.zz,
            self.zw,
            self.px,
            self.py,
            self.pz,
            self.pw,
        )

    def rows(self):
        return (
            (self.xx, self.xy, self.xz, self.xw),
            (self.yx, self.yy, self.yz, self.yw),
            (self.zx, self.zy, self.zz, self.zw),
            (self.px, self.py, self.pz, self.pw),
        )

    def columns(self):
        return (
            (self.xx, self.yx, self.zx, self.px),
            (self.xy, self.yy, self.zy, self.py),
            (self.xz, self.yz, self.zz, self.pz),
            (self.xw, self.yw, self.zw, self.pw),
        )

    def copy(self):
        return self.__class__(*self.aslist())

    def mirrored(self, mirrorAxis='x'):  # type: (basestring) -> Matrix
        matrixCopy = self.copy()
        matrixCopy.mirror(mirrorAxis)
        return matrixCopy

    def mirror(self, mirrorAxis='x'):  # type: (basestring) -> None
        if mirrorAxis == 'x':
            self.xx *= -1
            self.yx *= -1
            self.zx *= -1
            self.px *= -1

        elif mirrorAxis == 'y':
            self.xy *= -1
            self.yy *= -1
            self.zy *= -1
            self.py *= -1

        elif mirrorAxis == 'z':
            self.xz *= -1
            self.yz *= -1
            self.zz *= -1
            self.pz *= -1

        else:
            raise ValueError('Unrecognized mirror axis -> {}'.format(mirrorAxis))

    def normalized(self):
        raise NotImplementedError

    def normalize(self):
        raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            newMatrix = list()
            for column in self.rows()[:3]:
                for row in other.columns()[:3]:
                    result = 0
                    for c, r in zip(column, row):
                        result += c * r
                    newMatrix.append(result)
                newMatrix.append(0.0)
            newMatrix.append(self.px + other.px)
            newMatrix.append(self.py + other.py)
            newMatrix.append(self.pz + other.pz)
            newMatrix.append(1.0)
            return self.__class__(*newMatrix)
        raise TypeError(
            'cannot do \'{}\' * \'{}\''.format(
                str(self.__class__),
                str(type(other)),
            )
        )


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
