# Copyright (c) 2004 Nanorex, Inc.  All rights reserved.
from qt import *
from RotaryMotorPropDialog import *
from VQT import V

class RotaryMotorProp(RotaryMotorPropDialog):
    def __init__(self, rotMotor, glpane):

        RotaryMotorPropDialog.__init__(self)
        self.motor = rotMotor
        self.glpane = glpane
        self.setup()

    def setup(self):
        rotMotor = self.motor
        
        self.motor.originalColor = self.motor.normcolor
        
        self.nameLineEdit.setText(rotMotor.name)
        self.colorPixmapLabel.setPaletteBackgroundColor(
            QColor(int(rotMotor.normcolor[0]*255), 
                         int(rotMotor.normcolor[1]*255), 
                         int(rotMotor.normcolor[2]*255)))


        self.torqueLineEdit.setText(str(rotMotor.torque))
        self.speedLineEdit.setText(str(rotMotor.speed))
#        self.axLineEdit.setText(str(rotMotor.axis[0]))
#        self.ayLineEdit.setText(str(rotMotor.axis[1]))
#        self.azLineEdit.setText(str(rotMotor.axis[2]))

#        self.cxLineEdit.setText(str(rotMotor.center[0]))
#        self.cyLineEdit.setText(str(rotMotor.center[1]))
#        self.czLineEdit.setText(str(rotMotor.center[2]))
        
#        strList = map(lambda i: rotMotor.atoms[i].element.symbol + str(i),
#                                                range(0, len(rotMotor.atoms)))
#        self.atomsComboBox.insertStrList(strList, 0)

        self.lengthLineEdit.setText(str(rotMotor.length)) # motor length
        self.radiusLineEdit.setText(str(rotMotor.radius)) # motor radius
        self.sradiusLineEdit.setText(str(rotMotor.sradius)) # spoke radius
        
        self.applyPushButton.setEnabled(False)
        

    #########################
    # Change rotary motor color
    #########################
    def changeRotaryMotorColor(self):
        color = QColorDialog.getColor(
            QColor(int(self.motor.normcolor[0]*255), 
                         int(self.motor.normcolor[1]*255), 
                         int(self.motor.normcolor[2]*255)),
                         self, "ColorDialog")

        if color.isValid():
            self.colorPixmapLabel.setPaletteBackgroundColor(color)
            self.motor.color = self.motor.normcolor = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self.glpane.paintGL()

    #################
    # OK Button
    #################
    def accept(self):
        self.applyButtonPressed()
        self.motor.cancelled = False
        QDialog.accept(self)

    #################
    # Cancel Button
    #################
    def reject(self):
	    QDialog.reject(self)
	    self.motor.normcolor = self.motor.originalColor

    #################
    # Apply Button
    #################	
    def applyButtonPressed(self):
        
        self.motor.name = self.nameLineEdit.text()
        self.motor.torque = float(str(self.torqueLineEdit.text()))
        self.motor.speed = float(str(self.speedLineEdit.text()))
#        self.motor.axis[0] = float(str(self.axLineEdit.text()))
#        self.motor.axis[1] = float(str(self.ayLineEdit.text()))
#        self.motor.axis[2] = float(str(self.azLineEdit.text()))

#        self.motor.center[0] = float(str(self.cxLineEdit.text()))
#        self.motor.center[1] = float(str(self.cyLineEdit.text()))
#        self.motor.center[2] = float(str(self.czLineEdit.text()))

        self.motor.length = float(str(self.lengthLineEdit.text())) # motor length
        self.motor.radius = float(str(self.radiusLineEdit.text())) # motor radius
        self.motor.sradius = float(str(self.sradiusLineEdit.text())) # spoke radius
                
        self.applyPushButton.setEnabled(False)
	
    def propertyChanged(self):
        self.applyPushButton.setEnabled(True)	