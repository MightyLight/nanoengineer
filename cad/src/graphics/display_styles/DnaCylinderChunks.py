# Copyright 2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaCylinderChunks.py -- defines I{DNA Cylinder} display mode, which draws 
axis chunks as a cylinder in the chunk's color.

@author: Mark
@version: $Id$
@copyright: 2008 Nanorex, Inc.  See LICENSE file for details. 

This is still considered experimental.

Initially, this is mainly intended as a fast-rendering display mode for DNA.
When the DNA data model become operative, this class will be implemented
to give faster and better ways to compute the axis path and render the
cylinder.

To do:
- Add new user pref for "DNA Cylinder Radius".
- Fix limitations/bugs listed in the class docstring.

History:

Mark 2008-02-12: Created by making a copy of CylinderChunks.py

piotr 080310: I have rewritten most of the code here from scratch. Most of 
the code computed within this function has to be moved to "getmemo" 
for a speed optimization. There are several issues with this rendering code,
including lack of highlighting and selection support, and some
weird behavior when modeltree is used to select individual strands.

The DNA display style requires DNA updater to be enabled.

There are four independent structures within the DNA display style:
axis, strands, struts and bases. Properties of these parts can be set
in the User Preferences dialog.

piotr 080317: Added POV-Ray rendering routines.

piotr 080318: Moved most of the data generation code to "getmemo"
Highlighting and selection now works. Thank you, Ninad!!!

("rainbow" strands still can't be selected nor highlighted, this will 
be fixed later)


"""

from Numeric import dot, argmax, argmin, sqrt

import sys
import foundation.env as env
import graphics.drawing.drawer as drawer
from geometry.geometryUtilities import matrix_putting_axis_at_z
from geometry.VQT import V, Q, norm, cross, angleBetween
from utilities.debug import print_compact_traceback
from graphics.display_styles.displaymodes import ChunkDisplayMode
from utilities.constants import ave_colors, black, red, blue, white, darkgreen

from utilities.debug_prefs import debug_pref, Choice_boolean_True, Choice_boolean_False

from utilities.prefs_constants import atomHighlightColor_prefs_key

# piotr 080309: user pereferences for DNA style
from utilities.prefs_constants import dnaStyleStrandsColor_prefs_key
from utilities.prefs_constants import dnaStyleAxisColor_prefs_key
from utilities.prefs_constants import dnaStyleStrutsColor_prefs_key
from utilities.prefs_constants import dnaStyleBasesColor_prefs_key
from utilities.prefs_constants import dnaStyleStrandsShape_prefs_key
from utilities.prefs_constants import dnaStyleBasesShape_prefs_key
from utilities.prefs_constants import dnaStyleStrandsArrows_prefs_key
from utilities.prefs_constants import dnaStyleAxisShape_prefs_key
from utilities.prefs_constants import dnaStyleStrutsShape_prefs_key
from utilities.prefs_constants import dnaStyleStrandsScale_prefs_key
from utilities.prefs_constants import dnaStyleAxisScale_prefs_key
from utilities.prefs_constants import dnaStyleBasesScale_prefs_key
from utilities.prefs_constants import dnaStyleAxisTaper_prefs_key
from utilities.prefs_constants import dnaStyleStrutsScale_prefs_key

# piotr 080325 added more user preferences
from utilities.prefs_constants import dnaStrandLabelsEnabled_prefs_key
from utilities.prefs_constants import dnaStrandLabelsColor_prefs_key
from utilities.prefs_constants import dnaStrandLabelsColorMode_prefs_key
from utilities.prefs_constants import dnaBaseIndicatorsEnabled_prefs_key
from utilities.prefs_constants import dnaBaseIndicatorsColor_prefs_key
from utilities.prefs_constants import dnaBaseIndicatorsAngle_prefs_key
from utilities.prefs_constants import dnaBaseIndicatorsDistance_prefs_key

from model.elements import Singlet
from math import sin, cos, pi
from Numeric import zeros, Float, Float32

try:
    from OpenGL.GLE import glePolyCone
    from OpenGL.GLE import gleGetNumSides 
    from OpenGL.GLE import gleSetNumSides 
    from OpenGL.GLE import gleExtrusion
    from OpenGL.GLE import gleTwistExtrusion
    from OpenGL.GLE import glePolyCylinder 
    from OpenGL.GLE import gleSetJoinStyle
    from OpenGL.GLE import TUBE_NORM_EDGE 
    from OpenGL.GLE import TUBE_NORM_PATH_EDGE 
    from OpenGL.GLE import TUBE_JN_ROUND
    from OpenGL.GLE import TUBE_JN_ANGLE
    from OpenGL.GLE import TUBE_CONTOUR_CLOSED 
    from OpenGL.GLE import TUBE_JN_CAP 
except:
    print "DNA Cylinder: GLE module can't be imported. Now trying _GLE"
    from OpenGL._GLE import glePolyCone 
    from OpenGL._GLE import gleGetNumSides 
    from OpenGL._GLE import gleSetNumSides 
    from OpenGL._GLE import gleExtrusion
    from OpenGL._GLE import gleTwistExtrusion    
    from OpenGL._GLE import glePolyCylinder 
    from OpenGL._GLE import gleSetJoinStyle
    from OpenGL._GLE import TUBE_NORM_EDGE 
    from OpenGL._GLE import TUBE_NORM_PATH_EDGE 
    from OpenGL._GLE import TUBE_JN_ROUND
    from OpenGL._GLE import TUBE_JN_ANGLE
    from OpenGL._GLE import TUBE_CONTOUR_CLOSED 
    from OpenGL._GLE import TUBE_JN_CAP 

import colorsys
from OpenGL.GL import glBegin
from OpenGL.GL import glEnd
from OpenGL.GL import glVertex3f
from OpenGL.GL import glColor3f
from OpenGL.GL import glColor3fv
from OpenGL.GL import glTranslatef
from OpenGL.GL import GL_LINE_STRIP        
from OpenGL.GL import GL_LINES
from OpenGL.GL import GL_POLYGON
from OpenGL.GL import glEnable
from OpenGL.GL import glDisable
from OpenGL.GL import GL_LIGHTING
from OpenGL.GL import GL_SMOOTH
from OpenGL.GL import glShadeModel
from OpenGL.GL import GL_COLOR_MATERIAL
from OpenGL.GL import GL_TRIANGLES
from OpenGL.GL import GL_FRONT_AND_BACK
from OpenGL.GL import GL_AMBIENT_AND_DIFFUSE
from OpenGL.GL import glMaterialfv
from OpenGL.GL import glPushMatrix
from OpenGL.GL import glPopMatrix
from OpenGL.GL import glRotatef
from OpenGL.GL import glScalef
from OpenGL.GL import glLineWidth
from OpenGL.GL import GL_QUADS

from OpenGL.GLU import gluUnProject

from model.chunk import Chunk

chunkHighlightColor_prefs_key = atomHighlightColor_prefs_key # initial kluge

class DnaCylinderChunks(ChunkDisplayMode):
    """
    DNA Cylinder display mode, which draws "axis" chunks as a cylinder.

    Limitations/known bugs:
    - Cylinders are always straight. DNA axis chunks with atoms that are not 
    aligned in a straight line are not displayed correctly (i.e. they don't
    follow a curved axis path. fixed 080310 piotr
    - Hover highlighting does not work. fixed 080318: thank you, Ninad!!! 
    - Selected chunks are not colored in the selection color. same as above
    - Cannot drag/move a selected cylinder interactively. same as above
    - DNA Cylinders are not written to POV-Ray file. piotr: done 080317
    - DNA Cylinders are not written to PDB file and displayed in QuteMolX.
    piotr: to be done

    @note: Nothing else is rendered (no atoms, sugar atoms, etc) when 
        set to this display mode. piotr 080316: some feature can be displayed
        as "bases"

    @attention: This is still considered experimental.
    """
    # mmp_code must be a unique 3-letter code, distinct from the values in 
    # constants.dispNames or in other display modes
    mmp_code = 'dna'  
    disp_label = 'DNA Cylinder' # label for statusbar fields, menu text, etc.
    featurename = "Set Display DNA Cylinder"
    # Pretty sure Bruce's intention is to define icons for subclasses
    # of ChunkDisplayMode here, not in mticon_names[] and hideicon_names[] 
    # in chunks.py. Ask him to be sure. Mark 2008-02-12
    icon_name = "modeltree/DnaCylinder.png"
    hide_icon_name = "modeltree/DnaCylinder-hide.png"
    ### also should define icon as an icon object or filename, 
    ### either in class or in each instance
    ### also should define a featurename for wiki help
    def spline(self, data, idx, t):
        """
        Implements a Catmull-Rom spline.
        Interpolates between data[idx] and data[idx+1].
        0.0 <= t <= 1.0.
        """
        t2 = t*t
        t3 = t2*t
        x0 = data[idx-1]
        x1 = data[idx]
        x2 = data[idx+1]
        x3 = data[idx+2]
        return 0.5*((2.0*x1)+
                    (-x0+x2)*t+
                    (2.0*x0-5.0*x1+4.0*x2-x3)*t2+
                    (-x0+3.0*x1-3.0*x2+x3)*t3)

    def getRainbowColor(self, hue, saturation, value):
        """
        Gets a color of a hue range limited to 0 - 0.667 (red - blue)
        """
        if hue<0.0: hue=0.0
        if hue>1.0: hue=1.0
        return colorsys.hsv_to_rgb(0.667-0.677*hue, saturation, value)

    def getFullRainbowColor(self, hue):
        """
        Gets a color of a full hue range.
        """
        if hue<0.0: hue=0.0
        if hue>1.0: hue=1.0
        return colorsys.hsv_to_rgb(hue, 1.0, 1.0)

    def getBaseColor(self, base):
        """
        Returns a color according to DNA base type.
        """
        if base=="G":
            return ([0.8,0.5,0.0])
        elif base=="C":
            return ([0.8,0.1,0.0])
        if base=="A":
            return ([0.2,0.8,0.4])
        elif base=="T":
            return ([0.0,0.6,0.8])
        else:
            return ([0.5,0.5,0.5])

    def getRainbowColorInRange(self, pos, count, saturation, value):
        if count>1: count -= 1
        hue = float(pos)/float(count)
        if hue<0.0: hue = 0.0
        if hue>1.0: hue = 1.0
        return self.getRainbowColor(hue, saturation, value)

    def getStrandChunks(self, dna_group):
        """
        Returns a list of Strand chunks inside a DnaGroup object

        @return: A list containing all the strand chunks
                 within self.
        @rtype: list
        """
        strandChunkList = []
        def filterStrandChunks(node):
            if isinstance(node, Chunk) and node.isStrandChunk():
                strandChunkList.append(node)    

        dna_group.apply2all(filterStrandChunks)

        return strandChunkList


    def drawchunk(self, glpane, chunk, memo, highlighted):
        """
        Draw chunk in glpane in the whole-chunk display mode represented by 
        this ChunkDisplayMode subclass.

        Assume we're already in chunk's local coordinate system (i.e. do all
        drawing using atom coordinates in chunk.basepos, not chunk.atpos).

        If highlighted is true, draw it in hover-highlighted form (but note 
        that it may have already been drawn in unhighlighted form in the same
        frame, so normally the highlighted form should augment or obscure the
        unhighlighted form).

        Draw it as unselected, whether or not chunk.picked is true. See also
        self.drawchunk_selection_frame. (The reason that's a separate method
        is to permit future drawing optimizations when a chunk is selected
        or deselected but does not otherwise change in appearance or position.)

        If this drawing requires info about chunk which it is useful to 
        precompute (as an optimization), that info should be computed by our
        compute_memo method and will be passed as the memo argument
        (whose format and content is whatever self.compute_memo returns). 
        That info must not depend on the highlighted variable or on whether
        the chunk is selected.        
        """

        def drawStrand(points, colors, radii, color_style, shape, arrows):
            """
            Renders a strand shape along points array using colors 
            and radii arrays, optionally with arrows. 
            """
            n = len(points)
            if n>3:
                # copy colors and radii
                colors[0] = colors[1]
                colors[n-1] = colors[n-2]
                radii[0] = radii[1]
                radii[n-1] = radii[n-2]
                # draw the terminal spheres
                drawer.drawsphere(colors[1],points[1],radii[1],2) 
                drawer.drawsphere(colors[n-2],points[n-2],radii[1],2) 
                if shape==1: # draw cylinders
                    gleSetJoinStyle(TUBE_JN_ROUND | TUBE_NORM_PATH_EDGE 
                                    | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)        
                    #drawer.drawpolycone(colors[1], 
                    #                    points,
                    #                    radii)
                    if color_style==1:
                        drawer.drawpolycone_multicolor(colors[1], 
                                                       points,
                                                       colors,
                                                       radii)
                    else:
                        drawer.drawpolycone(colors[1], 
                                            points,
                                            radii)
                elif shape==2: # draw spline tube
                    gleSetJoinStyle(TUBE_JN_ANGLE | TUBE_NORM_PATH_EDGE 
                                    | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED)                    
                    new_points = zeros([4*(n-2)-1,3],Float)
                    new_colors = zeros([4*(n-2)-1,3],Float)
                    new_radii = zeros([4*(n-2)-1],Float)
                    o = 1
                    for p in range (1,n-2):
                        for m in range (0,4):
                            t = float(m)/4.0
                            new_points[o] = self.spline(points, p, t)
                            new_colors[o] = self.spline(colors, p, t)
                            new_radii[o] = self.spline(radii, p, t)
                            o += 1        
                    new_points[o] = self.spline(points, p, 1.0)
                    new_colors[o] = self.spline(colors, p, 1.0)
                    new_radii[o] = self.spline(radii, p, 1.0)
                    o += 1
                    new_points[0] = 3.0*new_points[1]-3.0*new_points[2]+new_points[3] 
                    new_points[o] = 3.0*new_points[o-1]-3.0*new_points[o-2]+new_points[o-3] 
                    # draw the tube
                    if color_style==1:
                        drawer.drawpolycone_multicolor(
                            colors[1], new_points, new_colors, new_radii)
                    else:
                        drawer.drawpolycone(
                            colors[1], new_points, new_radii)
            # draw the arrows
            if arrows==1 or arrows==3: # 5'
                drawer.drawpolycone(colors[1],
                                    [points[1],
                                     points[1],
                                     2.0*points[1]-points[2],
                                     2.0*points[1]-points[2]],
                                     [radii[1]*2.0,
                                      radii[1]*2.0,
                                      0.0,
                                      0.0])
            if arrows==2 or arrows==3: # 3'
                drawer.drawpolycone(colors[n-2],
                                    [points[n-2],
                                     points[n-2],
                                     2.0*points[n-2]-points[n-3],
                                     2.0*points[n-2]-points[n-3]],
                                     [radii[1]*2.0,
                                      radii[1]*2.0,
                                      0.0,
                                      0.0])

        # ---------------------------------------------------------------------

        if not memo: # nothing to render
            return

        if self.dnaExperimentalModeEnabled: 
            # experimental mode is drawn in drawchunk_realtime
            return

        strand_positions, strand_sequences, axis_positions, colors, radii, \
                        chunk_color, group_color, chunk_strand, num_strands \
                        = memo

        n_points = len(axis_positions)

        # render axis cylinder        
        if chunk.isAxisChunk(): # this is the DNA axis           
            if self.dnaStyleAxisShape>0:
                # spherical ends    
                if self.dnaStyleAxisTaper==4:
                    drawer.drawsphere(colors[1], 
                                      axis_positions[1], radii[1], 2)
                    drawer.drawsphere(colors[n_points-2], 
                                      axis_positions[n_points-2], radii[n_points-2], 2)                    
                # set polycone parameters
                gleSetJoinStyle(TUBE_JN_ANGLE | TUBE_NORM_PATH_EDGE 
                                | TUBE_JN_CAP | TUBE_CONTOUR_CLOSED) 
                # draw the polycone                
                if self.dnaStyleAxisColor==1 or self.dnaStyleAxisColor==2 \
                   or self.dnaStyleAxisColor==3: # render discrete colors                
                    drawer.drawpolycone_multicolor(colors[1], 
                                                   axis_positions, colors, radii)
                else:   
                    drawer.drawpolycone(colors[1], axis_positions, radii)

        elif chunk.isStrandChunk(): # strands, struts and bases 
            if self.dnaStyleStrandsShape>0: # render strands
                # handle the external bonds, if there are any
                for bond in chunk.externs:
                    if bond.atom1.molecule.dad==bond.atom2.molecule.dad: # same group
                        if bond.atom1.molecule!=bond.atom2.molecule: # but different chunks
                            drawer.drawcylinder(
                                colors[1], 
                                bond.atom1.posn()-chunk.center, 
                                bond.atom2.posn()-chunk.center, 
                                1.0*self.dnaStyleStrandsScale, True)   
                            """
                            if bond.atom1==chunk.ladder.strand_rails[chunk_strand].baseatoms[0]:
                                points[1] = bond.atom2.posn()-chunk.center
                            if bond.atom1==chunk.ladder.strand_rails[chunk_strand].baseatoms[n_bases-1]:
                                points[pos] = bond.atom2.posn()-chunk.center
                            if bond.atom2==chunk.ladder.strand_rails[chunk_strand].baseatoms[0]:
                                points[1] = bond.atom1.posn()-chunk.center
                            if bond.atom2==chunk.ladder.strand_rails[chunk_strand].baseatoms[n_bases-1]:
                                points[pos] = bond.atom1.posn()-chunk.center
                            """

                # draw the strand itself
                drawStrand(strand_positions[chunk_strand], 
                           colors, radii, 
                           self.dnaStyleStrandsColor, 
                           self.dnaStyleStrandsShape,
                           self.dnaStyleStrandsArrows)            

            # render struts
            if self.dnaStyleStrutsShape>0 and num_strands>1:
                for pos in range(1,n_points-1):
                    atom1_pos = strand_positions[chunk_strand][pos]
                    atom3_pos = strand_positions[1-chunk_strand][n_points-pos-1]                        

                    if self.dnaStyleStrutsShape==1: # strand-axis-strand
                        if chunk_strand==0:
                            atom2_pos = axis_positions[pos]
                        else:
                            atom2_pos = axis_positions[n_points-pos-1]

                    elif self.dnaStyleStrutsShape==2: # strand-strand
                        atom2_pos = 0.5*(atom1_pos+atom3_pos)
                    if self.dnaStyleStrutsColor==0:
                        color = chunk_color
                    elif self.dnaStyleStrutsColor==1:
                        color = self.getRainbowColorInRange(pos, n_points, 0.75, 1.0)                        
                    elif self.dnaStyleStrutsColor==2:
                        color = group_color
                    else:
                        color = self.getBaseColor(strand_sequences[chunk_strand][pos])

                    drawer.drawcylinder(color, atom1_pos, atom2_pos, 0.5*self.dnaStyleStrutsScale, True)

            # render bases
            if self.dnaStyleBasesShape>0:
                for pos in range(1,n_points-1):
                    atom_pos = strand_positions[chunk_strand][pos]
                    if self.dnaStyleBasesColor==0:
                        color = chunk_color
                    elif self.dnaStyleBasesColor==1:
                        if chunk_strand==0:
                            color = self.getRainbowColorInRange(pos-1, n_points-2, 0.75, 1.0)
                        else:
                            color = self.getRainbowColorInRange(n_points-pos+1, n_points, 0.75, 1.0)                        
                    elif self.dnaStyleBasesColor==2:
                        color = group_color
                    else:
                        color = self.getBaseColor(strand_sequences[chunk_strand][pos])
                    if self.dnaStyleBasesShape==1: # draw spheres
                        drawer.drawsphere(color, atom_pos, self.dnaStyleBasesScale, 2)
                    elif self.dnaStyleBasesShape==2 and num_strands>1: # draw a schematic 'cartoon' shape
                        atom1_pos = strand_positions[chunk_strand][pos]
                        atom3_pos = strand_positions[1-chunk_strand][n_points-pos-1]                        
                        if chunk_strand==0:
                            atom2_pos = axis_positions[pos]
                        else:
                            atom2_pos = axis_positions[n_points-pos-1]
                        # figure out a normal to the bases plane
                        v1 = atom1_pos-atom2_pos
                        v2 = atom1_pos-atom3_pos
                        normal = norm(cross(v1,v2))
                        bposn = atom1_pos+0.66*(atom2_pos-atom1_pos)
                        drawer.drawcylinder(
                            color, 
                            atom1_pos, 
                            bposn, 
                            0.25*self.dnaStyleBasesScale, True)
                        drawer.drawcylinder(
                            color, 
                            bposn-0.33*self.dnaStyleBasesScale*normal,
                            bposn+0.33*self.dnaStyleBasesScale*normal,
                            2.0*self.dnaStyleBasesScale, True)


    def drawchunk_selection_frame(self, glpane, chunk, selection_frame_color, memo, highlighted):
        """
        Given the same arguments as drawchunk, plus selection_frame_color, 
        draw the chunk's selection frame.

        (Drawing the chunk itself as well would not cause drawing errors
        but would presumably be a highly undesirable slowdown, especially if
        redrawing after selection and deselection is optimized to not have to
        redraw the chunk at all.)

        @note: in the initial implementation of the code that calls this method,
        the highlighted argument might be false whether or not we're actually
        hover-highlighted. And if that's fixed, then just as for drawchunk, 
        we might be called twice when we're highlighted, once with 
        highlighted = False and then later with highlighted = True.
        """
        drawchunk(self, glpane, chunk, selection_frame_color, memo, highlighted)
        return

    def drawchunk_realtime(self, glpane, chunk):
        """
        Draws the chunk style that may depend on a current view.
        These are experimental features, work in progress as of 080319.
        For the DNA style, draws base orientation indicators and strand labels.
        080321 piotr: added better label positioning
        and 
        """
        def drawFilledCircle(color, center, radius, normal):
            """
            Draws a filled circle. Extremely slow, should be moved
            to drawer and compiled into a display list.
            """
            glPushMatrix()
            glTranslatef(center[0], center[1], center[2])
            rQ = Q(V(0, 0, 1), normal)
            rotAngle = rQ.angle*180.0/pi
            glRotatef(rotAngle, rQ.x, rQ.y, rQ.z)
            glScalef(radius, radius, 1.0)            
            glColor3f(color[0], color[1], color[2])
            glBegin(GL_POLYGON)
            for ii in range(60):
                x = cos(ii*2.0*pi/60)
                y = sin(ii*2.0*pi/60)
                glVertex3f(x, y, 0.0)
            glEnd()    
            glPopMatrix()

        def realTextSize(text, fm):
            """
            Returns a pair of vectors corresponding to a width
            and a height vector of a rendered text. 

            @params: text - text to be measured
                     fm - font metrics created for the text font:
                     fm = QFontMetrics(font)

            @returns: (v1,v2) - pair of vector covering the text rectangle
                                expressed in world coordinates
            """
            textwidth = fm.width(text)
            textheight = fm.ascent()
            x0, y0, z0 = gluUnProject(0, 0, 0)
            x1, y1, z1 = gluUnProject(textwidth, 0, 0)
            x2, y2, z2 = gluUnProject(0, textheight, 0)
            return (V(x1-x0, y1-y0, z1-z0),V(x2-x0, y2-y0, z2-z0))

        def get_screen_position_of_strand_atom(strand_atom):
            """
            For a given strand atom, find its on-screen position.
            """
            axis_atom = strand_atom.axis_neighbor()
            if axis_atom:
                mol = axis_atom.molecule
                axis_atoms = mol.ladder.axis_rail.baseatoms
                n_bases = len(axis_atoms)
                pos = axis_atoms.index(axis_atom)
                atom0 = axis_atom
                if pos<n_bases-1:
                    atom1 = axis_atoms[pos+1]
                    dpos = atom1.posn()-atom0.posn()
                else:
                    atom1 = axis_atoms[pos-1]
                    atom2 = axis_atoms[pos]
                    dpos = atom2.posn()-atom1.posn()                           
                last_dpos = dpos
                dvec = norm(cross(dpos,glpane.out))
                pos0 = axis_atom.posn()#-mol.center
                pos1 = pos0+7.0*dvec
                pos2 = pos0-7.0*dvec
                if mol.ladder.strand_rails[0].baseatoms[pos]==strand_atom:
                    return pos1
                elif mol.ladder.strand_rails[1].baseatoms[pos]==strand_atom:
                    return pos2

            return None
        
        from utilities.constants import lightgreen
        from PyQt4.Qt import QFont, QString, QColor, QFontMetrics
        from widgets.widget_helpers import RGBf_to_QColor
        from dna.model.DnaLadderRailChunk import DnaStrandChunk

        labels_enabled = env.prefs[dnaStrandLabelsEnabled_prefs_key]
        indicators_enabled = env.prefs[dnaBaseIndicatorsEnabled_prefs_key]

        if chunk.color: # sometimes the chunk.color is not defined
            chunk_color = chunk.color
        else:
            chunk_color = white

        if indicators_enabled: # draw the orientation indicators
            self.dnaStyleStrandsShape = env.prefs[dnaStyleStrandsShape_prefs_key]
            self.dnaStyleStrutsShape = env.prefs[dnaStyleStrutsShape_prefs_key]
            self.dnaStyleBasesShape = env.prefs[dnaStyleBasesShape_prefs_key]
            indicators_angle = env.prefs[dnaBaseIndicatorsAngle_prefs_key]
            indicators_color = env.prefs[dnaBaseIndicatorsColor_prefs_key]
            if chunk.isStrandChunk(): 
                if chunk.ladder.axis_rail:
                    if self.dnaStyleStrandsShape>0 or \
                       self.dnaStyleBasesShape>0 or \
                       self.dnaStyleStrutsShape>0:                   
                        n_bases = chunk.ladder.baselength()
                        if chunk==chunk.ladder.strand_rails[0].baseatoms[0].molecule:
                            chunk_strand = 0
                        else:
                            chunk_strand = 1
                        for pos in range(0,n_bases):
                            atom1 = chunk.ladder.strand_rails[chunk_strand].baseatoms[pos]
                            atom2 = chunk.ladder.axis_rail.baseatoms[pos]
                            vz = glpane.out 
                            v2 = norm(atom1.posn()-atom2.posn())
                            # calculate an angle between this vector 
                            # and the vector towards the viewer
                            a = angleBetween(vz, v2)
                            if abs(a)<indicators_angle:
                                drawer.drawsphere(
                                    indicators_color, 
                                    atom1.posn()-chunk.center, 1.5, 2)

        if labels_enabled and not self.dnaExperimentalModeEnabled: 
            # draw the strand labels

            self.dnaStyleStrandsShape = env.prefs[dnaStyleStrandsShape_prefs_key]
            self.dnaStyleStrutsShape = env.prefs[dnaStyleStrutsShape_prefs_key]
            self.dnaStyleBasesShape = env.prefs[dnaStyleBasesShape_prefs_key]

            labels_color_mode = env.prefs[dnaStrandLabelsColorMode_prefs_key]

            if labels_color_mode==1:
                labels_color = black
            elif labels_color_mode==2:
                labels_color = white
            else: 
                labels_color = env.prefs[dnaStrandLabelsColor_prefs_key]

            # calculate the text size
            # this is kludgy...
            font_scale = int(500.0/glpane.scale)
            if sys.platform == "darwin":
                font_scale *= 2                        
            if font_scale<9: font_scale = 9
            if font_scale>50: font_scale = 50

            if chunk.isStrandChunk():                
                if self.dnaStyleStrandsShape>0 or \
                   self.dnaStyleBasesShape>0 or \
                   self.dnaStyleStrutsShape>0:                   

                    # the following is copied from DnaStrand.py
                    # I need to find a 5' sugar atom of the strand
                    # is there any more efficient way of doing that?
                    # this is terribly slow... I need something like
                    # "get_strand_chunks_in_bond_direction"...             


                    strandGroup = chunk.parent_node_of_class(chunk.assy.DnaStrand)
                    if strandGroup is None:
                        strand = chunk
                    else:
                            #dna_updater case which uses DnaStrand object for 
                            #internal DnaStrandChunks
                        strand = strandGroup                  

                    # the label is positioned at 5' end of the strand
                    # get the 5' strand atom
                    atom = strand.get_five_prime_end_base_atom()

                    # and the next atom for extra positioning
                    next_atom = atom.strand_next_baseatom(1)

                    if atom.molecule==chunk and atom and next_atom: 
                        # draw labels only for the first chunk

                        # vector to move the label slightly away from the atom center
                        halfbond = 0.5*(atom.posn()-next_atom.posn())

                        # create the label font
                        labelFont = QFont( QString("Helvetica"), font_scale)

                        # define a color of the label
                        if labels_color_mode==0:
                            glpane.qglColor(RGBf_to_QColor(chunk_color))
                        else:
                            glpane.qglColor(RGBf_to_QColor(labels_color))

                        # get font metrics to calculate text extents
                        fm = QFontMetrics(labelFont)
                        label_text = QString(strand.name)+QString(" ")
                        textsize = fm.width(label_text)

                        # calculate the text position
                        # move a bit into viewers direction
                        textpos = atom.posn()-chunk.center+halfbond+5.0*glpane.out 

                        # calculate shift for right aligned text
                        dx, dy = realTextSize(label_text, fm)

                        # check if the right alignment is necessary
                        if dot(glpane.right,halfbond)<0.0:
                            textpos -= dx

                        # center the label vertically
                        textpos -= 0.5*dy

                        # draw the label
                        glDisable(GL_LIGHTING)
                        glpane.renderText(textpos[0], textpos[1], textpos[2], 
                                          label_text, labelFont)
                        glEnable(GL_LIGHTING)

                    if self.dnaBaseLabelsEnabled: 
                        # calculate text size
                        # this is kludgy...
                        font_scale = int(500.0/glpane.scale)
                        if sys.platform == "darwin":
                            font_scale *= 2                        
                        if font_scale<9: font_scale = 9
                        if font_scale>50: font_scale = 50

                        # create the label font
                        labelFont = QFont( QString("Helvetica"), font_scale)
                        # get font metrics for the current font
                        fm = QFontMetrics(labelFont)
                        glpane.qglColor(RGBf_to_QColor(black))
                        # disable lighting
                        glDisable(GL_LIGHTING)            
                        for atom in chunk.atoms.itervalues():
                            # pre-compute atom position
                            textpos = atom.posn()-chunk.center+3.0*glpane.out
                            # get atom base name
                            label_text = QString(atom.getDnaBaseName())
                            # get text size in world coordinates
                            dx, dy = realTextSize(label_text, fm)
                            # move the text center to the atom position
                            textpos -= 0.5*(dx+dy)   
                            # render the text
                            glpane.renderText(textpos[0], textpos[1], textpos[2], 
                                              label_text, labelFont)                    

                        # done, enable lighting
                        glEnable(GL_LIGHTING)

        # render base names

        if self.dnaExperimentalModeEnabled and chunk.isAxisChunk():
            # very exprimental, kludgy, buggy and undocumented
            axis = chunk.ladder.axis_rail

            # rescale font size for OSX
            font_scale = int(500.0/glpane.scale)
            if sys.platform == "darwin":
                font_scale *= 2                        
            if font_scale<9: font_scale = 9
            if font_scale>100: font_scale = 100

            if axis:
                n_bases = len(chunk.ladder.axis_rail.baseatoms)

                atom0 = chunk.ladder.axis_rail.baseatoms[0]
                atom1 = chunk.ladder.axis_rail.baseatoms[n_bases-1]

                pos0 = atom0.posn()-chunk.center
                pos1 = atom1.posn()-chunk.center

                glDisable(GL_LIGHTING)
                glColor3f(0,0,0)

                # glLineWidth(5.0)
                glLineWidth(1.0+100.0/glpane.scale)
                #glBegin(GL_LINES)
                last_dpos = V(0,0,0)
                """
                for pos in range(0,n_bases):
                    a_atom = chunk.ladder.axis_rail.baseatoms[pos]
                    s1_atom = chunk.ladder.strand_rails[0].baseatoms[pos]
                    s2_atom = chunk.ladder.strand_rails[1].baseatoms[pos]

                    a_pos = a_atom.posn()-chunk.center
                    s1_pos = get_screen_postion_of_strand_atom(s1_atom)
                    s2_pos = get_screen_postion_of_strand_atom(s2_atom)

                    if s1_pos and s2_pos:
                        glVertex3f(a_pos[0], a_pos[1], a_pos[2])
                        glVertex3f(s1_pos[0], s1_pos[1], s1_pos[2])
                        glVertex3f(a_pos[0], a_pos[1], a_pos[2])
                        glVertex3f(s2_pos[0], s2_pos[1], s2_pos[2])

                glEnd()
                glEnable(GL_LIGHTING)

                return
                """

                labelFont = QFont( QString("Helvetica"), font_scale)
                fm = QFontMetrics(labelFont)
                glpane.qglColor(RGBf_to_QColor(black))

                glBegin(GL_LINES)
                # draw bases
                for pos in range(0,n_bases):
                    atom0 = chunk.ladder.axis_rail.baseatoms[pos]
                    if pos<n_bases-1:
                        atom1 = chunk.ladder.axis_rail.baseatoms[pos+1]
                        dpos = atom1.posn()-atom0.posn()
                    else:
                        atom1 = chunk.ladder.axis_rail.baseatoms[pos-1]
                        atom2 = chunk.ladder.axis_rail.baseatoms[pos]
                        dpos = atom2.posn()-atom1.posn()                           
                    last_dpos = dpos
                    dvec = norm(cross(dpos,glpane.out))
                    pos0 = atom0.posn()-chunk.center
                    # print "dvec = ", dvec
                    s_atom0 = chunk.ladder.strand_rails[0].baseatoms[pos]
                    s_atom1 = chunk.ladder.strand_rails[1].baseatoms[pos]
                    bvec = norm(s_atom0.posn()-s_atom1.posn())
                    #bvec = glpane.quat.unrot(dvec)
                    pos3 = pos0+7.0*dvec
                    pos4 = pos0-7.0*dvec
                    pos1 = pos3
                    pos2 = pos4
                    #angle = dot(bvec, dvec)
                    #if angle<0.0:
                    #    pos1 = pos4
                    #    pos2 = pos3
                    """
                    # this assignment should depend on a relative turn orientation
                    base_color = self.getBaseColor(s_atom0.getDnaBaseName())
                    #base_color = self.getFullRainbowColor(0.5*(angle+1.0))
                    glColor3f(base_color[0],base_color[1],base_color[2])
                    glVertex3f(pos0[0], pos0[1], pos0[2])
                    glVertex3f(pos1[0], pos1[1], pos1[2])
                    base_color = self.getBaseColor(s_atom1.getDnaBaseName())
                    #base_color = self.getFullRainbowColor(0.5*(angle+1.0))
                    glColor3f(base_color[0],base_color[1],base_color[2])
                    glVertex3f(pos0[0], pos0[1], pos0[2])
                    glVertex3f(pos2[0], pos2[1], pos2[2])

                    #dpos = norm(dpos)
                    #angle = dot(glpane.out,bvec)
                    #print "dpos = ", dpos
                    #print "bvec = ", bvec

                    #print "angle = ", angle

                    #base_color = self.getFullRainbowColor(0.5*(angle+1.0))
                    #glColor3f(base_color[0],base_color[1],base_color[2])
                    glColor3f(0,0,0)
                    """
                    glEnd()

                    textpos = pos0+0.5*(pos1-pos0)
                    label_text = QString(s_atom0.getDnaBaseName())
                    dx, dy = realTextSize(label_text, fm)
                    textpos -= 0.5*(dx+dy)  
                    base_color = self.getBaseColor(s_atom0.getDnaBaseName())
                    glColor3f(base_color[0],base_color[1],base_color[2])
                    glpane.renderText(textpos[0], textpos[1], textpos[2], 
                                      label_text, labelFont)                    

                    textpos = pos0+0.5*(pos2-pos0)
                    label_text = QString(s_atom1.getDnaBaseName())
                    dx, dy = realTextSize(label_text, fm)
                    textpos -= 0.5*(dx+dy)  
                    base_color = self.getBaseColor(s_atom1.getDnaBaseName())
                    glColor3f(base_color[0],base_color[1],base_color[2])
                    glpane.renderText(textpos[0], textpos[1], textpos[2], 
                                      label_text, labelFont)                    

                    drawFilledCircle(black, pos0, 0.5, glpane.out)
                    glBegin(GL_LINES)

                    if pos>0:
                        glColor3f(s_atom0.molecule.color[0],
                                  s_atom0.molecule.color[1],
                                  s_atom0.molecule.color[2])
                        glVertex3f(last_pos3[0],last_pos3[1],last_pos3[2])
                        glVertex3f(pos3[0],pos3[1],pos3[2])
                        glColor3f(s_atom1.molecule.color[0],
                                  s_atom1.molecule.color[1],
                                  s_atom1.molecule.color[2])
                        glVertex3f(pos4[0],pos4[1],pos4[2])
                        glVertex3f(last_pos4[0],last_pos4[1],last_pos4[2])


                    last_pos1 = pos1
                    last_pos2 = pos2
                    last_pos3 = pos3
                    last_pos4 = pos4

                # draw arrows on endatoms                    
                endatoms = (chunk.ladder.axis_rail.baseatoms[0],
                            chunk.ladder.axis_rail.baseatoms[n_bases-1])

                for atom in endatoms:
                    neighbors = atom.strand_neighbors()
                    for strand_atom in neighbors:
                        strand_chunk = strand_atom.molecule
                        strand = strand_chunk.parent_node_of_class(
                            strand_chunk.assy.DnaStrand)
                        if strand_atom==strand.get_three_prime_end_base_atom():
                            glColor3f(strand_atom.molecule.color[0],
                                      strand_atom.molecule.color[1],
                                      strand_atom.molecule.color[2])
                            a_neighbors = atom.axis_neighbors()
                            dvec = atom.posn()-a_neighbors[0].posn()
                            ovec = norm(cross(dvec,glpane.out))
                            pos0 = atom.posn() - chunk.center + 7.0*ovec
                            pos1 = pos0 + dvec 
                            glVertex3f(pos0[0], pos0[1], pos0[2])
                            glVertex3f(pos1[0], pos1[1], pos1[2])
                            dvec = norm(dvec)
                            avec2 = pos1-0.5*(dvec-ovec)-1.0*dvec
                            glVertex3f(pos1[0],pos1[1],pos1[2])
                            glVertex3f(avec2[0],avec2[1],avec2[2])
                            avec3 = pos1-0.5*(dvec+ovec)-1.0*dvec
                            glVertex3f(pos1[0], pos1[1], pos1[2])
                            glVertex3f(avec3[0], avec3[1], avec3[2])

                glEnd()

                """
                neighbors = endatoms[0].strand_neighbors()
                s = 1
                for strand_atom in neighbors:
                    strand_chunk = strand_atom.molecule
                    print "drawing strand ", strand_chunk
                    for atom in strand_chunk.atoms.itervalues():
                        axis_atom = atom.axis_neighbor()
                        if axis_atom:
                            a_neighbors = axis_atom.axis_neighbors()
                            if axis_atom.index<a_neighbors[0].index:
                                idx = -1
                            else:
                                idx = 1
                            dvec = axis_atom.posn()-a_neighbors[0].posn()
                            ovec = norm(cross(dvec,glpane.out))
                            pos0 = axis_atom.posn() - axis_atom.molecule.center + 7.0*s*idx*ovec                                        
                            drawFilledCircle(strand_chunk.color, pos0, 0.5, glpane.out)
                    s *= -1 # next strand            
                """
                
                axis_atoms = chunk.ladder.axis_rail.baseatoms
                """
                neighbors = endatoms[0].strand_neighbors()
                for strand_atom in neighbors:
                    strand_chunk = strand_atom.molecule
                    for atom in strand_chunk.atoms.itervalues():
                        if atom:
                            pos = get_screen_position_of_strand_atom(atom)
                            if pos:
                                drawFilledCircle(atom.molecule.color, pos, 0.5, glpane.out)
                """
                
                
                glBegin(GL_LINES)
                # draw external bonds
                neighbors = endatoms[0].strand_neighbors()
                for strand_atom in neighbors:
                    strand_chunk = strand_atom.molecule
                    for bond in strand_chunk.externs:
                        if bond.atom1.molecule.dad==bond.atom2.molecule.dad: # same group
                            if bond.atom1.molecule!=bond.atom2.molecule: # but different chunks
                                pos0 = get_screen_position_of_strand_atom(bond.atom1)
                                pos1 = get_screen_position_of_strand_atom(bond.atom2)
                                if pos0 and pos1:
                                    pos0 -= chunk.center
                                    pos1 -= chunk.center
                                    glColor3f(bond.atom1.molecule.color[0],
                                              bond.atom1.molecule.color[1],
                                              bond.atom1.molecule.color[2])
                                    glVertex3f(pos0[0], pos0[1], pos0[2])
                                    glVertex3f(pos1[0], pos1[1], pos1[2])
                                
                glEnd() # end line drawing

                # line width should be restored to initial value
                # but I think 1.0 is maintained within the program
                glLineWidth(1.0) 

    def writepov(self, chunk, memo, file):
        """
        Renders the chunk to a POV-Ray file.
        This is an experimental feature as of 080319.
        """

        from graphics.rendering.povray.povheader import povpoint
        from geometry.VQT import vlen

        def writetube(points, colors, radii, rainbow, smooth):
            """ 
            Writes a smooth tube in a POV-Ray format.
            """
            file.write("sphere_sweep {\n")
            if smooth==True:
                file.write("  cubic_spline\n")
            else:
                file.write("  cubic_spline\n")
            file.write("  %d,\n" % (len(points)-2))
            n = len(points)-1
            for i in range(1,n):
                file.write("  " + povpoint(points[i]) +", %d\n" % radii[i]);
            file.write("  pigment {\n")
            vec = points[n]-points[1]
            file.write("    gradient <%g,%g,%g> scale %g translate <%g,%g,%g>\n" % 
                       (vec[0], vec[1], vec[2], vlen(vec),
                        points[1][0], points[1][1], points[1][2]))
            file.write("    color_map { RainbowMap }\n")
            file.write("  }\n")
            file.write("}\n")

        def writecylinder(start, end, color):
            file.write("cylinder {\n")
            file.write("  " + povpoint(start) + ", " + povpoint(end))
            file.write(", %g\n" % (0.5*self.dnaStyleStrutsScale))
            file.write("  pigment {color <%g %g %g>}\n" % (color[0], color[1], color[2]))
            file.write("}\n")

        strand_positions, strand_sequences, axis_positions, colors, radii, \
                        chunk_color, group_color, chunk_strand, num_strands \
                        = memo

        # render axis cylinder        
        if chunk.isAxisChunk(): # this is the DNA axis           
            if self.dnaStyleAxisShape>0:
                if self.dnaStyleAxisShape==1: # shape 
                    is_spline = False # connected cylinders
                else:
                    is_spline = True # spline

                if self.dnaStyleAxisColor==1 or self.dnaStyleAxisColor==2:
                    is_rainbow = True
                else:
                    is_rainbow = False

                writetube(axis_positions, colors, radii, is_rainbow, is_spline)

        """                   
        # render the axis cylinder        
        if chunk.isAxisChunk(): # this is the DNA axis           
            if self.dnaStyleAxisShape>0:
                writetube(points, colors, radii, False, True)

        if chunk.isStrandChunk(): 
            # render strands  
            if self.dnaStyleStrandsShape>0:
                writetube(points, colors, radii, False)

            # render struts
            if self.dnaStyleStrutsShape>0:
                for pos in range(1,n_bases-1):
                    atom1 = strand_positions[chunk_strand][pos]
                    atom3 = strand_positions[1-chunk_strand][pos]
                    if self.dnaStyleStrutsShape==1:
                        atom2_pos = axis_positions[pos]
                    elif self.dnaStyleStrutsShape==2:
                        atom2_pos = 0.5*(atom1+atom3)
                    if self.dnaStyleStrutsColor==0 or chunk_selected:
                        color = chunk_color
                    elif self.dnaStyleStrutsColor==1:
                        color = self.getRainbowColorInRange(pos, n_bases, 0.75, 1.0)                        
                    elif self.dnaStyleStrutsColor==2:
                        color = group_color
                    else:
                        color = white ###self.getBaseColor(atom1.getDnaBaseName())
                    writecylinder(atom1.posn(),atom2.posn(),color)
        """


    def compute_memo(self, chunk):
        """
        If drawing chunks in this display mode can be optimized by precomputing
        some info from chunk's appearance, compute that info and return it.

        If this computation requires preference values, access them as 
        env.prefs[key], and that will cause the memo to be removed (invalidated)
        when that preference value is changed by the user.

        This computation is assumed to also depend on, and only on, chunk's
        appearance in ordinary display modes (i.e. it's invalidated whenever
        havelist is). There is not yet any way to change that, so bugs will 
        occur if any ordinarily invisible chunk info affects this rendering,
        and potential optimizations will not be done if any ordinarily visible
        info is not visible in this rendering. These can be fixed if necessary
        by having the real work done within class Chunk's _recompute_ rules,
        with this function or drawchunk just accessing the result of that
        (and sometimes causing its recomputation), and with whatever 
        invalidation is needed being added to appropriate setter methods of 
        class Chunk. If the real work can depend on more than chunk's ordinary
        appearance can, the access would need to be in drawchunk;
        otherwise it could be in drawchunk or in this method compute_memo().

        @param chunk: The chunk.
        @type  chunk: chunk
        """

        # for this example, we'll turn the chunk axes into a cylinder.
        # Since chunk.axis is not always one of the vectors chunk.evecs 
        # (actually chunk.poly_evals_evecs_axis[2]),
        # it's best to just use the axis and center, then recompute 
        # a bounding cylinder.

        if not chunk.atoms or not chunk.ladder: # nothing to display 
            return None

        n_bases = chunk.ladder.baselength()    
        if n_bases<1: # no bases? quit
            return

        chunk_center = chunk.center
        if chunk.color:
            chunk_color = chunk.color
        else:
            chunk_color = white

        # import the style preferences from User Preferences
        self.dnaStyleStrandsShape = env.prefs[dnaStyleStrandsShape_prefs_key]
        self.dnaStyleStrandsColor = env.prefs[dnaStyleStrandsColor_prefs_key]
        self.dnaStyleStrandsScale = env.prefs[dnaStyleStrandsScale_prefs_key]
        self.dnaStyleStrandsArrows = env.prefs[dnaStyleStrandsArrows_prefs_key]        
        self.dnaStyleAxisShape = env.prefs[dnaStyleAxisShape_prefs_key]
        self.dnaStyleAxisColor = env.prefs[dnaStyleAxisColor_prefs_key]
        self.dnaStyleAxisScale = env.prefs[dnaStyleAxisScale_prefs_key]
        self.dnaStyleAxisTaper = env.prefs[dnaStyleAxisTaper_prefs_key]
        self.dnaStyleStrutsShape = env.prefs[dnaStyleStrutsShape_prefs_key]
        self.dnaStyleStrutsColor = env.prefs[dnaStyleStrutsColor_prefs_key]
        self.dnaStyleStrutsScale = env.prefs[dnaStyleStrutsScale_prefs_key]                
        self.dnaStyleBasesShape = env.prefs[dnaStyleBasesShape_prefs_key]
        self.dnaStyleBasesColor = env.prefs[dnaStyleBasesColor_prefs_key]
        self.dnaStyleBasesScale = env.prefs[dnaStyleBasesScale_prefs_key]

        # render experimental mode?
        self.dnaExperimentalModeEnabled = debug_pref(
            "DNA Cylinder Style: enable experimental 2D mode?",
            Choice_boolean_False,
            prefs_key = True,
            non_debug = True )

        # render base names?
        self.dnaBaseLabelsEnabled = debug_pref(
            "DNA Cylinder Style: display DNA base names?",
            Choice_boolean_False,
            prefs_key = True,
            non_debug = True )


        strand_positions = axis_positions = None
        strand_sequence = None

        num_strands = chunk.ladder.num_strands()

        strand_atoms = [None, None]
        strand_sequences = [None, None]
        axis_atoms = None

        # get lists of atom positions and sequences
        for n in range(0,num_strands):
            strand_atoms[n] = chunk.ladder.strand_rails[n].baseatoms;

        if num_strands>0 and chunk.ladder.axis_rail:
            axis_atoms = chunk.ladder.axis_rail.baseatoms

        strand_positions = zeros([num_strands,n_bases+2,3],Float)
        axis_positions = zeros([n_bases+2,3],Float)

        for n in range(0, num_strands):
            strand_sequences[n] = [' ']
            for pos in range (0,n_bases):
                if n==0:
                    strand_positions[n][pos+1] = strand_atoms[n][pos].posn()-chunk.center
                    strand_sequences[n].append(chunk.ladder.strand_rails[n].baseatoms[pos].getDnaBaseName())
                else:            
                    strand_positions[n][pos+1] = strand_atoms[n][n_bases-pos-1].posn()-chunk.center
                    strand_sequences[n].append(chunk.ladder.strand_rails[n].baseatoms[n_bases-pos-1].getDnaBaseName())
            strand_sequences[n].append(' ')

        if chunk.ladder.axis_rail: 
            for pos in range (0,n_bases):
                axis_positions[pos+1] = chunk.ladder.axis_rail.baseatoms[pos].posn()-chunk.center

        n_points = 0        
        chunk_strand = 0

        colors = zeros([n_bases+2,3],Float)
        radii = zeros([n_bases+2],Float)                            

        group_color = white

        # process the axis cylinder        
        if chunk.isAxisChunk() and axis_atoms: # this is the DNA axis           
            if self.dnaStyleAxisShape>0:
                # get the group color (axis chunks order)
                axis_chunks = chunk.getDnaGroup().getAxisChunks()
                group_color = self.getRainbowColorInRange(
                    axis_chunks.index(chunk), len(axis_chunks), 0.75, 1.0)                             
                if self.dnaStyleAxisShape==1:
                    rad = 7.0*self.dnaStyleAxisScale
                else:    
                    rad = 2.0*self.dnaStyleAxisScale
                if self.dnaStyleAxisColor==2 or self.dnaStyleAxisColor==3: # render discrete colors
                    axis_positions = zeros([2*n_bases+2,3],Float) # re-alloc the arrays
                    colors = zeros([2*n_bases+2,3],Float)
                    radii = zeros([2*n_bases+2],Float)                
                    pos = 2
                    for base in range (1,n_bases):
                        pos1 = axis_atoms[base-1].posn()-chunk.center
                        pos2 = axis_atoms[base].posn()-chunk.center                
                        if self.dnaStyleAxisColor==2: 
                            color1 = self.getRainbowColorInRange(
                                base-1, n_bases, 0.75, 1.0)
                            color2 = self.getRainbowColorInRange(
                                base, n_bases, 0.75, 1.0)
                        else:
                            color1 = self.getBaseColor(
                                axis_atoms[base-1].getDnaBaseName())
                            color2 = self.getBaseColor(
                                axis_atoms[base].getDnaBaseName())
                        axis_positions[pos] = 0.5*(pos1+pos2)
                        colors[pos] = color1
                        radii[pos] = rad
                        axis_positions[pos+1] = 0.5*(pos1+pos2)
                        colors[pos+1] = color2
                        radii[pos+1] = rad
                        pos += 2
                    radii[1] = radii[2*n_bases] = rad
                    axis_positions[1] = \
                                  chunk.ladder.axis_rail.baseatoms[0].posn()-chunk.center
                    colors[1] = colors[2]           
                    axis_positions[2*n_bases] = \
                                  chunk.ladder.axis_rail.baseatoms[n_bases-1].posn()-chunk.center
                    colors[2*n_bases] = colors[2*n_bases-1]
                    pos = 2*n_bases+1
                    # taper the ends
                    if self.dnaStyleAxisTaper==2 or self.dnaStyleAxisTaper==3:
                        radii[1] = 0.0
                        radii[2] = 0.5*rad
                        radii[3] = 0.5*rad
                    if self.dnaStyleAxisTaper==1 or self.dnaStyleAxisTaper==3:
                        radii[pos-3] = 0.5*rad
                        radii[pos-2] = 0.5*rad
                        radii[pos-1] = 0.0
                else:
                    for pos in range (1,n_bases+1):
                        axis_positions[pos] = axis_atoms[pos-1].posn()-chunk.center
                        if self.dnaStyleAxisColor==0 or chunk.picked:
                            colors[pos] = chunk_color
                        elif self.dnaStyleAxisColor==1:
                            colors[pos] = self.getRainbowColorInRange(pos-1, 
                                                                      n_bases, 
                                                                      0.75, 
                                                                      1.0)
                        else:
                            colors[pos] = group_color
                        radii[pos] = rad
                        pos += 1
                    # taper the ends
                    if self.dnaStyleAxisTaper==2 or self.dnaStyleAxisTaper==3:
                        radii[1] = 0.0
                        radii[2] = 0.66*rad
                    if self.dnaStyleAxisTaper==1 or self.dnaStyleAxisTaper==3:
                        radii[pos-2] = 0.66*rad
                        radii[pos-1] = 0.0        

                # compute dummy first and last coordinates    
                axis_positions[0] = \
                              2.0*axis_positions[1]-axis_positions[2]   
                axis_positions[pos] = \
                              2.0*axis_positions[pos-1]-axis_positions[pos-2]

        elif chunk.isStrandChunk(): # strands, struts and bases            
            if chunk==chunk.ladder.strand_rails[0].baseatoms[0].molecule:
                chunk_strand = 0
            else:
                chunk_strand = 1

            # figure out the color according to strand order
            strands = chunk.getDnaGroup().getStrands()
            group_color = self.getRainbowColorInRange(
                strands.index(chunk.dad), len(strands), 0.75, 1.0)

            # render strands        
            if self.dnaStyleStrandsShape>0:
                for pos in range (1,n_bases+1):
                    if self.dnaStyleStrandsColor==0 or chunk.picked:
                        colors[pos] = chunk_color
                    elif self.dnaStyleStrandsColor==1:
                        colors[pos] = self.getRainbowColorInRange(pos-1, 
                                                                  n_bases, 
                                                                  0.75, 1.0)
                    else:
                        colors[pos] = group_color
                    radii[pos] = 1.0*self.dnaStyleStrandsScale
                # compute first and last dummy atom coordinates 
                if n_bases>3:
                    strand_positions[chunk_strand][0] = \
                                    3.0*strand_positions[chunk_strand][1] \
                                    - 3.0*strand_positions[chunk_strand][2] \
                                    + strand_positions[chunk_strand][3]              
                    strand_positions[chunk_strand][pos+1] = \
                                    3.0*strand_positions[chunk_strand][pos] \
                                    - 3.0*strand_positions[chunk_strand][pos-1] \
                                    + strand_positions[chunk_strand][pos-2]                       
                else:
                    strand_positions[chunk_strand][0] = \
                                    2.0*strand_positions[chunk_strand][1] \
                                    - strand_positions[chunk_strand][2] 
                    strand_positions[chunk_strand][pos+1] = \
                                    2.0*strand_positions[chunk_strand][pos] \
                                    - strand_positions[chunk_strand][pos-1] 

        return (strand_positions, strand_sequences, axis_positions, 
                colors, radii, chunk_color, group_color, chunk_strand, num_strands)

    pass # end of class DnaCylinderChunks

ChunkDisplayMode.register_display_mode_class(DnaCylinderChunks)

# end
