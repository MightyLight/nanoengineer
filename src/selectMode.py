# Copyright (c) 2004 Nanorex, Inc.  All rights reserved.
"""
selectMode.py -- the default mode for Atom's main model view.

$Id$
"""

from modes import *
from chunk import molecule
import env

def do_what_MainWindowUI_should_do(w):
    '''This creates the Select Atoms (not the Select Chunks) dashboard .
    '''
    w.selectAtomsDashboard.clear()

    w.depositAtomLabel = QLabel(w.selectAtomsDashboard,"Select Atoms")
    w.depositAtomLabel.setText(" Select Atoms ")
    w.selectAtomsDashboard.addSeparator()

    w.filterCheckBox = QCheckBox(" Filter : ", w.selectAtomsDashboard)
    
    w.elemFilterComboBox = QComboBox(0,w.selectAtomsDashboard, "elemFilterComboBox")

    w.modifySetElementAction.addTo(w.selectAtomsDashboard)

    w.selectAtomsDashboard.addSeparator()

    w.selectConnectedAction.addTo(w.selectAtomsDashboard)
    w.selectDoublyAction.addTo(w.selectAtomsDashboard)
    
    w.selectAtomsDashboard.addSeparator()
    w.toolsDoneAction.addTo(w.selectAtomsDashboard)
    w.selectAtomsDashboard.setLabel("Select Atoms")
    w.elemFilterComboBox.clear()
    # WARNING:
    # these are identified by *position*, not by their text, using corresponding entries in eCCBtab1;
    # this is done by win.elemChange even though nothing but depositMode calls that;
    # the current element is stored in win.Element (as an atomic number ###k).
    # All this needs cleanup so it's safer to modify this and so atomtype can sometimes be included.
    # Both eCCBtab1 and eCCBtab2 are set up and used in MWsemantics but should be moved here,
    # or perhaps with some part moved into elements.py if it ought to share code with elementSelector.py
    # and elementColors.py (though it doesn't now).
    w.elemFilterComboBox.insertItem("Hydrogen")
    w.elemFilterComboBox.insertItem("Helium")
    w.elemFilterComboBox.insertItem("Boron")
    w.elemFilterComboBox.insertItem("Carbon") # will change to two entries, Carbon(sp3) and Carbon(sp2) -- no, use separate combobox
    w.elemFilterComboBox.insertItem("Nitrogen")
    w.elemFilterComboBox.insertItem("Oxygen")
    w.elemFilterComboBox.insertItem("Fluorine")
    w.elemFilterComboBox.insertItem("Neon")
    w.elemFilterComboBox.insertItem("Aluminum")
    w.elemFilterComboBox.insertItem("Silicon")
    w.elemFilterComboBox.insertItem("Phosphorus")
    w.elemFilterComboBox.insertItem("Sulfur")
    w.elemFilterComboBox.insertItem("Chlorine")
    w.elemFilterComboBox.insertItem("Argon")
    w.elemFilterComboBox.insertItem("Germanium")
    w.elemFilterComboBox.insertItem("Arsenic")
    w.elemFilterComboBox.insertItem("Selenium")
    w.elemFilterComboBox.insertItem("Bromine")
    w.elemFilterComboBox.insertItem("Krypton")
    #w.elemFilterComboBox.insertItem("Antimony")
    #w.elemFilterComboBox.insertItem("Tellurium")
    #w.elemFilterComboBox.insertItem("Iodine")
    #w.elemFilterComboBox.insertItem("Xenon")
    w.connect(w.elemFilterComboBox,SIGNAL("activated(int)"),w.elemChange)
    
    
class selectMode(basicMode):
    "the default mode of GLPane"
    
    # class constants
    backgroundColor = 189/255.0, 228/255.0, 238/255.0
    gridColor = (0.0, 0.0, 0.6)

    # default initial values
    savedOrtho = 0

    jigSelectionEnabled = True

    #def __init__(self, glpane):
    #    """The initial function is called only once for the whole program """
    #    basicMode.__init__(self, glpane)
    #    self.jigSelectionEnabled = True
    
    # init_gui handles all the GUI display when entering a mode    
    def init_gui(self):
        pass # let the subclass handle everything for the GUI - Mark [2004-10-11]

    # restore_gui handles all the GUI display when leavinging this mode [mark 041004]
    def restore_gui(self):
        pass # let the subclass handle everything for the GUI - Mark [2004-10-11]
   
    def leftDown(self, event):
        self.StartPick(event, 2) # new selection (replace)
    
    def leftCntlDown(self, event):
        self.StartPick(event, 0) # subtract from selection

    def leftShiftDown(self, event):
        self.StartPick(event, 1) # add to selection


    def StartPick(self, event, sense):
        """Start a selection curve
        """
        self.selSense = sense
        self.picking = 1
        self.o.SaveMouse(event)
        self.o.prevvec = None

        p1, p2 = self.o.mousepoints(event, 0.01)
        self.o.normal = self.o.lineOfSight
        self.sellist = [p1]
        self.o.backlist = [p2]
        self.pickLineStart = self.pickLinePrev = p1
        self.pickLineLength = 0.0

    
    def leftDrag(self, event):
        self.ContinPick(event, 2)
    
    def leftCntlDrag(self, event):
        self.ContinPick(event, 0)
    
    def leftShiftDrag(self, event):
        self.ContinPick(event, 1)

    def ContinPick(self, event, sense):
        """Add another segment to a selection curve
        """
        if not self.picking: return
        self.selSense = sense
        p1, p2 = self.o.mousepoints(event, 0.01)

        self.sellist += [p1]
        self.o.backlist += [p2]
        netdist = vlen(p1-self.pickLineStart)

        self.pickLineLength += vlen(p1-self.pickLinePrev)
        self.selLassRect = self.pickLineLength < 2*netdist

        self.pickLinePrev = p1
        self.o.gl_update()

    def leftUp(self, event):
        self.EndPick(event, 2)
    
    def leftCntlUp(self, event):
        self.EndPick(event, 0)
    
    def leftShiftUp(self, event):
        self.EndPick(event, 1)

    def EndPick(self, event, selSense):
        """Close a selection curve and do the selection
        """
        if not self.picking: return
        self.picking = False

        p1, p2 = self.o.mousepoints(event, 0.01)

        if self.pickLineLength/self.o.scale < 0.03:
            # didn't move much, call it a click
            if not self.jigGLSelect(event, selSense):
                if selSense == 0: self.o.assy.unpick_at_event(event)
                if selSense == 1: self.o.assy.pick_at_event(event)
                if selSense == 2: self.o.assy.onlypick_at_event(event)
            ###Huaicai 1/29/05: to fix zoom messing up selection bug
            ###In window zoom mode, even for a big selection window, the 
            ###pickLineLength/scale could still be < 0.03, so we need clean 
            ### sellist[] to release the rubber band selection window. One 
            ###problem is its a single pick not as user expect as area pick 
#            self.sellist = []
#            self.w.win_update()
#            return
        
        # Realized that the 3 lines above were the same as the last 2 lines of this method,
        # so I created this else statement and included everything (except the last 2 lines).
        # This seems better and may be necessary for fixing bug 86 (see more comments below).
        # Mark 050710
        else:

            self.sellist += [p1]
            self.sellist += [self.sellist[0]]
            self.o.backlist += [p2]
            self.o.backlist += [self.o.backlist[0]]
            self.o.shape=SelectionShape(self.o.right, self.o.up, self.o.lineOfSight)
            eyeball = (-self.o.quat).rot(V(0,0,6*self.o.scale)) - self.o.pov        
            if self.selLassRect:
                self.o.shape.pickrect(self.o.backlist[0], p2, -self.o.pov, selSense,  (not self.o.ortho) and eyeball)
            else:
                self.o.shape.pickline(self.o.backlist, -self.o.pov, selSense,
                             (not self.o.ortho) and eyeball)
        
            self.o.shape.select(self.o.assy)
            self.o.shape = None

        # end else
                
        self.sellist = []
            # (for debug, it's sometimes useful to not reset sellist here,
            #  so you can see it at the same time as the selection it caused.)

        # This section was added to fix bug 86 and others like it.  I am attempting to 
        # enable/disable menu and toolbar (action) items based on how many atoms 
        # are selected.  I have local code (menu_control.py) that works, but I need to 
        # discuss this with Bruce, after A6. This code works for updating menus/toolbars 
        # when selecting atoms in the glpane with the mouse, but not for the "Select" 
        # actions (i.e. Select All) while in Select Atoms mode. There is also something 
        # to be said about leaving "illegal" action widgets enabled, esp for novice users 
        # that can benefit from informative history msgs when attempting to do something
        # they shouldn't.
        # Mark 050710
#        from menu_control import update_menus
#        update_menus(self.w)
        
        self.w.win_update()

    def leftDouble(self, event):
        """Select the part containing the atom the cursor is on.
        """
        self.move() # go into move mode
        # bruce 040923: we use to inline the same code as is in this method
        # bruce 041217: I am guessing we still intend to leave this in,
        # here and in Move mode (to get back).

    
    # bruce 041216: renamed elemSet to modifyTransmute, added force option,
    # made it work on selected chunks as well as selected atoms
    # [that last part is undiscussed, we might remove it]
    def modifyTransmute(self, elem, force = False): 
        # elem is an element number
        # make it current in the element selector dialog
        self.w.setElement(elem) # bruce comment 040922 -- this line is an inlined version of the superclass method.
        # now change selected atoms to the specified element
        # [bruce 041215: this should probably be made available for any modes
        #  in which "selected atoms" are permitted, not just Select modes. #e]
        from elements import PeriodicTable
        if self.o.assy.selatoms:
            for atm in self.o.assy.selatoms.values():
                atm.Transmute(PeriodicTable.getElement(elem), force = force)
                # bruce 041215 fix bug 131 by replacing low-level mvElement call
                # with new higher-level method Transmute. Note that singlets
                # can't be selected, so the fact that Transmute does nothing to
                # them is not (presently) relevant.
            #e status message?
            # (Presently a.Transmute makes one per "error or refusal".)
            self.o.gl_update()
        elif self.o.assy.selmols:
            for mol in self.o.assy.selmols[:]:
                for atm in mol.atoms.values():
                    atm.Transmute(PeriodicTable.getElement(elem), force = force)
                        # this might run on some killed singlets; should be ok
            self.o.gl_update()
        return

    def setJigSelectionEnabled(self):
        self.jigSelectionEnabled = not self.jigSelectionEnabled
                 
        id = self.Menu1.idAt(3)
        self.Menu1.setItemChecked(id, self.jigSelectionEnabled)
        
    
    def jigGLSelect(self, event, selSense):
        '''Use the OpenGL picking/selection to select any jigs '''
        if not self.jigSelectionEnabled: return False
        
        wX = event.pos().x()
        wY = self.o.height - event.pos().y()
        
        aspect = float(self.o.width)/self.o.height
        
        wZ = glReadPixelsf(wX, wY, 1, 1, GL_DEPTH_COMPONENT)
        gz = wZ[0][0]
        
        pxyz = A(gluUnProject(wX, wY, gz))
        pn = self.o.out
        pxyz -= 0.0002*pn
        dp = - dot(pxyz, pn)
        #print "clip plane: ", pn, dp 
        #print "Point on plane: ", pxyz
        
        current_glselect = (wX,wY,1,1) #bruce 050615 for use by nodes which want to set up their own projection matrix
        self.o._setup_projection( aspect, self.o.vdist, glselect = current_glselect) 
        
        glSelectBuffer(self.o.glselectBufferSize)
        glRenderMode(GL_SELECT)
        glInitNames()
        glMatrixMode(GL_MODELVIEW)
        try:
            glClipPlane(GL_CLIP_PLANE0, (pn[0], pn[1], pn[2], dp))
            glEnable(GL_CLIP_PLANE0)
            self.o.assy.draw(self.o)
            glDisable(GL_CLIP_PLANE0)
            #self.mode.Draw() # should perhaps optim by skipping chunks based on bbox... don't know if that would help or hurt
                # note: this might call some display lists which, when created, registered namestack names,
                # so we need to still know those names!
        except:
            print_compact_traceback("exception in mode.Draw() during GL_SELECT; ignored; restoring modelview matrix: ")
            glMatrixMode(GL_MODELVIEW)
            self.o._setup_modelview( self.o.vdist) ###k correctness of this is unreviewed! ####@@@@
            # now it's important to continue, at least enough to restore other gl state
        
        glFlush()
        
        hit_records = list(glRenderMode(GL_RENDER))
        print "%d hits" % len(hit_records)
        for (near,far,names) in hit_records: # see example code, renderpass.py
            print "hit record: near,far,names:",near,far,names
                # e.g. hit record: near,far,names: 1439181696 1453030144 (1638426L,)
                # which proves that near/far are too far apart to give actual depth,
                # in spite of the 1-pixel drawing window (presumably they're vertices
                # taken from unclipped primitives, not clipped ones).
            if names:
                obj = env.obj_with_glselect_name.get(names[-1]) #k should always return an obj
                #self.glselect_dict[id(obj)] = obj # now these can be rerendered specially, at the end of mode.Draw
                if isinstance(obj, Jig):
                    if selSense == 0: #Ctrl key, unpick picked
                        if obj.picked:  
                            obj.unpick()
                    elif selSense == 1: #Shift key, Add pick
                        if not obj.picked: 
                            obj.pick()
                    else:               #Without key press, exclusive pick
                        self.o.assy.unpickparts() 
                        self.o.assy.unpickatoms()
                        if not obj.picked:
                            obj.pick()
                    return True
        return  False       

    
    def Draw(self):
        # bruce comment 040922: code is almost identical with modifyMode.Draw;
        # the difference (no check for self.o.assy existing) might be a bug in this version, or might have no effect.
        basicMode.Draw(self)   
        #self.griddraw()
        if self.sellist: self.pickdraw()
        self.o.assy.draw(self.o)

    def makeMenus(self): # menu item names modified by bruce 041217

        def fixit3(text, func):
            if self.default_mode_status_text == "Mode: " + text:
                # this menu item indicates the current mode --
                # add a checkmark and disable it [bruce 050112]
                return text, func, 'checked'
            else:
                return text, func
        
        self.Menu_spec = [
            ###e these accelerators should be changed to be Qt-official
            # by extending widgets.makemenu_helper to use Qt's setAccel...
            # [bruce 050112]
            ('Select All                     Ctrl+A', self.o.assy.selectAll),
            ('Select None                Ctrl+D', self.o.assy.selectNone),
            ('Invert Selection   Ctrl+Shift+I', self.o.assy.selectInvert),
            ('Enable Jig Selection',  self.setJigSelectionEnabled, 'checked'),
            None,
            # bruce 041217 renamed Atoms and Chunks to the full names of the
            # modes they enter, and added Move Chunks too. (It was already
            # present but in a different menu. I left it there, too, for the
            # sake of existing users. But it would be better to remove it.)
            #bruce 051213 reordered these to conform with toolbar.
            fixit3(('Select Chunks'), self.w.toolsSelectMolecules),
            fixit3(('Select Atoms'), self.w.toolsSelectAtoms),
            ('Move Chunks', self.w.toolsMoveMolecule), 
            ('Build Atoms', self.w.toolsBuildAtoms),
            ]
        
        self.Menu_spec_shift = [
            ('Delete        Del', self.o.assy.delete_sel),
            ('Move', self.move), # redundant but intentionally left in for now
            None,
            ('Hide', self.o.assy.Hide),
            None,
            ('Stretch', self.o.assy.Stretch) ]
        
        self.Menu_spec_control = [
            ('Invisible', self.w.dispInvis),
            None,
            ('Default', self.w.dispDefault),
            ('Lines', self.w.dispLines),
            ('CPK', self.w.dispCPK),
            ('Tubes', self.w.dispTubes),
            ('VdW', self.w.dispVdW),
            None,
            ('Chunk Color...', self.w.dispObjectColor),
            ('Reset Chunk Color', self.w.dispResetChunkColor),
            ('Reset Atoms Display', self.w.dispResetAtomsDisplay),
            ('Show Invisible Atoms', self.w.dispShowInvisAtoms),
            ]

    def move(self):
        # we must set OldCursor to the MoveSelectCursor before going into move mode.
        # go into move mode [bruce 040923: now also called from leftDouble]
        self.o.setMode('MODIFY') # [bruce 040923: i think how we do this doesn't need to be changed]

    pass # end of class selectMode
    
class selectMolsMode(selectMode):
        modename = 'SELECTMOLS'
        default_mode_status_text = "Mode: Select Chunks"
    
        def Enter(self): 
            basicMode.Enter(self)
            self.o.assy.pickParts() # josh 10/7 to avoid race in assy init
            
        def init_gui(self):
            selectMode.init_gui(self)
#            print "selectMode.py: init_gui(): Cursor set to SelectMolsCursor"
            self.o.setCursor(self.w.SelectMolsCursor)
            self.w.OldCursor = QCursor(self.o.cursor())
            self.w.toolsSelectMoleculesAction.setOn(1) # toggle on the "Select Chunks" tools icon
            self.w.selectMolDashboard.show() 
            
        def restore_gui(self):
            self.w.selectMolDashboard.hide()
        
        def keyPress(self,key):
            basicMode.keyPress(self, key)
            if key == Qt.Key_Shift:
#                print "selectMode.py: keyPress(): Cursor set to SelectMolsAddCursor"
                self.o.setCursor(self.w.SelectMolsAddCursor)
            if key == Qt.Key_Control:
#                print "selectMode.py: keyPress(): Cursor set to SelectMolsSubtractCursor"
                self.o.setCursor(self.w.SelectMolsSubtractCursor)
                
        def keyRelease(self,key):
            basicMode.keyRelease(self, key)
            if key == Qt.Key_Shift or key == Qt.Key_Control:
#                print "selectMode.py: keyRelease(): Cursor set to SelectMolsCursor"
                self.o.setCursor(self.w.SelectMolsCursor)
                
        def rightShiftDown(self, event):
            basicMode.rightShiftDown(self, event)
            self.o.setCursor(self.w.SelectMolsCursor)
           
        def rightCntlDown(self, event):          
            basicMode.rightCntlDown(self, event)
            self.o.setCursor(self.w.SelectMolsCursor)


class selectAtomsMode(selectMode):
        modename = 'SELECTATOMS'
        default_mode_status_text = "Mode: Select Atoms"
        
        def Enter(self): 
            basicMode.Enter(self)
            self.o.assy.selectAtoms()
            # Reinitialize previously picked atoms (ppas).
            self.o.assy.ppa2 = self.o.assy.ppa3 = None
            
        def init_gui(self):
            selectMode.init_gui(self)
            self.o.setCursor(self.w.SelectAtomsCursor)
            self.w.toolsSelectAtomsAction.setOn(1) # toggle on the "Select Atoms" tools icon
            self.w.selectAtomsDashboard.show() 
            
        def restore_gui(self):
            self.w.selectAtomsDashboard.hide()
            self.w.filterCheckBox.setChecked(0)
            
        def keyPress(self,key):
            basicMode.keyPress(self, key)
            if key == Qt.Key_Shift:
                self.o.setCursor(self.w.SelectAtomsAddCursor)
            if key == Qt.Key_Control:
                self.o.setCursor(self.w.SelectAtomsSubtractCursor)
            # Shortcut keys for atom type in selection filter.  Bug/NFR 649.  Mark 050711.
            for sym, code, num in elemKeyTab:
                if key == code:
                    self.w.setElement(num)
                                
        def keyRelease(self,key):
            basicMode.keyRelease(self, key)
            if key == Qt.Key_Shift or key == Qt.Key_Control:
                self.o.setCursor(self.w.SelectAtomsCursor)
       
       
        def rightShiftDown(self, event):
            basicMode.rightShiftDown(self, event)
            self.o.setCursor(self.w.SelectAtomsCursor)
           
        def rightCntlDown(self, event):          
            basicMode.rightCntlDown(self, event)
            self.o.setCursor(self.w.SelectAtomsCursor)         