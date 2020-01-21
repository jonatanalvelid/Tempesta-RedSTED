# -*- coding: utf-8 -*-

import pickle
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.dockarea import Dock, DockArea
from control.SLM import slmpy, Mask
# from control import instruments

# Width and height of the SLM which can change from one device to another:
M = 600
N = 792


class SlmWidget(QtGui.QFrame):
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
        self.maskMask = Mask.Helix_Hat(M, N, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value())
        self.maskAber = Mask.Aberrations(M, N, self.lbdPar.value(),
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
        image_widget = pg.GraphicsLayoutWidget()
        self.vb = image_widget.addViewBox(row=1, col=1)
        self.img = pg.ImageItem()
        image = self.mask.img
        image = np.fliplr(image.transpose())
        self.img.setImage(image, autoLevels=False, autoDownsample=True,
                          autoRange=True)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.slm.updateArray(self.mask)

        self.arrows_module = ArrowsControl()

        # Link between the buttons in the arrow module and the functions to
        # control the SLM
        self.arrows_module.upButton.clicked.connect(self.up_clicked)
        self.arrows_module.downButton.clicked.connect(self.down_clicked)
        self.arrows_module.leftButton.clicked.connect(self.left_clicked)
        self.arrows_module.rightButton.clicked.connect(self.right_clicked)
        self.arrows_module.saveButton.clicked.connect(self.save_param)
        self.arrows_module.loadButton.clicked.connect(self.load_param)
        self.arrows_module.blackButton.clicked.connect(self.set_black)
        self.arrows_module.gaussiansButton.clicked.connect(self.set_gaussians)
        self.arrows_module.halfButton.clicked.connect(self.set_half)
        self.arrows_module.quadrantButton.clicked.connect(self.set_quadrant)
        self.arrows_module.hexButton.clicked.connect(self.set_hex)
        self.arrows_module.splitbullButton.clicked.connect(self.set_split)

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
        grid.addWidget(image_widget, 0, 2, 1, 3)
#        grid.addWidget(self.treeAber, 1, 0, 1, 1)
#        grid.addWidget(self.tree, 2, 0, 1, 1)
        grid.addWidget(self.arrows_module, 1, 2, 1, 3)

#        grid.setColumnMinimumWidth(1, 50)
#        grid.setColumnMinimumWidth(0, 50)
#        grid.setRowMinimumHeight(0, 200)
#        grid.setRowMinimumHeight(1, 200)
#        grid.setRowMinimumHeight(2, 50)

    def up_clicked(self):
        """Moves the current Mask up"""
        self.move_mask(-1 * self.arrows_module.increment.value(), 0)

    def down_clicked(self):
        """Moves the current Mask down"""
        self.move_mask(self.arrows_module.increment.value(), 0)

    def left_clicked(self):
        """Moves the current Mask left"""
        self.move_mask(0, -1 * self.arrows_module.increment.value())

    def right_clicked(self):
        """Moves the current Mask right"""
        self.move_mask(0, self.arrows_module.increment.value())

    def move_mask(self, x, y):
        """Sends instruction to both the SLM and the display to move the
        corresponding mask when one arrow is pressed.
        :param int x: new x position of the center of the Mask
        :param int y: new y position of the center of the Mask"""

        if str(self.arrows_module.mask_menu.currentText()) == "Donut":
            self.maskMask.moveLeft(x, y)
            self.maskAber.moveLeft(x, y)
        elif str(self.arrows_module.mask_menu.currentText()) == "Top hat":
            self.maskMask.moveRight(x, y)
            self.maskAber.moveRight(x, y)
        else:
            print("Error: Name of mask does not exist.")
        self.maskMask.update()
        self.maskAber.update()
        self.update()

    def set_black(self):
        """Sets the current mask to a black (null phase) Mask.
        Useful to check the masks one by one"""
        if str(self.arrows_module.mask_menu.currentText()) == "Donut":
            self.maskMask.left.setBlack()
            self.maskAber.left.setBlack()
            self.black_left = True
        elif str(self.arrows_module.mask_menu.currentText()) == "Top hat":
            self.maskMask.right.setBlack()
            self.maskAber.right.setBlack()
            self.black_right = True
        else:
            print("Error: Name of mask does not exist.")
        self.maskMask.update()
        self.maskAber.update()
        self.update()

    def set_gaussians(self):
        """Sets the current masks to Gaussian masks, with the same center.
        Useful for alignment."""
        self.gaussiansBool = True
        self.maskMask = Mask.Gaussians(M, N, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value(),
                                       self.left_center,
                                       self.right_center)
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def set_half(self):
        """Sets the current masks to half masks, with the same center,
        for accurate center position determination."""
        self.maskMask = Mask.Half(M, N, self.lbdPar.value(),
                                  self.RPar.value(),
                                  self.sigmaPar.value(),
                                  self.left_center,
                                  self.right_center,
                                  np.float(self.arrows_module.rot_ang_edit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def set_quadrant(self):
        """Sets the current masks to quadrant masks, with the same center,
        for astigmatism aberration determination."""
        self.maskMask = Mask.Quad(M, N, self.lbdPar.value(),
                                  self.RPar.value(),
                                  self.sigmaPar.value(),
                                  self.left_center,
                                  self.right_center,
                                  np.float(self.arrows_module.rot_ang_edit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def set_hex(self):
        """Sets the current masks to hexagonal masks, with the same center,
        for trefoil aberration determination."""
        self.maskMask = Mask.Hex(M, N, self.lbdPar.value(),
                                 self.RPar.value(),
                                 self.sigmaPar.value(),
                                 self.left_center,
                                 self.right_center,
                                 np.float(self.arrows_module.rot_ang_edit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def set_split(self):
        """Sets the current masks to split bullseye masks, with the same
        center, for coma aberration determination."""
        self.maskMask = Mask.Split(M, N, self.lbdPar.value(),
                                   self.RPar.value(),
                                   self.sigmaPar.value(),
                                   self.left_center,
                                   self.right_center,
                                   np.float(self.arrows_module.rot_ang_edit.text()))
        self.maskMask.tilt(self.anglePar.value())
        self.maskMask.update()
        self.update()

    def apply(self):
        """Applies a configuration to the SLM and changes the mask displayed"""
        self.d_aber_factors, self.th_aber_factors = self.treeAber.get_aber_factors()

        if self.gaussiansBool:
            self.maskMask = Mask.Gaussians(M, N, self.lbdPar.value(),
                                           self.RPar.value(),
                                           self.sigmaPar.value(),
                                           left_pos=self.left_center,
                                           right_pos=self.right_center)
        else:
            self.maskMask = Mask.Helix_Hat(M, N, self.lbdPar.value(),
                                           self.RPar.value(),
                                           self.sigmaPar.value(),
                                           self.left_center,
                                           self.right_center,
                                           self.helix_rotPar.value())
        self.maskMask.tilt(self.anglePar.value())
        self.maskAber = Mask.Aberrations(M, N, self.lbdPar.value(),
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

    def save_param(self):
        """Saves the current SLM configuration, in particular the position of
        the Masks. The informations are stored in a file 'informations.bbn'
        (arbitrary extension) with the module pickle. Separate files are
        saved depending on if you use the glycerol or oil objective."""
        state = self.tree.p.saveState()
        mask_state = {"left_center": self.maskMask.left_center,
                      "right_center": self.maskMask.right_center}
        stateAber = self.treeAber.p.saveState()

        if str(self.arrows_module.obj_lens_menu.currentText()) == "Oil":
            with open("informationsOil.bbn", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(state)
                pickler.dump(mask_state)
            with open("informationsAberOil.bbn", "wb") as fAber:
                pickler = pickle.Pickler(fAber)
                pickler.dump(stateAber)
        elif str(self.arrows_module.obj_lens_menu.currentText()) == "Glycerol":
            with open("informationsGlyc.bbn", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(state)
                pickler.dump(mask_state)
            with open("informationsAberGlyc.bbn", "wb") as fAber:
                pickler = pickle.Pickler(fAber)
                pickler.dump(stateAber)
        elif str(self.arrows_module.obj_lens_menu.currentText()) == "No objective":
            print('You have to choose an objective in the drop down menu!')

        print("Saved all parameters...")
        return

    def load_param(self):
        """Loads the parameters from a previous configuration. Depending on
        which objective is in use, load different parameter files."""
        self.gaussiansBool = False

        if str(self.arrows_module.obj_lens_menu.currentText()) == "Oil":
            with open('informationsOil.bbn', 'rb') as f:
                depickler = pickle.Unpickler(f)
                state = depickler.load()
                mask_state = depickler.load()
            with open('informationsAberOil.bbn', 'rb') as fAber:
                depickler = pickle.Unpickler(fAber)
                stateAber = depickler.load()
        elif str(self.arrows_module.obj_lens_menu.currentText()) == "Glycerol":
            with open('informationsGlyc.bbn', 'rb') as f:
                depickler = pickle.Unpickler(f)
                state = depickler.load()
                mask_state = depickler.load()
            with open('informationsAberGlyc.bbn', 'rb') as fAber:
                depickler = pickle.Unpickler(fAber)
                stateAber = depickler.load()
        elif str(self.arrows_module.obj_lens_menu.currentText()) == "No objective":
            print('You have to choose an objective in the drop down menu!')
            return

        self.tree.p.restoreState(state)
        print("Load mask centers:", mask_state)
        self.treeAber.p.restoreState(stateAber)
        self.d_aber_factors, self.th_aber_factors = self.treeAber.get_aber_factors()

        self.left_center = mask_state["left_center"]
        self.right_center = mask_state["right_center"]

        self.maskMask = Mask.Helix_Hat(M, N, self.lbdPar.value(),
                                       self.RPar.value(),
                                       self.sigmaPar.value(),
                                       left_pos=self.left_center,
                                       right_pos=self.right_center)
        self.maskMask.tilt(self.anglePar.value())
        self.maskAber = Mask.Aberrations(M, N, self.lbdPar.value(),
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
            {'name': 'D Secondary spherical', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
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
            {'name': 'TH Secondary spherical', 'type': 'float', 'value': 0, 'limits': (-lim, lim)},
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
        f_d_sec_sph = self.p.param("D Secondary spherical").value()

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
        f_th_sec_sph = self.p.param("TH Secondary spherical").value()

        d_aber_factors = np.array([f_d_tilt, f_d_tip, f_d_defoc, f_d_sph, f_d_vert_coma, f_d_hoz_coma,
                                   f_d_vert_ast, f_d_obl_ast, f_d_vert_trefoil, f_d_obl_trefoil, f_d_sec_sph])
        th_aber_factors = np.array([f_th_tilt, f_th_tip, f_th_defoc, f_th_sph, f_th_vert_coma, f_th_hoz_coma,
                                    f_th_vert_ast, f_th_obl_ast, f_th_vert_trefoil, f_th_obl_trefoil, f_th_sec_sph])
        return d_aber_factors, th_aber_factors


class ArrowsControl(QtGui.QFrame):
    """This widget creates four buttons able to move a circular phase mask
    with a tunable number of pixels. Useful to align the phase mask with the
    incident beam without touching any optics."""
    def __init__(self, *args, **kwargs):
        # Definition of the Widget to choose left or right part of the Mask
        super().__init__(*args, **kwargs)
        self.mask_choice_widget = QtGui.QWidget()
        self.mask_choice_widget_layout = QtGui.QGridLayout()
        self.mask_choice_widget.setLayout(self.mask_choice_widget_layout)

        # Choose which mask to modify
        self.mask_menu = QtGui.QComboBox()
        self.mask_menu.addItem("Donut")
        self.mask_menu.addItem("Top hat")
        self.mask_choice_widget_layout.addWidget(QtGui.QLabel('Select part of the mask:'), 0, 0)
        self.mask_choice_widget_layout.addWidget(self.mask_menu, 0, 1)

        # Choose which objective is in use
        self.obj_lens_menu = QtGui.QComboBox()
        self.obj_lens_menu.addItem("No objective")
        self.obj_lens_menu.addItem("Oil")
        self.obj_lens_menu.addItem("Glycerol")
        self.mask_choice_widget_layout.addWidget(QtGui.QLabel('Select which objective is used:'), 1, 0)
        self.mask_choice_widget_layout.addWidget(self.obj_lens_menu, 1, 1)

        # Defining the part with only the arrows themselves
        self.arrows = QtGui.QFrame()
        self.arrow_layout = QtGui.QGridLayout()
        self.arrows.setLayout(self.arrow_layout)

        self.up_button = QtGui.QPushButton('Up (YZ)')
        self.up_button.setCheckable(False)
        self.up_button.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                    QtGui.QSizePolicy.Expanding)
        self.up_button.setFixedSize(self.up_button.sizeHint())

        self.down_button = QtGui.QPushButton('Down (YZ)')
        self.down_button.setCheckable(False)
        self.down_button.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)
        self.down_button.setFixedSize(self.up_button.sizeHint())

        self.left_button = QtGui.QPushButton('Left (XZ)')
        self.left_button.setCheckable(False)
        self.left_button.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Expanding)
        self.left_button.setFixedSize(self.up_button.sizeHint())

        self.right_button = QtGui.QPushButton('Right (XZ)')
        self.right_button.setCheckable(False)
        self.right_button.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Expanding)
        self.right_button.setFixedSize(self.up_button.sizeHint())

        # Widget to change the amount of deplacement induced by the arrows
        self.increment_widget = QtGui.QWidget()
        self.increment_widget_layout = QtGui.QVBoxLayout()
        self.increment_widget.setLayout(self.increment_widget_layout)

        label = QtGui.QLabel()
        label.setText("Move (px)")
        self.increment = QtGui.QSpinBox()
        self.increment.setRange(1, 500)
        self.increment.setValue(1)
        self.increment_widget_layout.addWidget(label)
        self.increment_widget_layout.addWidget(self.increment)

        self.save_button = QtGui.QPushButton("Save")
        self.load_button = QtGui.QPushButton("Load")

        self.black_button = QtGui.QPushButton("Black frame")
        self.gaussians_button = QtGui.QPushButton("Gaussians")

        self.half_button = QtGui.QPushButton("Half pattern")
        self.quadrant_button = QtGui.QPushButton("Quadrant pattern")
        self.hex_button = QtGui.QPushButton("Hex pattern")
        self.splitbull_button = QtGui.QPushButton("Split bullseye pattern")

        self.rot_ang_label = QtGui.QLabel('Pattern rotation angle [rad]')
        self.rot_ang_edit = QtGui.QLineEdit('0')

        self.left_pattern_box = QtGui.QCheckBox('Modify left')
        self.right_pattern_box = QtGui.QCheckBox('Modify right')

        self.arrow_layout.addWidget(self.up_button, 1, 1)
        self.arrow_layout.addWidget(self.down_button, 3, 1)
        self.arrow_layout.addWidget(self.left_button, 2, 0)
        self.arrow_layout.addWidget(self.right_button, 2, 2)
        self.arrow_layout.addWidget(self.increment_widget, 2, 1)

        self.arrow_layout.addWidget(self.save_button, 4, 0)
        self.arrow_layout.addWidget(self.load_button, 4, 1)
        self.arrow_layout.addWidget(self.black_button, 4, 2)
        self.arrow_layout.addWidget(self.gaussians_button, 4, 3)

        self.arrow_layout.addWidget(self.half_button, 5, 0)
        self.arrow_layout.addWidget(self.quadrant_button, 5, 1)
        self.arrow_layout.addWidget(self.hex_button, 5, 2)
        self.arrow_layout.addWidget(self.splitbull_button, 5, 3)

        self.arrow_layout.addWidget(self.rot_ang_label, 6, 0)
        self.arrow_layout.addWidget(self.rot_ang_edit, 7, 0)

        self.arrow_layout.addWidget(self.left_pattern_box, 6, 2)
        self.arrow_layout.addWidget(self.right_pattern_box, 7, 2)

        # Definition of the global layout:
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.mask_choice_widget)
        self.layout.addWidget(self.arrows)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    slm = slmpy.SLMdisplay()

    win = slmWidget(slm)
    win.show()
    app.exec_()
#    slm.close()
