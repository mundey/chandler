/////////////////////////////////////////////////////////////////////////////
// Name:        _menu.i
// Purpose:     SWIG interface defs for wxMenuBar, wxMenu and wxMenuItem
//
// Author:      Robin Dunn
//
// Created:     24-June-1997
// RCS-ID:      $Id$
// Copyright:   (c) 2003 by Total Control Software
// Licence:     wxWindows license
/////////////////////////////////////////////////////////////////////////////

// Not a %module


//---------------------------------------------------------------------------
%newgroup


MustHaveApp(wxMenu);

class wxMenu : public wxEvtHandler
{
public:
    %pythonAppend wxMenu         "self._setOORInfo(self)"
    %typemap(out) wxMenu*;    // turn off this typemap

    wxMenu(const wxString& title = wxPyEmptyString, long style = 0);

    // Turn it back on again
    %typemap(out) wxMenu* { $result = wxPyMake_wxObject($1, $owner); }

    
    // append any kind of item (normal/check/radio/separator)
    wxMenuItem* Append(int id,
                       const wxString& text,
                       const wxString& help = wxPyEmptyString,
                       wxItemKind kind = wxITEM_NORMAL);

    // append a separator to the menu
    wxMenuItem* AppendSeparator();

    // append a check item
    wxMenuItem* AppendCheckItem(int id,
                                const wxString& text,
                                const wxString& help = wxPyEmptyString);

    // append a radio item
    wxMenuItem* AppendRadioItem(int id,
                                const wxString& text,
                                const wxString& help = wxPyEmptyString);
    // append a submenu
    %Rename(AppendMenu, wxMenuItem*, Append(int id,
                                           const wxString& text,
                                           wxMenu *submenu,
                                           const wxString& help = wxPyEmptyString));

    // the most generic form of Append() - append anything
    %Rename(AppendItem, wxMenuItem*, Append(wxMenuItem *item));

    // insert a break in the menu (only works when appending the items, not
    // inserting them)
    virtual void Break();

    // insert an item before given position
    %Rename(InsertItem, wxMenuItem*, Insert(size_t pos, wxMenuItem *item));

    // insert an item before given position
    wxMenuItem* Insert(size_t pos,
                       int id,
                       const wxString& text,
                       const wxString& help = wxPyEmptyString,
                       wxItemKind kind = wxITEM_NORMAL);

    // insert a separator
    wxMenuItem* InsertSeparator(size_t pos);

    // insert a check item
    wxMenuItem* InsertCheckItem(size_t pos,
                                int id,
                                const wxString& text,
                                const wxString& help = wxPyEmptyString);

    // insert a radio item
    wxMenuItem* InsertRadioItem(size_t pos,
                                int id,
                                const wxString& text,
                                const wxString& help = wxPyEmptyString);

    // insert a submenu
    %Rename(InsertMenu, wxMenuItem*, Insert(size_t pos,
                                         int id,
                                         const wxString& text,
                                         wxMenu *submenu,
                                         const wxString& help = wxPyEmptyString));

    // prepend an item to the menu
    %Rename(PrependItem,  wxMenuItem*, Prepend(wxMenuItem *item));

    // prepend any item to the menu
    wxMenuItem* Prepend(int id,
                        const wxString& text,
                        const wxString& help = wxPyEmptyString,
                        wxItemKind kind = wxITEM_NORMAL);

    // prepend a separator
    wxMenuItem*  PrependSeparator();

    // prepend a check item
    wxMenuItem* PrependCheckItem(int id,
                                 const wxString& text,
                                 const wxString& help = wxPyEmptyString);

    // prepend a radio item
    wxMenuItem*  PrependRadioItem(int id,
                                  const wxString& text,
                                  const wxString& help = wxPyEmptyString);

    // prepend a submenu
    %Rename(PrependMenu,  wxMenuItem*, Prepend(int id,
                                           const wxString& text,
                                           wxMenu *submenu,
                                           const wxString& help = wxPyEmptyString));

    // detach an item from the menu, but don't delete it so that it can be
    // added back later (but if it's not, the caller is responsible for
    // deleting it!)
    wxMenuItem *Remove(int id);
    %Rename(RemoveItem,  wxMenuItem*, Remove(wxMenuItem *item));

    // delete an item from the menu (submenus are not destroyed by this
    // function, see Destroy)
    bool Delete(int id);
    %Rename(DeleteItem,  bool, Delete(wxMenuItem *item));

    // delete the item from menu and destroy it (if it's a submenu)
    %extend { void Destroy() { delete self; } }
    %Rename(DestroyId,  bool, Destroy(int id));
    %Rename(DestroyItem,  bool, Destroy(wxMenuItem *item));


    // get the items
    size_t GetMenuItemCount() const;
    %extend {
        PyObject* GetMenuItems() {
            wxMenuItemList& list = self->GetMenuItems();
            return wxPy_ConvertList(&list);
        }
    }

    // search
    int FindItem(const wxString& item) const;
    %Rename(FindItemById, wxMenuItem*, FindItem(int id /*, wxMenu **menu = NULL*/) const);

    // find by position
    wxMenuItem* FindItemByPosition(size_t position) const;

    // get/set items attributes
    void Enable(int id, bool enable);
    bool IsEnabled(int id) const;

    void Check(int id, bool check);
    bool IsChecked(int id) const;

    void SetLabel(int id, const wxString& label);
    wxString GetLabel(int id) const;

    virtual void SetHelpString(int id, const wxString& helpString);
    virtual wxString GetHelpString(int id) const;


    // the title
    virtual void SetTitle(const wxString& title);
    const wxString GetTitle() const;

    // event handler
    void SetEventHandler(wxEvtHandler *handler);
    wxEvtHandler *GetEventHandler() const;

    // invoking window
    void SetInvokingWindow(wxWindow *win);
    wxWindow *GetInvokingWindow() const;

    // style
    long GetStyle() const { return m_style; }


    // Updates the UI for a menu and all submenus recursively. source is the
    // object that has the update event handlers defined for it. If NULL, the
    // menu or associated window will be used.
    void UpdateUI(wxEvtHandler* source = NULL);

    // get the menu bar this menu is attached to (may be NULL, always NULL for
    // popup menus)
    wxMenuBar *GetMenuBar() const;

// TODO:  Should these be exposed?
    // called when the menu is attached/detached to/from a menu bar
    virtual void Attach(wxMenuBarBase *menubar);
    virtual void Detach();

    // is the menu attached to a menu bar (or is it a popup one)?
    bool IsAttached() const;

    // set/get the parent of this menu
    void SetParent(wxMenu *parent);
    wxMenu *GetParent() const;
};

//---------------------------------------------------------------------------
%newgroup

MustHaveApp(wxMenuBar);

class wxMenuBar : public wxWindow
{
public:
    %pythonAppend wxMenuBar         "self._setOORInfo(self)"
    %typemap(out) wxMenuBar*;    // turn off this typemap

    wxMenuBar(long style = 0);

    // Turn it back on again
    %typemap(out) wxMenuBar* { $result = wxPyMake_wxObject($1, $owner); }

    // append a menu to the end of menubar, return True if ok
    virtual bool Append(wxMenu *menu, const wxString& title);

    // insert a menu before the given position into the menubar, return True
    // if inserted ok
    virtual bool Insert(size_t pos, wxMenu *menu, const wxString& title);


    // get the number of menus in the menu bar
    size_t GetMenuCount() const;

    // get the menu at given position
    wxMenu *GetMenu(size_t pos) const;

    // replace the menu at given position with another one, returns the
    // previous menu (which should be deleted by the caller)
    virtual wxMenu *Replace(size_t pos, wxMenu *menu, const wxString& title);

    // delete the menu at given position from the menu bar, return the pointer
    // to the menu (which should be  deleted by the caller)
    virtual wxMenu *Remove(size_t pos);

    // enable or disable a submenu
    virtual void EnableTop(size_t pos, bool enable);

    // is the menu enabled?
    virtual bool IsEnabledTop(size_t pos) const;

    // get or change the label of the menu at given position
    virtual void SetLabelTop(size_t pos, const wxString& label);
    virtual wxString GetLabelTop(size_t pos) const;


    // by menu and item names, returns wxNOT_FOUND if not found or id of the
    // found item
    virtual int FindMenuItem(const wxString& menu, const wxString& item) const;

    // find item by id (in any menu), returns NULL if not found
    //
    // if menu is !NULL, it will be filled with wxMenu this item belongs to
    %Rename(FindItemById, virtual wxMenuItem*, FindItem(int id /*, wxMenu **menu = NULL*/) const);

    // find menu by its caption, return wxNOT_FOUND on failure
    int FindMenu(const wxString& title);

 
    // all these functions just use FindItem() and then call an appropriate
    // method on it
    //
    // NB: under MSW, these methods can only be used after the menubar had
    //     been attached to the frame

    void Enable(int id, bool enable);
    void Check(int id, bool check);
    bool IsChecked(int id) const;
    bool IsEnabled(int id) const;
    // TODO: bool IsEnabled() const;
     
    void SetLabel(int id, const wxString &label);
    wxString GetLabel(int id) const;

    void SetHelpString(int id, const wxString& helpString);
    wxString GetHelpString(int id) const;

 
    // get the frame we are attached to (may return NULL)
    wxFrame *GetFrame() const;

    // returns True if we're attached to a frame
    bool IsAttached() const;

    // associate the menubar with the frame
    virtual void Attach(wxFrame *frame);

    // called before deleting the menubar normally
    virtual void Detach();

#ifdef __WXMAC__
    static void SetAutoWindowMenu( bool enable );
    static bool GetAutoWindowMenu();
#else
    %extend {
        static void SetAutoWindowMenu( bool enable ) {}
        static bool GetAutoWindowMenu() { return false; }
    }
#endif
};

//---------------------------------------------------------------------------
%newgroup

class wxMenuItem : public wxObject {
public:
    wxMenuItem(wxMenu* parentMenu=NULL, int id=wxID_ANY,
               const wxString& text = wxPyEmptyString,
               const wxString& help = wxPyEmptyString,
               wxItemKind kind = wxITEM_NORMAL,
               wxMenu* subMenu = NULL);

    // the menu we're in
    wxMenu *GetMenu() const;
    void SetMenu(wxMenu* menu);

    // get/set id
    void SetId(int id);
    int  GetId() const;
    bool IsSeparator() const;

    // the item's text (or name)
    //
    // NB: the item's text includes the accelerators and mnemonics info (if
    //     any), i.e. it may contain '&' or '_' or "\t..." and thus is
    //     different from the item's label which only contains the text shown
    //     in the menu
    virtual void SetText(const wxString& str);
    wxString GetLabel() const;
    const wxString& GetText() const;

    // get the label from text 
    static wxString GetLabelFromText(const wxString& text);

    // what kind of menu item we are
    wxItemKind GetKind() const;
    void SetKind(wxItemKind kind);

    virtual void SetCheckable(bool checkable);
    bool IsCheckable() const;

    bool IsSubMenu() const;
    void SetSubMenu(wxMenu *menu);
    wxMenu *GetSubMenu() const;

    // state
    virtual void Enable(bool enable = true);
    virtual bool IsEnabled() const;

    virtual void Check(bool check = true);
    virtual bool IsChecked() const;
    void Toggle();

    // help string (displayed in the status bar by default)
    void SetHelp(const wxString& str);
    const wxString& GetHelp() const;

    // get our accelerator or NULL (caller must delete the pointer)
    virtual wxAcceleratorEntry *GetAccel() const;

    // set the accel for this item - this may also be done indirectly with
    // SetText()
    virtual void SetAccel(wxAcceleratorEntry *accel);

    
    // wxOwnerDrawn methods
#ifdef __WXMSW__
    void SetFont(const wxFont& font);
    wxFont GetFont();
    void SetTextColour(const wxColour& colText);
    wxColour GetTextColour();
    void SetBackgroundColour(const wxColour& colBack);
    wxColour GetBackgroundColour();
    void SetBitmaps(const wxBitmap& bmpChecked,
                    const wxBitmap& bmpUnchecked = wxNullBitmap);
    
    void SetDisabledBitmap( const wxBitmap& bmpDisabled );
    const wxBitmap& GetDisabledBitmap() const;
   
    void SetMarginWidth(int nWidth);
    int GetMarginWidth();
    static int GetDefaultMarginWidth();
    bool IsOwnerDrawn();

    // switch on/off owner-drawing the item
    void SetOwnerDrawn(bool ownerDrawn = true);
    void ResetOwnerDrawn();
#else
    %extend {
        void SetFont(const wxFont& font) {}
        wxFont GetFont() { return wxNullFont; }
        void SetTextColour(const wxColour& colText) {}
        wxColour GetTextColour() { return wxNullColour; }
        void SetBackgroundColour(const wxColour& colBack) {}
        wxColour GetBackgroundColour() { return wxNullColour; }
        void SetBitmaps(const wxBitmap& bmpChecked,
                        const wxBitmap& bmpUnchecked = wxNullBitmap) {}
    
        void SetDisabledBitmap( const wxBitmap& bmpDisabled ) {}
        const wxBitmap& GetDisabledBitmap() const { return wxNullBitmap; }
   
        void SetMarginWidth(int nWidth) {}
        int GetMarginWidth() { return 0; }
        static int GetDefaultMarginWidth() { return 0; }
        bool IsOwnerDrawn() { return false; }
        void SetOwnerDrawn(bool ownerDrawn = true) {}
        void ResetOwnerDrawn() {}
    }
#endif

    void SetBitmap(const wxBitmap& bitmap);
    const wxBitmap& GetBitmap();
};

//---------------------------------------------------------------------------
//---------------------------------------------------------------------------
