from maya import cmds
from . import RData, RComp, RObj, RRig
import rigBuilder as RBuild


def test():
    import os

    # Matrix Data
    # Data path
    dataPath = r'C:\Users\plaurent\Desktop'

    # Fetch matrix data
    matrixDataPath = os.path.join(dataPath, r'matrix.json')
    matrixFile = RData.MatrixFile(matrixDataPath)
    matrixData = matrixFile.load()

    # # Import guides
    matrixFile.import_()

    # Matrices
    ctrlMatrix = matrixData['ctrl']
    chainMatrices = matrixData['chain1'], matrixData['chain2'], matrixData['chain3']

    # Instantiate the components
    baseComponent = RComp.RBaseComponent(ctrlSize=10.0)

    l_ctrlComp = RComp.RCtrlComponent(side=RComp.Config.leftSide, matrix=ctrlMatrix)
    r_ctrlComp = l_ctrlComp.mirrored()

    l_chainComp = RComp.RFkChainComponent(matrices=chainMatrices, side=RComp.Config.leftSide)
    r_chainComp = l_chainComp.mirrored()

    # Connections
    connections = [
        (baseComponent, 'worldOutput', l_ctrlComp, 'input'),
        (baseComponent, 'worldOutput', r_ctrlComp, 'input'),
        (l_ctrlComp, 'output', l_chainComp, 'input'),
        (r_ctrlComp, 'output', r_chainComp, 'input'),
    ]

    RObj.createMatrixConstraint((baseComponent.outputs[1],), l_ctrlComp.inputs[0])
    RObj.createMatrixConstraint((baseComponent.outputs[1],), r_ctrlComp.inputs[0])
    RObj.createMatrixConstraint((r_ctrlComp.outputs[0],), r_ctrlComp.inputs[0])

    components = [
        baseComponent,
        l_ctrlComp,
        r_ctrlComp,
        l_chainComp,
        r_chainComp,
    ]

    # Create myRig
    cmds.file(new=True, force=True)
    myRig = RRig.RRig(components=components, connections=connections)
    myRig.create()
    cmds.select(clear=True)
