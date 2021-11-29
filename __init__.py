from maya import cmds
from . import RData, RComp, RObj, RRig
import rigBuilder as RBuild


def test():
    import os

    class RMyRig(RRig.RBaseRig):

        def _doCreation(self):
            # Matrices
            ctrlMatrix = self.matrixData['ctrl']
            chainMatrices = self.matrixData['chain1'], self.matrixData['chain2'], self.matrixData['chain3']

            # Instantiate the components
            l_ctrlComp = RComp.RCtrlComponent(side=RComp.Config.leftSide, matrix=ctrlMatrix)
            r_ctrlComp = l_ctrlComp.mirrored()
            l_chainComp = RComp.RFkChainComponent(matrices=chainMatrices, side=RComp.Config.leftSide)
            r_chainComp = l_chainComp.mirrored()

            self.connections = [
                (self.baseComponent, 1, l_ctrlComp, 0),
                (self.baseComponent, 1, r_ctrlComp, 0),
                (l_ctrlComp, 0, l_chainComp, 0),
                (r_ctrlComp, 0, r_chainComp, 0),
            ]

            self.components += [
                l_ctrlComp,
                r_ctrlComp,
                l_chainComp,
                r_chainComp,
            ]

    # Matrix Data
    # Data path
    dataPath = r'C:\Users\plaurent\Desktop'

    # Fetch matrix data
    matrixDataPath = os.path.join(dataPath, r'matrix.json')
    matrixFile = RData.MatrixFile(matrixDataPath)
    matrixData = matrixFile.load()

    # # Import guides
    # matrixFile.import_()

    # Create myRig
    cmds.file(new=True, force=True)
    myRig = RMyRig(matrixData=matrixData)
    myRig.baseComponent.ctrlSize = 10.0
    myRig.create()
    cmds.select(clear=True)
