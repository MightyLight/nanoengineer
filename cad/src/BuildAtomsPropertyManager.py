# Copyright 2007 Nanorex, Inc.  See LICENSE file for details. 
"""
BuildAtomsPropertyManager.py

The BuildAtomsPropertyManager class provides the Property Manager for the
B{Build Atoms mode}.  The UI is defined in L{Ui_BuildAtomsPropertyManager}
    
@author: Bruce, Huaicai, Mark, Ninad
@version: $Id:$
@copyright: 2007 Nanorex, Inc.  See LICENSE file for details.

History:
Before Alpha9, (code that used Qt3 framework) Build Atoms mode had a 
'Molecular Modeling Kit' (MMKit) and a dashboard. Starting Alpha 9,
this functionality was integrated into a Property Manager. Since then 
several changes have been made. 
ninad 2007-08-29: Created to use PM module classes, thus deprecating old 
                  Property Manager class MMKit. Split out old 'clipboard' 
                  functionality into new L{PasteMode} 
"""

from Ui_BuildAtomsPropertyManager import Ui_BuildAtomsPropertyManager
from bond_constants               import btype_from_v6

NOBLEGASES = ["He", "Ne", "Ar", "Kr"]

class BuildAtomsPropertyManager(Ui_BuildAtomsPropertyManager):
    """
    The BuildAtomsPropertyManager class provides the Property Manager for the
    B{Build Atoms mode}.  The UI is defined in L{Ui_BuildAtomsPropertyManager}
    """
    
    def __init__(self, parentMode):
        """
        Constructor for the B{Build Atoms} property manager.
        
        @param parentMode: The parent mode where this Property Manager is used
        @type  parentMode: L{depositMode} 
        """
        Ui_BuildAtomsPropertyManager.__init__(self, parentMode)
        
        self.w = self.parentMode.w
        self.win = self.parentMode.w
        self.pw = self.parentMode.pw
        
        self._addGroupBoxes()
        self.updateMessage()
        
    def ok_btn_clicked(self):
        """
        Calls MainWindow.toolsDone to exit the current mode. 
        @attention: this method needs to be renamed. (this should be done in 
        PM_Dialog)
        """
        self.w.toolsDone()
    
    def update_selection_filter_list(self):
        """
        Adds/removes the element selected in the Element Chooser to/from Atom 
        Selection Filter based on what modifier key is pressed (if any).
        """
        element = self.elementChooser.element        
        if self.o.modkeys is None:
            self.w.filtered_elements = []
        if self.o.modkeys == 'Shift':
            if not element in self.w.filtered_elements[:]:
                self.w.filtered_elements.append(element)
        elif self.o.modkeys == 'Control':
            if element in self.w.filtered_elements[:]:
                self.w.filtered_elements.remove(element)
                
        self.update_selection_filter_list_widget()
        
    def update_selection_filter_list_widget(self):
        """
        Updates the list of elements displayed in the Atom Selection Filter 
        List.
        """
        filtered_syms = ''
        for e in self.w.filtered_elements[:]:
            if filtered_syms: 
                filtered_syms += ", "
            
            filtered_syms += e.symbol
        #TODO: Define element filter line edit (self.filterlistLE) in propMgr.
        #The following is disabled for now.
        ##self.filterlistLE.setText(filtered_syms)
                
    def updateMessage(self):
        """
        Updates the message box with an informative message based on the 
        current page and current selected atom type.
        """
        msg = ""
        element = self.elementChooser.element
        
        if self.elementChooser.isVisible():
            msg = "Double click in empty space to insert a single " \
                + element.name + " atom. "
            if not element.symbol in NOBLEGASES:
                msg += "Click on an atom's <i>red bondpoint</i> to attach a " \
                    + element.name + " atom to it."       
        else: # Bonds Tool is selected
            if self.parentMode.cutBondsAction.isChecked():
                msg = "<b> Cut Bonds </b> tool is active. \
                Click on bonds in order to delete them."
                self.MessageGroupBox.insertHtmlMessage(msg)
                return          
            if not hasattr(self.parentMode, 'bondclick_v6'): 
                return
            if self.parentMode.bondclick_v6:
                name = btype_from_v6(self.parentMode.bondclick_v6)
                msg = "Click bonds or bondpoints to make them %s bonds." % name 
            
        # Post message.
        self.MessageGroupBox.insertHtmlMessage(msg)
    
    def update_clipboard_items(self):
        """
        Do nothing. Subclasses should override this method. 
        @see: L{PasteMode.update_clipboard_items} for an example. 
        """
        #TODO: Need further clean up of depositMode.py that will make this 
        #unnecessary
        pass   