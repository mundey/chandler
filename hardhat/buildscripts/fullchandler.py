# Chandler blueprint for new build process

"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

# To appease older Pythons:
True = 1
False = 0


import os, hardhatutil, hardhatlib, sys, re

path = os.environ.get('PATH', os.environ.get('path'))
whereAmI = os.path.dirname(os.path.abspath(hardhatlib.__file__))
cvsProgram = hardhatutil.findInPath(path, "cvs")
treeName = "Chandler"
mainModule = 'chandler'
logPath = 'hardhat.log'

def Start(hardhatScript, workingDir, cvsVintage, buildVersion, clobber, log):

    global buildenv, changes

    try:
        buildenv = hardhatlib.defaults
        buildenv['root'] = workingDir
        buildenv['hardhatroot'] = whereAmI
        hardhatlib.init(buildenv)
    
    except hardhatlib.HardHatMissingCompilerError:
        print "Could not locate compiler.  Exiting."
        sys.exit(1)
    
    except hardhatlib.HardHatUnknownPlatformError:
        print "Unsupported platform, '" + os.name + "'.  Exiting."
        sys.exit(1)
    
    except hardhatlib.HardHatRegistryError:
        print
        print "Sorry, I am not able to read the windows registry to find" 
        print "the necessary VisualStudio complier settings.  Most likely you"
        print "are running the Cygwin python, which will hopefully be supported"
        print "soon.  Please download a windows version of python from:\n"
        print "http://www.python.org/download/"
        print
        sys.exit(1)
    
    except Exception, e:
        print "Could not initialize hardhat environment.  Exiting."
        print "Exception:", e
        traceback.print_exc()
        raise e
        sys.exit(1)
    
    # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)
    chanDir = os.path.join(workingDir, mainModule)
    # test if we've been thruough the loop at least once
    if clobber == 1:
        if os.path.exists(chanDir):
            hardhatutil.rmdirRecursive(chanDir)
            
    os.chdir(workingDir)

    # remove outputDir and create it
    outputDir = os.path.join(workingDir, "output")
    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)
    os.mkdir(outputDir)
    
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")
    
    if not os.path.exists(chanDir):
        # Initialize sources
        print "Setup source tree..."
        log.write("- - - - tree setup - - - - - - -\n")
        
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-q -z3", "checkout", cvsVintage, "external internal chandler"])
        hardhatutil.dumpOutputList(outputList, log)
    
        os.chdir(chanDir)
    
        # build release first, because on Windows, debug needs release libs (temp fix for bug 1468)
        for releaseMode in ('release', 'debug'):
            doBuild(releaseMode, workingDir, log, clean='')
            #   Create end-user, developer distributions
            print "Making distribution files for " + releaseMode
            log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
            log.write("Making distribution files for " + releaseMode + "\n")
            if releaseMode == "debug":
                distOption = "-dD"
            else:
                distOption = "-D"
                
            outputList = hardhatutil.executeCommandReturnOutput(
             [hardhatScript, "-o", os.path.join(outputDir, buildVersion), distOption, buildVersionEscaped])
            hardhatutil.dumpOutputList(outputList, log)
            
            ret = Do(hardhatScript, releaseMode, workingDir, outputDir, 
              cvsVintage, buildVersion, log)
            CopyLog(os.path.join(workingDir, logPath), log)

        changes = "-first-run"
    else:
        os.chdir(chanDir)
    
        print "Checking CVS for updates"
        log.write("Checking CVS for updates\n")
        
        if changesInCVS(chanDir, workingDir, cvsVintage, log):
            log.write("Changes in CVS require build\n")
            changes = "-changes"
            for releaseMode in ('debug', 'release'):        
                doBuild(releaseMode, workingDir, log)
                
            log.write("Changes in CVS require making distributions\n")
            for releaseMode in ('debug', 'release'):        
                #   Create end-user, developer distributions
                print "Making distribution files for " + releaseMode
                log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
                log.write("Making distribution files for " + releaseMode + "\n")
                if releaseMode == "debug":
                    distOption = "-dD"
                else:
                    distOption = "-D"
                    
                outputList = hardhatutil.executeCommandReturnOutput(
                 [hardhatScript, "-o", os.path.join(outputDir, buildVersion), distOption, buildVersionEscaped])
                hardhatutil.dumpOutputList(outputList, log)
                    
        else:
            log.write("No changes\n")
            changes = "-nochanges"

        # do tests
        for releaseMode in ('debug', 'release'):   
            ret = Do(hardhatScript, releaseMode, workingDir, outputDir, 
              cvsVintage, buildVersion, log)
            CopyLog(os.path.join(workingDir, logPath), log)

    return ret + changes 


# These modules are the ones to check out of CVS
cvsModules = (
    'external', 'internal', 'chandler',
)

def Do(hardhatScript, mode, workingDir, outputDir, cvsVintage, buildVersion, log):

    testDir = os.path.join(workingDir, "chandler")
    os.chdir(testDir)

    if mode == "debug":
        dashT = '-dvt'
    else:
        dashT = '-vrt'
    
    try: # test
        print "Testing " + mode
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Testing " + mode + " ...\n")
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatScript, dashT])
        hardhatutil.dumpOutputList(outputList, log)

    except Exception, e:
        print "a testing error"
        log.write("***Error during tests*** " + str(e) + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Tests log:" + "\n")
        if os.path.exists(os.path.join(workingDir, logPath)) :
            CopyLog(os.path.join(workingDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        return "test_failed"
    else:
        log.write("Tests successful" + "\n")
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
        log.write("Detailed Tests log:" + "\n")
        if os.path.exists(os.path.join(workingDir, logPath)) :
            CopyLog(os.path.join(workingDir, logPath), log)
        log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    return "success"  # end of Do( )

def changesInCVS(moduleDir, workingDir, cvsVintage, log):
    changesAtAll = False
#     print "Examining CVS"
#     log.write("Examining CVS\n")
    for module in cvsModules:
        print module, "..."
        log.write("- - - - " + module + " - - - - - - -\n")
        moduleDir = os.path.join(workingDir, module)
        os.chdir(moduleDir)
        # print "seeing if we need to update", module
        log.write("Seeing if we need to update " + module + "\n")
        outputList = hardhatutil.executeCommandReturnOutputRetry(
         [cvsProgram, "-qn -z3", "update", "-d", cvsVintage])
        # hardhatutil.dumpOutputList(outputList, log)
        if NeedsUpdate(outputList):
            changesAtAll = True
            print "" + module + " needs updating"
            # update it
            print "Getting changed sources"
            log.write("Getting changed sources\n")
            
            outputList = hardhatutil.executeCommandReturnOutputRetry(
            [cvsProgram, "-q -z3", "update", "-dAP"])
            hardhatutil.dumpOutputList(outputList, log)
        
        else:
            # print "NO, unchanged"
            log.write("Module unchanged" + "\n")

    log.write("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
    log.write("Done with CVS\n")
    return changesAtAll

def doBuild(buildmode, workingDir, log, clean='clean'):
    if buildmode == "debug":
        dbgStr = "DEBUG=1"
    else:
        dbgStr = ""

    buildRoot =  os.path.join(workingDir, 'external')
    print 'Setting BUILD_ROOT=', buildRoot
    log.write('Setting BUILD_ROOT=' + buildRoot + '\n')
    os.putenv('BUILD_ROOT', buildRoot)

    for mod in cvsModules:
        if mod == 'chandler':
            continue
        moduleDir = os.path.join(workingDir, mod)
        print "cd", moduleDir
        log.write("cd " + moduleDir + "\n")
        os.chdir(moduleDir)

        print "Doing make " + dbgStr + " " + clean + " all binaries install\n"
        log.write("Doing make " + dbgStr + " " + clean + " all binaries install\n")

        outputList = hardhatutil.executeCommandReturnOutput( [buildenv['make'], dbgStr, clean, "all binaries install" ])
        hardhatutil.dumpOutputList(outputList, log)
                

def NeedsUpdate(outputList):
    # XXX Make this smarter:
    # XXX   if external changed, need to build all
    # XXX   if internal changed, need to build changed internal dirs
    # XXX   if chandler changed, no need to build
    for line in outputList:
        if line.lower().find("ide scripts") != -1:
            # this hack is for skipping some Mac-specific files that
            # under Windows always appear to be needing an update
            continue
        if line.lower().find("xercessamples") != -1:
            # same type of hack as above
            continue
        if line[0] == "U":
            print "needs update because of", line
            return True
        if line[0] == "P":
            print "needs update because of", line
            return True
        if line[0] == "A":
            print "needs update because of", line
            return True
    return False

def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()

def getVersion(fileToRead):
    input = open(fileToRead, "r")
    line = input.readline()
    while line:
        if line == "\n":
            line = input.readline()
            continue
        else:
            m=re.match('VERSION=(.*)', line)
            if not m == 'None' or m == 'NoneType':
                version = m.group(1)
                input.close()
                return version

        line = input.readline()
    input.close()
    return 'No Version'
