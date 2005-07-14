#include "MoriartyPreferences.hpp"
#include "PreferencesForm.hpp"
#include <SysUtils.hpp>

enum {
    tableItemModuleName,
    tableItemCheckbox
};  

enum {
    maxLayoutNamesLength=13
};

typedef const char_t layoutNames_t[maxLayoutNamesLength];


enum {
#ifdef SHIPPING
    layoutNamesCount=2
#else
    layoutNamesCount=3
#endif
};

static const layoutNames_t layoutNames[layoutNamesCount]={
    "List",
    "Table"
#ifndef SHIPPING
    ,"Icons & Text"
#endif
};

static void ModuleNameDrawFunction(void* t, Int16 row, Int16 column, RectangleType* bounds)
{
    TableType* table = static_cast<TableType*>(t);
    const char* text = static_cast<const char*>(TblGetItemPtr(table, row, column));
    FontID oldFont = FntSetFont(stdFont);
    WinDrawTruncChars(text, StrLen(text), bounds->topLeft.x, bounds->topLeft.y, bounds->extent.x);
    FntSetFont(oldFont);
}

PreferencesForm::PreferencesForm(MoriartyApplication& app):
    MoriartyForm(app, preferencesForm),
    okButton_(*this),
    cancelButton_(*this),
    scrollBar_(*this),
    modulesTable_(*this, &scrollBar_),
    displayPage_(pageModules),
    modulesButton_(*this),
    displayButton_(*this),
    layoutPopupTrigger_(*this),
    layoutLabel_(*this),
    layoutPopupIndex_(0)
{}

PreferencesForm::~PreferencesForm() {}

void PreferencesForm::attachControls()
{   
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    modulesButton_.attach(modulesButton);
    scrollBar_.attach(tableScrollBar);
    modulesTable_.attach(modulesTable);
    displayButton_.attach(displayButton);
    layoutPopupTrigger_.attach(layoutPopupTrigger);
    layoutLabel_.attach(layoutLabel);
}

bool PreferencesForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    
    ArsRectangle rect;
    modulesTable_.bounds(rect);
    modulesTable_.setColumnWidth(tableItemModuleName, rect.width()-16);
    modulesTable_.setColumnSpacing(tableItemModuleName, 2);
    modulesTable_.setColumnWidth(tableItemCheckbox, 12);
    modulesTable_.setColumnSpacing(tableItemCheckbox, 2);

    MoriartyModule* modules = application().modules();
    UInt16 rowsCount = modulesTable_.rowsCount();
    FontID oldFont = FntSetFont(stdFont);
    UInt16 lineHeight = FntLineHeight();
    FntSetFont(oldFont);
    assert(MORIARTY_MODULES_COUNT < rowsCount);    
    for (uint_t i = 0; i<MORIARTY_MODULES_COUNT; ++i)
    {
        MoriartyModule& module = modules[i];
        modulesTable_.setItemStyle(i, tableItemModuleName, customTableItem);
        char* text = const_cast<char*>(module.displayName);
        modulesTable_.setItemPtr(i, tableItemModuleName, text);
        modulesTable_.setItemStyle(i, tableItemCheckbox, checkboxTableItem);
        modulesTable_.setItemInt(i, tableItemCheckbox, !module.disabledByUser);
        modulesTable_.setRowHeight(i, lineHeight);
    }
    for (uint_t i = MORIARTY_MODULES_COUNT; i<rowsCount; ++i)
        modulesTable_.setRowHeight(i, lineHeight);

    modulesTable_.setColumnUsable(tableItemModuleName, true);
    modulesTable_.setColumnUsable(tableItemCheckbox, true);
    modulesTable_.setCustomDrawFunction(tableItemModuleName, ModuleNameDrawFunction);
    modulesTable_.setItemsCount(MORIARTY_MODULES_COUNT);
    modulesTable_.setTopItem(0, true);

    Preferences* prefs = &application().preferences();
    layoutPopupIndex_ = prefs->mainFormView;
    assert(layoutPopupIndex_ >= 0 && layoutPopupIndex_ < layoutNamesCount);
    layoutPopupTrigger_.setLabel(layoutNames[layoutPopupIndex_]);
    setDisplayPage(displayPage_);
    
    return result;
}

void PreferencesForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(2, 2, screenBounds.width()-4, screenBounds.height()-4);
    setBounds(bounds);

    modulesTable_.anchor(screenBounds, anchorRightEdge, 16, anchorBottomEdge, 50);    
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 13, anchorBottomEdge, 50);
    modulesTable_.adjustVisibleItems();
    
    okButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    cancelButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();    
}

void PreferencesForm::setDisplayPage(DisplayPage page)
{
    displayButton_.setValue(false);
    modulesButton_.setValue(false);
    scrollBar_.hide();
    modulesTable_.hide();
    layoutPopupTrigger_.hide();
    layoutLabel_.hide();
    
    switch (page)
    {
        case pageModules:
            modulesButton_.setValue(true);
            scrollBar_.show();
            modulesTable_.show();
            modulesTable_.adjustVisibleItems();
            break;

        case pageDisplay:
            displayButton_.setValue(true);
            layoutPopupTrigger_.show();
            layoutLabel_.show();
            break;

        default:
            assert(false);
    }
    displayPage_ = page;
}

bool PreferencesForm::handleEvent(EventType& event)
{
    if (pageModules == displayPage_ && modulesTable_.handleEventInForm(event))
        return true;
        
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelected(event);
            break;


        case popSelectEvent:
            if (layoutPopupList == event.data.popSelect.listID)
            {
                layoutPopupIndex_ = event.data.popSelect.selection;
                if (layoutPopupIndex_ >= 0 && layoutPopupIndex_ < layoutNamesCount)
                    layoutPopupTrigger_.setLabel(layoutNames[layoutPopupIndex_]);
            }    
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool PreferencesForm::handleControlSelected(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case modulesButton:
            if (pageModules == displayPage_)
                break;
            setDisplayPage(pageModules);
            update();
            break;
            
        case displayButton:
            if (pageDisplay == displayPage_)
                break;
            setDisplayPage(pageDisplay);
            update();
            break;

        case okButton:
            handleOkButton();
            break;

        case cancelButton:
            closePopup();
            break;

        case layoutPopupTrigger:
            return false;
    
        default:
            assert(false);
    }
    return true;
}

void PreferencesForm::handleOkButton()
{
    bool changed = false;
    MoriartyModule* modules = application().modules();
    for (uint_t i = 0; i<MORIARTY_MODULES_COUNT; ++i)
    {
        bool moduleDisabled = !bool(modulesTable_.itemInt(i, tableItemCheckbox));
        changed = changed || (moduleDisabled != modules[i].disabledByUser);
        modules[i].disabledByUser = moduleDisabled;
    }

    Preferences* prefs = &application().preferences();
    if (prefs->mainFormView != layoutPopupIndex_)
    {
        prefs->mainFormView = layoutPopupIndex_;
        changed = true;    
    }
    closePopup();
    if (changed)
        sendEvent(MoriartyApplication::appActiveModulesCountChangedEvent);    
}


