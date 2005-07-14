#include "EpicuriousPreferencesForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>

enum {
    tableItemPartName,
    tableItemCheckbox
};  

static void RecipePartNameDrawFunction(void* t, Int16 row, Int16 column, RectangleType* bounds)
{
    TableType* table = static_cast<TableType*>(t);
    const char* text = static_cast<const char*>(TblGetItemPtr(table, row, column));
    FontID oldFont = FntSetFont(stdFont);
    WinDrawTruncChars(text, StrLen(text), bounds->topLeft.x, bounds->topLeft.y, bounds->extent.x);
    FntSetFont(oldFont);
}

EpicuriousPreferencesForm::EpicuriousPreferencesForm(MoriartyApplication& app):
    MoriartyForm(app, epicuriousPreferencesForm),
    okButton_(*this),
    cancelButton_(*this),
    recipePartsTable_(*this)
{}

EpicuriousPreferencesForm::~EpicuriousPreferencesForm() {}

void EpicuriousPreferencesForm::attachControls()
{
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    recipePartsTable_.attach(recipePartsTable);
}

bool EpicuriousPreferencesForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    
    ArsRectangle rect;
    recipePartsTable_.bounds(rect);
    recipePartsTable_.setColumnWidth(tableItemPartName, rect.width()-16);
    recipePartsTable_.setColumnSpacing(tableItemPartName, 2);
    recipePartsTable_.setColumnWidth(tableItemCheckbox, 12);
    recipePartsTable_.setColumnSpacing(tableItemCheckbox, 2);

    UInt16 rowsCount = recipePartsTable_.rowsCount();
    FontID oldFont = FntSetFont(stdFont);
    UInt16 lineHeight = FntLineHeight();
    FntSetFont(oldFont);

    const Preferences::EpicuriousPreferences& prefs = application().preferences().epicuriousPreferences; 

    assert(prefs.recipePartsCount <= rowsCount);    

    for (uint_t i=0; i < prefs.recipePartsCount; i++)
    {
        recipePartsTable_.setItemStyle(i, tableItemPartName, customTableItem);
        switch (i)
        {
            case prefs.recipeName:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Name");
                break;
            case prefs.recipeNote:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Information");
                break;
            case prefs.recipeIngredients:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Ingredients");
                break;
            case prefs.recipePreperation:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Preparation");
                break;
            case prefs.recipeReviews:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Reviews");
                break;
            case prefs.recipeGlobalNote:
                recipePartsTable_.setItemPtr(i, tableItemPartName, (char*)"Global note");
                break;
            default:
                assert(false);
                break;        
        }
        recipePartsTable_.setItemStyle(i, tableItemCheckbox, checkboxTableItem);
        recipePartsTable_.setItemInt(i, tableItemCheckbox, prefs.fDisplayRecipePart[i]);
        recipePartsTable_.setRowHeight(i, lineHeight);
        recipePartsTable_.setRowUsable(i, true);

    }

    for (uint_t i = prefs.recipePartsCount; i<rowsCount; i++)
    {
        recipePartsTable_.setRowHeight(i, lineHeight);
        recipePartsTable_.setRowUsable(i, false);
    }
    
    recipePartsTable_.setColumnUsable(tableItemPartName, true);
    recipePartsTable_.setColumnUsable(tableItemCheckbox, true);
    recipePartsTable_.setCustomDrawFunction(tableItemPartName, RecipePartNameDrawFunction);
    recipePartsTable_.invalidate();
        
    return result;
}

void EpicuriousPreferencesForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(2, 2, screenBounds.width()-4, screenBounds.height()-4);
    setBounds(bounds);

    recipePartsTable_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 51);    
    recipePartsTable_.invalidate();
    okButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    cancelButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();    
}

bool EpicuriousPreferencesForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelected(event);
            handled = true;
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void EpicuriousPreferencesForm::handleControlSelected(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case okButton:
            handleOkButton();
            break;

        case cancelButton:
            closePopup();
            break;

        default:
            assert(false);
    }
}

void EpicuriousPreferencesForm::handleOkButton()
{
    Preferences::EpicuriousPreferences& prefs = application().preferences().epicuriousPreferences; 
    bool changed = false;
    for (uint_t i = 0; i<prefs.recipePartsCount; i++)
    {
        bool display = bool(recipePartsTable_.itemInt(i, tableItemCheckbox));
        if (prefs.fDisplayRecipePart[i] != display)
        {
            changed = true;
            prefs.fDisplayRecipePart[i] = display;
        }    
    }
    closePopup();
    if (changed)
        sendEvent(MoriartyApplication::appRecipePartsChangedEvent);
}


