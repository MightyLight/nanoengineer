# Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
"""
main_startup.py -- provides the startup_script function called by main.py

$Id$

History:

mostly unrecorded, except in cvs;
originally by Josh (under the name atom.py);
lots of changes by various developers at various times.

renamed from atom.py to main.py before release of A9, mid-2007,
and split out of main.py into this file (main_startup.py)
by bruce 070704.
"""

import sys, time

from startup import startup_before_most_imports
## from startup import startup_misc # do this after i svn move the file
import startup_funcs as startup_misc # do this before then #### TODO - fix this -- also do it lower down!

# NOTE: all other imports MUST be added inside the following function,
# since they must not be done before startup_before_most_imports.before_most_imports is executed.

def startup_script( main_globals):
    """
    This is the main startup script for NE1.
    It is intended to be run only once, and only by the code in main.py.
    When this function returns, the caller is intended to immediately exit
    normally.
       Parameter main_globals should be the value of globals() in __main__,
    which is needed in case .atom-debug-rc is executed, since it must be
    executed in that global namespace.
    """

    # Note: importing all of NE1's functionality can take a long time.
    # To the extent possible, we want that time to be spent after
    # something is visible to the user, but (mostly) before the main
    # window is shown to the user (since showing the main window implies
    # that NE1 is almost ready to go). So we display a splashscreen
    # before doing most imports and initializations, then set up most
    # of our data structures and UI commands (thus importing the code
    # needed to implement them), and then show the main window.
    # (Some experimental commands are initialized after that, so that
    # errors that occur then can't prevent the main window from becoming
    # visible.)

    # TODO: turn the sections of code below into named functions or methods,
    # and perhaps split before_most_imports and before_creating_app into
    # more named functions or methods. The biggest split should be between
    # functions that need to be careful to do very few or no imports,
    # and functions that are free to do any imports.
    

    # "Do things that should be done before most imports occur."
    
    startup_before_most_imports.before_most_imports( main_globals )


    from PyQt4.Qt import QApplication, QSplashScreen

    
    # "Do things that should be done before creating the application object."
    
    startup_before_most_imports.before_creating_app()
    

    # create the application object (an instance of QApplication).
    
    QApplication.setColorSpec(QApplication.CustomColor)
    app = QApplication(sys.argv)
    

    # do some imports used for putting up splashscreen
    
    import icon_utilities
    icon_utilities.initialize() 


    # Put up the splashscreen (if its image file can be found in cad/images).
    #    
    # Note for developers:
    # If you don't want the splashscreen, just rename the splash image file.

    splash_pixmap = icon_utilities.imagename_to_pixmap( "images/splash.png" )
        # splash_pixmap will be null if the image file was not found
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap) # create the splashscreen
        splash.show()
        MINIMUM_SPLASH_TIME = 3.0 
            # I intend to add a user pref for MINIMUM_SPLASH_TIME for A7. mark 060131.
        splash_start = time.time()
    else:
        print "note: splash.png was not found"


    # connect the lastWindowClosed signal
    
    from PyQt4.Qt import SIGNAL
    app.connect(app, SIGNAL("lastWindowClosed ()"), app.quit)


    # NOTE: At this point, it is ok to do arbitrary imports as needed,
    # except of experimental code.


    # import MWsemantics.
    
    # An old comment (I don't know if it's still true -- bruce 071008):
    # this might have side effects other than defining things.

    from MWsemantics import MWsemantics 


    # set up the value of debug_pref("Multipane GUI",...).
    # TODO: change this into a hardcoded flag and probably remove support for one value of it.
    
    from debug_prefs import debug_pref, Choice_boolean_True, Choice_boolean_False
    ##########################################################################################################
    #
    # The debug preference menu is now working in Qt 4 but you can't effectively change this debug
    # preference after the program has already come up, as too much of the GUI is already in place
    # by then. To change it, manually edit it here.
    #
    # [note added later: I suspect we are now dependent on this value of True and should
    #  should not leave the appearance that the False value is supported. I don't know for sure.
    #  [bruce 071005 comment]]
    #
    debug_pref("Multipane GUI", Choice_boolean_True)
    #debug_pref("Multipane GUI", Choice_boolean_False)
    #
    ##########################################################################################################


    # initialize modules and data structures
    
    startup_misc.call_module_init_functions()


    # create the single main window object
    
    foo = MWsemantics() # This does a lot of initialization (in MainWindow.__init__)

    import __main__
    __main__.foo = foo
        # developers often access the main window object using __main__.foo when debugging,
        # so this is explicitly supported


    # initialize CoNTubGenerator
    # TODO: move this into one of the other initialization functions
    
    import CoNTubGenerator
    CoNTubGenerator.initialize()


    # for developers: run a hook function that .atom-debug-rc might have defined
    # in this module's global namespace, for doing things *before* showing the
    # main window.
    
    try:
        # do this, if user asked us to by defining it in .atom-debug-rc
        meth = atom_debug_pre_main_show
    except:
        pass
    else:
        meth()


    # Do other things that should be done just before showing the main window
    
    startup_misc.pre_main_show(foo) # this sets foo's geometry, among other things
    
    foo._init_after_geometry_is_set()
    
    if not splash_pixmap.isNull():
        # If the MINIMUM_SPLASH_TIME duration has not expired, sleep for a moment.
        while time.time() - splash_start < MINIMUM_SPLASH_TIME:
            time.sleep(0.1)
        splash.finish( foo ) # Take away the splashscreen


    # show the main window
    
    foo.show() 


    # set up the sponsors system and perhaps show the permission dialog
    
    if sys.platform != 'darwin':
        #bruce 070515 added condition to disable this on Mac, until Brian fixes the hang on Mac.
        # Note: this is enabled in the Mac released version, due to a patch during the release
        # building process, at least in A9.1.
        from Sponsors import PermissionDialog
##        print "start sponsors startup code"
        # Show the dialog that asks permission to download the sponsor logos, then
        # launch it as a thread to download and process the logos.
        #
        permdialog = PermissionDialog(foo)
        if permdialog.needToAsk:
            permdialog.exec_()
        permdialog.start()
##        print "end sponsors startup code"


    # show the MMKit (I think this is obsolete and should be removed -- bruce 071008 comment)
    
    if not debug_pref("Multipane GUI", Choice_boolean_False):
        if foo.glpane.mode.modename == 'DEPOSIT':
            # Two problems are addressed here when nE-1 starts in Build (DEPOSIT) mode.
            # 1. The MMKit can cover the splashscreen (bug #1439).
            #   BTW, the other part of bug fix 1439 is in MWsemantics.modifyMMKit()
            # 2. The MMKit appears 1-3 seconds before the main window.
            # Both situations now resolved.  mark 060202
            # Should this be moved to startup_misc.post_main_show()? I chose to leave
            # it here since the splashscreen code it refers to is in this file.  mark 060202.
            foo.glpane.mode.MMKit.show()


    # for developers: run a hook function that .atom-debug-rc might have defined
    # in this module's global namespace, for doing things *after* showing the
    # main window.

    try:
        # do this, if user asked us to by defining it in .atom-debug-rc
        meth = atom_debug_post_main_show 
    except:
        pass
    else:
        meth()


    # do other things after showing the main window
    startup_misc.post_main_show(foo)


    # Decide whether to do profiling, and if so, with which
    # profiling command and into what file. Set local variables
    # to record the decision, which are used later when running
    # the Qt event loop.
    
    # If the user's .atom-debug-rc specifies PROFILE_WITH_HOTSHOT = True, use hotshot, otherwise
    # fall back to vanilla Python profiler.
    try:
        PROFILE_WITH_HOTSHOT
    except NameError:
        PROFILE_WITH_HOTSHOT = False
    
    try:
        # user can set this to a filename in .atom-debug-rc,
        # to enable profiling into that file
        atom_debug_profile_filename 
        if atom_debug_profile_filename:
            print "user's .atom-debug-rc requests profiling into file %r" % (atom_debug_profile_filename,)
            if not type(atom_debug_profile_filename) in [type("x"), type(u"x")]:
                print "error: atom_debug_profile_filename must be a string; running without profiling"
                assert 0 # caught and ignored, turns off profiling
            if PROFILE_WITH_HOTSHOT:
                try:
                    import hotshot
                except:
                    print "error during 'import hotshot'; running without profiling"
                    raise # caught and ignored, turns off profiling
            else:
                try:
                    import profile
                except:
                    print "error during 'import profile'; running without profiling"
                    raise # caught and ignored, turns off profiling
    except:
        atom_debug_profile_filename = None


    # Create a fake "current exception", to help with debugging
    # (in case it's shown inappropriately in a later traceback).
    # One time this is seen is if a developer inserts a call to print_compact_traceback
    # when no exception is being handled (instead of the intended print_compact_stack).
    try:
        assert 0, "if you see this exception in a traceback, it is from the" \
            " startup script called by main.py, not the code that printed the traceback"
    except:
        pass


    # Handle the optional startup argument, --initial-file .
    # TODO: figure out what this is for and what it does, and document it here.
    from platform import atom_debug
    if atom_debug:
        # Use a ridiculously specific keyword, so this isn't triggered accidentally.
        if len(sys.argv) >= 3 and sys.argv[1] == '--initial-file':
            # fileOpen gracefully handles the case where the file doesn't exist.
            foo.fileOpen(sys.argv[2])
            if len(sys.argv) > 3:
                import env
                from utilities.Log import orangemsg
                env.history.message(orangemsg("We can only import one file at a time."))


    # Finally, run the main Qt event loop --
    # perhaps with profiling, depending on local variables set above.
    # This does not normally return until the user asks NE1 to exit.
    
    # Note that there are three copies of the statement which runs that loop,
    # two inside string literals, all of which presumably should be the same.

    if atom_debug_profile_filename:
        if PROFILE_WITH_HOTSHOT:
            profile = hotshot.Profile(atom_debug_profile_filename)
            profile.run('app.exec_()')
        else:
            profile.run('app.exec_()', atom_debug_profile_filename)
        print "\nprofile data was presumably saved into %r" % (atom_debug_profile_filename,)
    else:
        # if you change this code, also change the string literal just above
        app.exec_() 


    # Now return to the caller in order to do a normal immediate exit of NE1.
    
    return # from startup_script

# end
