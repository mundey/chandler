// A bunch of %rename directives generated by BuildRenamers in config.py
// in order to remove the wx prefix from all global scope names.

#ifndef BUILDING_RENAMERS

%rename(MEDIASTATE_STOPPED)                 wxMEDIASTATE_STOPPED;
%rename(MEDIASTATE_PAUSED)                  wxMEDIASTATE_PAUSED;
%rename(MEDIASTATE_PLAYING)                 wxMEDIASTATE_PLAYING;
%rename(MediaEvent)                         wxMediaEvent;
%rename(MediaCtrl)                          wxMediaCtrl;

#endif