# -*- coding: utf-8 -*-

import numpy as np
from control.SLM import slmpy
# import control.instruments as instruments
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from control.SLM import Mask
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.dockarea import Dock, DockArea
import pickle

# Width and height of the SLM which can change from one device to another:
m = 600
n = 792


class slmWidget(QtGui.QFrame):
    """Class creating a GUI to control the phase pattern displayed by the SLM.
    In this version, it is optimized to display and address 2 masks
    independently. The whole image is separated in two: one left part and
    right part. One part is selected at a time and can be controlled with the
    arrows from *ArrowsControl*. :param SLMdisplay slm: instance of a second
    monitor generated via slmpy. Communication with the SLM is initiated when
    Tempesta is started along with all other instruments."""
    def __init__(self, slm, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the parameters from the tree
        self.tree = SLMParamTree()
        self.treeAber = SLMParamTreeAber()
        self.RPar = self.tree.p.child("R")
        self.sigmaPar = self.tree.p.param("sigma")
        self.anglePar = self.tree.p.param("angle")
        self.lbdPar = self.tree.p.param('lambda depletion: (nm)')
        self.helix_rotPar = self.tree.p.param("helix clock rotation")

        # Get the parameters from the tree - for aberrations for D and TH
        self.d_aber_factors, self.th_aber_factors = self.treeAber.get_aber_factors()

        self.slm = slm
        self.maskMask = Mask.Helix_Hat(m, n, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value())
        self.maskAber = Mask.Aberrations(m, n, self.lbdPar.value(),
                                         self.RPar.value(),
                                         self.sigmaPar.value(),
                                         self.d_aber_factors,
                                         self.th_aber_factors)

        self.maskMask.tilt(self.anglePar.value())
        self.mask = self.maskMask + self.maskAber
        self.left_center = (0, 0)
        self.right_center = (0, 0)

        self.gaussiansBool = False

        # Indicates wether each side of the mask is actually displaying
        # a mask or not
        self.black_left = False
        self.black_right = False

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)

        self.updateButton = QtGui.QPushButton('Update')
        self.updateButton.setCheckable(True)
        self.updateButton.clicked.connect(self.update)
        self.updateButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                        QtGui.QSizePolicy.Expanding)

        self.applyPar = self.tree.p.param('Apply')
        self.applyPar.sigStateChanged.connect(self.apply)
        self.applyAberPar = self.treeAber.p.param('Apply')
        self.applyAberPar.sigStateChanged.connect(self.apply)

        # Widget displaying the phase pattern displayed on the SLM
        imageWidget = pg.GraphicsLayoutWidget()
        self.vb = imageWidget.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        image = self.mask.img
        image = np.fliplr(image.transpose())
        self.img.setImage(image, autoLevels=False, autoDownsample=True,
                          autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
#        print(self.mask)
#        print(self.slm)
        self.slm.updateArray(self.mask)

        self.arrowsModule = ArrowsControl()

        # Link between the buttons in the arrow module and the functions to
        # control the SLM
        self.arrowsModule.upButton.clicked.connect(self.upClicked)
        self.arrowsModule.downButton.clicked.connect(self.downClicked)
        self.arrowsModule.leftButton.clicked.connect(self.leftClicked)
        self.arrowsModule.rightButton.clicked.connect(self.rightClicked)
        self.arrowsModule.saveButton.clicked.connect(self.saveParam)
        self.arrowsModule.loadButton.clicked.connect(self.loadParam)
        self.arrowsModule.blackButton.clicked.connect(self.setBlack)
        self.arrowsModule.gaussiansButton.clicked.connect(self.setGaussians)
        self.arrowsModule.halfButton.clicked.connect(self.setHalf)
        self.arrowsModule.quadrantButton.clicked.connect(self.setQuadrant)
        self.arrowsModule.hexButton.clicked.connect(self.setHex)
        self.arrowsModule.splitbullButton.clicked.connect(self.setSplit)

        # GUI layout
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        # Dock widget
        dock_area = DockArea()

        # Laser Widget
        paramtree_dock = Dock("Parameter tree", size=(400, 400))
        paramtree_dock.addWidget(self.tree)
        paramtree_aberr_dock = Dock("Parameter tree aberrations", size=(400, 400))
        paramtree_aberr_dock.addWidget(self.treeAber)
        dock_area.addDock(paramtree_dock)
        dock_area.addDock(paramtree_aberr_dock, "above", paramtree_dock)

        grid.addWidget(dock_area, 0, 0, 2, 2)
        grid.addWidget(imageWidget, 0, 2, 1, 3)
#        grid.addWidget(self.treeAber, 1, 0, 1, 1)
#        grid.addWidget(self.tree, 2, 0, 1, 1)
        grid.addWidget(self.arrowsModule, 1, 2, 1, 3)

#        grid.setColumnMinimumWidth(1, 50)
#        grid.setColumnMinimumWidth(0, 50)
#        grid.setRowMinimumHeight(0, 200)
#        grid.setRowMinimumHeight(1, 200)
#        grid.setRowMinimumHeight(2, 50)

    def upClicked(self):
        """Moves the current Mask up"""
        self.moveMask(-1 * self.arrowsModule.increment.value(), 0)

    def downClicked(self):
        """Moves the current Mask down"""
        self.moveMask(self.arrowsModule.increment.value(), 0)

    def leftClicked(self):
        """Moves the current Mask left"""
        self.moveMask(0, -1 * self.arrowsModule.increment.value())

    def rightClicked(self):
        """Moves the current Mask right"""
        self.moveMask(0, self.arrowsModule.increment.value())

    def moveMask(self, x, y):
        """Sends instruction to both the SLM and the display to move the
        corresponding mask when one arrow is pressed.
        :param int x: new x position of the center of the Mask
        :param int y: new y position of the center of the Mask"""

        if(str(self.arrowsModule.maskMenu.currentText()) == "Donut"):
            self.maskMask.moveLeft(x, y)
            self.maskAber.moveLeft(x, y)
        elif(str(self.arrowsModule.maskMenu.currentText()) == "Top hat"):
            self.maskMask.moveRight(x, y)
            self.maskAber.moveRight(x, y)
        else:
            print("Error: Name of mask does not exist.")
        self.maskMask.update()
        self.maskAber.update()
        self.update()


        ### I AM HERE ###


    def setBlack(self):
        """Sets the current mask to a black (null phase) Mask.
        Useful to check the masks one by one"""
        if(str(self.arrowsModule.maskMenu.currentText()) == "Donut"):
            self.maskMask.left.setBlack()
            self.maskAber.left.setBlack()
            self.black_left = True
        elif(str(self.arrowsModule.maskMenu.currentText()) == "Top hat"):
            self.maskMask.right.setBlack()
            self.maskAber.right.setBlack()
            self.black_right = True
        else:
            print("Error: Name of mask does not exist.")
        self.maskMask.update()
        self.maskAber.update()
        self.update()

    def setGaussians(self):
        """Sets the current masks to Gaussian masks, with the same center.
        Useful for alignment."""
        self.gaussiansBool = True
        self.maskMask = Mask.Gaussians(m, n, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value(),
                                       self.left_center,
                                       self.right_center)
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def setHalf(self):
        """Sets the current masks to half masks, with the same center,
        for accurate center position determination."""
        self.maskMask = Mask.Half(m, n, self.lbdPar.value(),
                                  self.RPar.value(),
                                  self.sigmaPar.value(),
                                  self.left_center,
                                  self.right_center,
                                  np.float(self.arrowsModule.rotAngEdit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def setQuadrant(self):
        """Sets the current masks to quadrant masks, with the same center,
        for astigmatism aberration determination."""
        self.maskMask = Mask.Quad(m, n, self.lbdPar.value(),
                                  self.RPar.value(),
                                  self.sigmaPar.value(),
                                  self.left_center,
                                  self.right_center,
                                  np.float(self.arrowsModule.rotAngEdit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def setHex(self):
        """Sets the current masks to hexagonal masks, with the same center,
        for trefoil aberration determination."""
        self.maskMask = Mask.Hex(m, n, self.lbdPar.value(),
                                 self.RPar.value(),
                                 self.sigmaPar.value(),
                                 self.left_center,
                                 self.right_center,
                                 np.float(self.arrowsModule.rotAngEdit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def setSplit(self):
        """Sets the current masks to split bullseye masks, with the same
        center, for coma aberration determination."""
        self.maskMask = Mask.Split(m, n, self.lbdPar.value(),
                                   self.RPar.value(),
                                   self.sigmaPar.value(),
                                   self.left_center,
                                   self.right_center,
                                   np.float(self.arrowsModule.rotAngEdit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def apply(self):
        """Applies a configuration to the SLM and changes the mask displayed"""
        self.d_aber_factors, self.th_aber_factors = self.treeAber.get_aber_factors()

        if self.gaussiansBool:
            self.maskMask = Mask.Gaussians(m, n, self.lbdPar.value(),
                                           self.RPar.value(),
                                           self.sigmaPar.value(),
                                           left_pos=self.left_center,
                                           right_pos=self.right_center)
        else:
            self.maskMask = Mask.Helix_Hat(m, n, self.lbdPar.value(),
                                           self.RPar.value(),
                                           self.sigmaPar.value(),
                                           self.left_center,
                                           self.right_center,
                                           self.helix_rotPar.value())
        self.maskMask.tilt(self.anglePar.value())
        self.maskAber = Mask.Aberrations(m, n, self.lbdPar.value(),
                                         self.RPar.value(),
                                         self.sigmaPar.value(),
                                         self.d_aber_factors,
                                         self.th_aber_factors,
                                         self.left_center,
                                         self.right_center,
                                         self.helix_rotPar.value())

        self.update()

    def update(self):
        """When any parameter changes, sends the new image to the SLM and the
        display."""
        # Changing the orientation of image so they have the same orientation
        # on the slm and on the screen
        self.left_center = self.maskMask.left_center
        self.right_center = self.maskMask.right_center
        print('wait4')
        self.mask = self.maskMask + self.maskAber
        print('wait5')
        image = self.mask.img.transpose()
        image = np.fliplr(image)
        self.img.setImage(image, autoLevels=False, autoDownsample=False)
        self.slm.updateArray(self.mask)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)

    def saveParam(self):
        """Saves the current SLM configuration, in particular the position of
        the Masks. The informations are stored in a file 'informations.bbn'
        (arbitrary extension) with the module pickle. Separate files are
        saved depending on if you use the glycerol or oil objective."""
        state = self.tree.p.saveState()
        mask_state = {"left_center": self.maskMask.left_center,
                      "right_center": self.maskMask.right_center}
        stateAber = self.treeAber.p.saveState()

        if(str(self.arrowsModule.objlensMenu.currentText()) == "Oil"):
            with open("informationsOil.bbn", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(state)
                pickler.dump(mask_state)
            with open("informationsAberOil.bbn", "wb") as fAber:
                pickler = pickle.Pickler(fAber)
                pickler.dump(stateAber)
        elif(str(self.arrowsModule.objlensMenu.currentText()) == "Glycerol"):
            with open("informationsGlyc.bbn", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(state)
                pickler.dump(mask_state)
            with open("informationsAberGlyc.bbn", "wb") as fAber:
                pickler = pickle.Pickler(fAber)
                pickler.dump(stateAber)
        elif(str(self.arrowsModule.objlensMenu.currentText()) == "No objective"):
            print('You have to choose an objective in the drop down menu!')

        print("Saved all parameters...")
        return

    def loadParam(self):
        """Loads the parameters from a previous configuration. Depending on
        which objective is in use, load different parameter files."""
        self.gaussiansBool = False

        if(str(self.arrowsModule.objlensMenu.currentText()) == "Oil"):
            with open('informationsOil.bbn', 'rb') as f:
                depickler = pickle.Unpickler(f)
                state = depickler.load()
                mask_state = depickler.load()
            with open('informationsAberOil.bbn', 'rb') as fAber:
                depickler = pickle.Unpickler(fAber)
                stateAber = depickler.load()
        elif(str(self.arrowsModule.objlensMenu.currentText()) == "Glycerol"):
            with open('informationsGlyc.bbn', 'rb') as f:
                depickler = pickle.Unpickler(f)
                state = depickler.load()
                mask_state = depickler.load()
            with open('informationsAberGlyc.bbn', 'rb') as fAber:
                depickler = pickle.Unpickler(fAber)
                stateAber = depickler.load()
        elif(str(self.arrowsModule.objlensMenu.currentText()) == "No objective"):
            print('You have to choose an objective in the drop down menu!')
            return

        self.tree.p.restoreState(state)
        print("Load mask centers:", mask_state)
        self.treeAber.p.restoreState(stateAber)
        self.d_aber_factors, self.th_aber_factors = self.treeAber.get_aber_factors()

        self.left_center = mask_state["left_center"]
        self.right_center = mask_state["right_center"]

        self.maskMask = Mask.Helix_Hat(m, n, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value(),
                                       left_pos=self.left_center,
                                       right_pos=self.right_center)
        self.maskMask.tilt(self.anglePar.value())
        self.maskAber = Mask.Aberrations(m, n, self.lbdPar.value(),
                                         self.RPar.value(),
                                         self.sigmaPar.value(),
                                         self.d_aber_factors,
                                         self.th_aber_factors,
                                         left_pos=self.left_center,
                                         right_pos=self.right_center)
        print('wait')
        self.update()
        print("Loaded all parameters.")


class SLMParamTree(ParameterTree):
    """ Parameter Tree containing the different parameters for the SLM's
    phase masks. These parameters are:
    R (int): radius of circular phase masks, in pixels
    sigma (float): std of the incident gaussian beam, to determine the inner
                    radius of a top-hat phase mask, in pixels.
    angle (float): in an off-axis configuration.
    lambda depletion (nm): the wavelength incident on the SLM.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        params = [
                  {'name': 'R', 'type': 'int', 'value': 100, 'limits': (0, 600)},
                  {'name': 'sigma', 'type': 'float', 'value': 35, 'limits': (0.001, 10**6)},
                  {'name': 'angle', 'type': 'float', 'value': 0.15, 'limits': (0, 0.3)},
                  {'name': 'lambda depletion: (nm)', 'type': 'int', 'value': 775, 'limits': (0, 1200)},
                  {'name': 'helix clock rotation', 'type': 'bool', 'value': True},
                  {'name': 'Apply', 'type': 'action'}
                  ]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True


class SLMParamTreeAber(ParameterTree):
    """ Parameter Tree containing the different parameters for the SLM's
    phase masks. These parameters are:
    Radius (int): of circular phase masks, in pixels
    sigma (float): std of the incident gaussian beam, to determine the inner
                    radius of a top-hat phase mask, in pixels.
    angle (float): in an off-axis configuration.
    lambda depletion (nm): the wavelength incident on the SLM.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lim = 2
        params = [
            {'name': 'D Tilt', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Tip', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Defocus', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Spherical', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Vertical coma', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Horizontal coma', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Vertical astigmatism', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Oblique astigmatism', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Vertical trefoil', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'D Oblique trefoil', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Tilt', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Tip', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Defocus', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Spherical', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Vertical coma', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Horizontal coma', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Vertical astigmatism', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Oblique astigmatism', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Vertical trefoil', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'TH Oblique trefoil', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
            {'name': 'Apply', 'type': 'action'}
            ]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True

    def get_aber_factors(self):
        """Returns the aberration factors in the aberration tree to two np.arrays."""
        # pylint: disable-msg=too-many-locals
        f_d_tilt = self.p.param("D Tilt").value()
        f_d_tip = self.p.param("D Tip").value()
        f_d_defoc = self.p.param("D Defocus").value()
        f_d_sph = self.p.param("D Spherical").value()
        f_d_vert_coma = self.p.param("D Vertical coma").value()
        f_d_hoz_coma = self.p.param("D Horizontal coma").value()
        f_d_vert_ast = self.p.param("D Vertical astigmatism").value()
        f_d_obl_ast = self.p.param("D Oblique astigmatism").value()
        f_d_vert_trefoil = self.p.param("D Vertical trefoil").value()
        f_d_obl_trefoil = self.p.param("D Oblique trefoil").value()

        f_th_tilt = self.p.param("TH Tilt").value()
        f_th_tip = self.p.param("TH Tip").value()
        f_th_defoc = self.p.param("TH Defocus").value()
        f_th_sph = self.p.param("TH Spherical").value()
        f_th_vert_coma = self.p.param("TH Vertical coma").value()
        f_th_hoz_coma = self.p.param("TH Horizontal coma").value()
        f_th_vert_ast = self.p.param("TH Vertical astigmatism").value()
        f_th_obl_ast = self.p.param("TH Oblique astigmatism").value()
        f_th_vert_trefoil = self.p.param("TH Vertical trefoil").value()
        f_th_obl_trefoil = self.p.param("TH Oblique trefoil").value()

        d_aber_factors = np.array([f_d_tilt, f_d_tip, f_d_defoc, f_d_sph, f_d_vert_coma, f_d_hoz_coma,
                                   f_d_vert_ast, f_d_obl_ast, f_d_vert_trefoil, f_d_obl_trefoil])
        th_aber_factors = np.array([f_th_tilt, f_th_tip, f_th_defoc, f_th_sph, f_th_vert_coma, f_th_hoz_coma,
                                    f_th_vert_ast, f_th_obl_ast, f_th_vert_trefoil, f_th_obl_trefoil])
        return d_aber_factors, th_aber_factors


class ArrowsControl(QtGui.QFrame):
    """This widget creates four buttons able to move a circular phase mask
    with a tunable number of pixels. Useful to align the phase mask with the
    incident beam without touching any optics."""
    def __init__(self, *args, **kwargs):
        # Definition of the Widget to choose left or right part of the Mask
        super().__init__(*args, **kwargs)
        self.chooseInterface = QtGui.QWidget()
        self.chooseInterface_layout = QtGui.QGridLayout()
        self.chooseInterface.setLayout(self.chooseInterface_layout)

        # Choose which mask to modify
        self.maskMenu = QtGui.QComboBox()
        self.maskMenu.addItem("Donut")
        self.maskMenu.addItem("Top hat")
        self.chooseInterface_layout.addWidget(QtGui.QLabel('Select part of the mask:'), 0, 0)
        self.chooseInterface_layout.addWidget(self.maskMenu, 0, 1)

        # Choose which objective is in use
        self.objlensMenu = QtGui.QComboBox()
        self.objlensMenu.addItem("No objective")
        self.objlensMenu.addItem("Oil")
        self.objlensMenu.addItem("Glycerol")
        self.chooseInterface_layout.addWidget(QtGui.QLabel('Select which objective is used:'), 1, 0)
        self.chooseInterface_layout.addWidget(self.objlensMenu, 1, 1)

        # Defining the part with only the arrows themselves
        self.arrows = QtGui.QFrame()
        self.arrow_layout = QtGui.QGridLayout()
        self.arrows.setLayout(self.arrow_layout)

        self.upButton = QtGui.QPushButton('Up (YZ)')
        self.upButton.setCheckable(False)
        self.upButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                    QtGui.QSizePolicy.Expanding)
        self.upButton.setFixedSize(self.upButton.sizeHint())

        self.downButton = QtGui.QPushButton('Down (YZ)')
        self.downButton.setCheckable(False)
        self.downButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        self.downButton.setFixedSize(self.upButton.sizeHint())

        self.leftButton = QtGui.QPushButton('Left (XZ)')
        self.leftButton.setCheckable(False)
        self.leftButton.setFixedSize(self.upButton.sizeHint())

        self.rightButton = QtGui.QPushButton('Right (XZ)')
        self.rightButton.setCheckable(False)
        self.rightButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Expanding)
        self.rightButton.setFixedSize(self.upButton.sizeHint())

        # Widget to change the amount of deplacement induced by the arrows
        self.incrementWidget = QtGui.QWidget()
        self.incrementLayout = QtGui.QVBoxLayout()
        self.incrementWidget.setLayout(self.incrementLayout)

        label = QtGui.QLabel()
        label.setText("Move (px)")
        self.increment = QtGui.QSpinBox()
        self.increment.setRange(1, 500)
        self.increment.setValue(1)
        self.incrementLayout.addWidget(label)
        self.incrementLayout.addWidget(self.increment)

        self.saveButton = QtGui.QPushButton("Save")
        self.loadButton = QtGui.QPushButton("Load")

        self.blackButton = QtGui.QPushButton("Black frame")
        self.gaussiansButton = QtGui.QPushButton("Gaussians")

        self.halfButton = QtGui.QPushButton("Half pattern")
        self.quadrantButton = QtGui.QPushButton("Quadrant pattern")
        self.hexButton = QtGui.QPushButton("Hex pattern")
        self.splitbullButton = QtGui.QPushButton("Split bullseye pattern")

        self.rotAngLabel = QtGui.QLabel('Pattern rotation angle [rad]')
        self.rotAngEdit = QtGui.QLineEdit('0')

        self.leftPatternBox = QtGui.QCheckBox('Modify left')
        self.rightPatternBox = QtGui.QCheckBox('Modify right')

        self.arrow_layout.addWidget(self.upButton, 1, 1)
        self.arrow_layout.addWidget(self.downButton, 3, 1)
        self.arrow_layout.addWidget(self.leftButton, 2, 0)
        self.arrow_layout.addWidget(self.rightButton, 2, 2)
        self.arrow_layout.addWidget(self.incrementWidget, 2, 1)

        self.arrow_layout.addWidget(self.saveButton, 4, 0)
        self.arrow_layout.addWidget(self.loadButton, 4, 1)
        self.arrow_layout.addWidget(self.blackButton, 4, 2)
        self.arrow_layout.addWidget(self.gaussiansButton, 4, 3)

        self.arrow_layout.addWidget(self.halfButton, 5, 0)
        self.arrow_layout.addWidget(self.quadrantButton, 5, 1)
        self.arrow_layout.addWidget(self.hexButton, 5, 2)
        self.arrow_layout.addWidget(self.splitbullButton, 5, 3)

        self.arrow_layout.addWidget(self.rotAngLabel, 6, 0)
        self.arrow_layout.addWidget(self.rotAngEdit, 7, 0)

        self.arrow_layout.addWidget(self.leftPatternBox, 6, 2)
        self.arrow_layout.addWidget(self.rightPatternBox, 7, 2)

        # Definition of the global layout:
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.chooseInterface)
        self.layout.addWidget(self.arrows)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    slm = slmpy.SLMdisplay()

    win = slmWidget(slm)
    win.show()
    app.exec_()
#    slm.close()
