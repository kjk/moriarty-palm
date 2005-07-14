#include <vector>
#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <Graphics.hpp>

#include <StringListForm.hpp>
#include <TextElement.hpp>
#include <IconElement.hpp>
#include <ParagraphElement.hpp>
#include <BulletElement.hpp>

#include "HyperlinkHandler.hpp"
#include "MoriartyPreferences.hpp"
#include "MainForm.hpp"

#include "MoriartyStyles.hpp"

#define TABLE_LINE_HEIGHT       14

static void checkForUpdates()
{
    if (errNone != WebBrowserCommand(false, 0, sysAppLaunchCmdGoToURL, updateCheckURL, NULL))
        FrmAlert(noWebBrowserAlert);
}

static void checkUpdatesActionCallback(void* data)
{
    checkForUpdates();
}

class ModulesListDrawHandler: public ExtendedList::CustomDrawHandler
{
    uint_t              modulesCount_;
    MoriartyModule*  modules_;
    typedef std::vector<uint_t> ModuleIndexes_t;
    ModuleIndexes_t activeModuleIndexes_;

public:

    void updateActiveModules();

    ModulesListDrawHandler(uint_t modulesCount, MoriartyModule* modules, bool large):
        modulesCount_(modulesCount),
        modules_(modules)
    {
        updateActiveModules();
    }

    ~ModulesListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    uint_t itemsCount() const;

};

void ModulesListDrawHandler::updateActiveModules()
{
    activeModuleIndexes_.resize(activeModulesCount(modulesCount_, modules_));
    uint_t index = 0;
    for (uint_t i = 0; i<modulesCount_; i++)
    {
        if (modules_[i].active())
            activeModuleIndexes_[index++]=i;
    }
}

ModulesListDrawHandler::~ModulesListDrawHandler() {}

uint_t ModulesListDrawHandler::itemsCount() const
{
    if (MoriartyApplication::instance().isNewVersionAvailable())
        return activeModuleIndexes_.size()+1;
    else
        return activeModuleIndexes_.size();
}

void ModulesListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    uint_t width;
    uint_t length;
    
    if (MoriartyApplication::instance().isNewVersionAvailable())
    {
        if (item == 0)
        {
            String txt(_T("  Upgrade to version "));
            txt += MoriartyApplication::instance().preferences().latestClientVersion;
            Graphics::FontSetter setFont(graphics, boldFont);
            width = itemBounds.width();
            length = txt.length();
            graphics.charsInWidth(txt.c_str(), length, width);
            RGBColorType newColor;
            RGBColorType oldColor;
            setRgbColor(newColor, 200, 0, 0);
            WinSetTextColorRGB(&newColor, &oldColor);
            graphics.drawText(txt.c_str(), length, itemBounds.topLeft);
            WinSetTextColorRGB(&oldColor, NULL);
            return;
        }
        else
        {
            item--;
        }   
    }


    if (item>=activeModuleIndexes_.size())
        return;

    width = itemBounds.width();
    const MoriartyModule* module = &modules_[activeModuleIndexes_[item]];

    uint_t iconId = module->smallIconId;
    if (frmInvalidObjectId!=module->largeIconId)
        iconId = module->largeIconId;

    uint_t margin = 2;

    if (frmInvalidObjectId != iconId)
    {
        MemHandle handle = DmGet1Resource(bitmapRsc, iconId);
        if (handle)
        {
            BitmapType* bmp = static_cast<BitmapType*>(MemHandleLock(handle));
            if (bmp)
            {
                Coord bmpW, bmpH;
                UInt16 rowSize;
                BmpGetDimensions(bmp, &bmpW, &bmpH, &rowSize);
                int y = itemBounds.y()+(itemBounds.height()-bmpH)/2;
                WinDrawBitmap(bmp, itemBounds.x()+margin, y);
                width -= (margin += bmpW + 4);
                MemHandleUnlock(handle);
            }
            DmReleaseResource(handle);
        }
    }
    const char_t* displayName = module->displayName;
    length = tstrlen(displayName);

    Graphics::FontSetter setFont(graphics, stdFont);
    graphics.charsInWidth(displayName, length, width);
    Point p = itemBounds.topLeft;
    p.x += margin;
    p.y = itemBounds.y() + (itemBounds.height()-graphics.fontHeight())/2;
    graphics.drawText(displayName, length, p);
    uint_t mainFontHeight = graphics.fontHeight();
    MoriartyApplication& app = MoriartyApplication::instance();
    // draw " (free)"
    if (module->free)
    {
        if (tstrlen(displayName) == length)
        {
            const char_t* text = _T(" (free)");
            p.x += width;
            width = itemBounds.width()-p.x;
            length = tstrlen(text);
            graphics.charsInWidth(text, length, width);
            graphics.drawText(text, length, p);
        }
    }

    /*
    // show if new version is available, show "(var x.y avaialble!)"
    // in bold red, right-aligned if server says that a new version x.y
    // is available
    if ((moduleIdAbout == module->id) && (!app.preferences().latestClientVersion.empty()))
    {
        // we better make sure to keep myVersion up-to-date
        const char_t *myVersion = appVersion;
        const char_t *latestVersion = app.preferences().latestClientVersion.c_str();
        // the logic is simple: if latestVersion != my version then it must
        // be newer
        if (versionNumberCmp(latestVersion, myVersion) > 0)
        {
            String txt(_T("(ver "));
            txt += app.preferences().latestClientVersion;
            txt += " available!)";

            Graphics::FontSetter setFont(graphics, boldFont);

            uint_t displayNameDx = graphics.textWidth(displayName, length) + 4;
            width = itemBounds.width();
            width -= displayNameDx;
            length = txt.length();
            graphics.charsInWidth(txt.c_str(), length, width);

            p.x = itemBounds.topLeft.x;
            p.x += (itemBounds.width() - width - 2);

            RGBColorType newColor;
            RGBColorType oldColor;
            setRgbColor(newColor, 200, 0, 0);
            WinSetTextColorRGB(&newColor, &oldColor);

            graphics.drawText(txt.c_str(), length, p);

            WinSetTextColorRGB(&oldColor, NULL);
        }
    }
    */
#define GREY_COLOR 127, 127, 127

    if (module->tracksUpdateTime)
    {
        String updated;
        RGBColorType color;
        setRgbColor(color, GREY_COLOR);
        if (moduleNeverUpdated != module->lastUpdateTime)
        {
            UInt32 interval = TimGetSeconds() - module->lastUpdateTime;
            char_t buffer[16] = {0};
            uint_t len = fuzzyTimeInterval(interval, buffer);
            updated.assign(buffer, len);
            updated += _T(" ago");
         }
        Graphics::FontSetter setFont(graphics, smallFont);

        uint_t displayNameDx = graphics.textWidth(displayName, length) + 4;
        width = itemBounds.width();
        width -= displayNameDx;
        length = updated.length();
        graphics.charsInWidth(updated.c_str(), length, width);
        p.y += (mainFontHeight - graphics.fontHeight());

        p.x = itemBounds.topLeft.x;
        p.x += (itemBounds.width() - width - 2);

        RGBColorType oldColor;
        WinSetTextColorRGB(&color, &oldColor);

        graphics.drawText(updated.c_str(), length, p);

        WinSetTextColorRGB(&oldColor, NULL);
    }
}

// table draw function
static void ModuleNameDrawFunction(void* t, Int16 row, Int16 column, RectangleType* bounds)
{
    Boolean fSelected;
    Int16 selectedRow, selectedColumn;
    TableType* table = static_cast<TableType*>(t);
    if (NULL == TblGetItemPtr(table, row, column))
    {
        if (0 == row && 0 == column && MoriartyApplication::instance().isNewVersionAvailable())
        {
            Graphics graphics;
            String txt(_T(" Up to v "));
            txt += MoriartyApplication::instance().preferences().latestClientVersion;
            Graphics::FontSetter setFont(graphics, boldFont);
            uint_t width = bounds->extent.x;
            uint_t length = txt.length();
            graphics.charsInWidth(txt.c_str(), length, width);
            RGBColorType newColor;
            RGBColorType oldColor;
            setRgbColor(newColor, 200, 0, 0);
            WinSetTextColorRGB(&newColor, &oldColor);
            graphics.drawText(txt.c_str(), length, bounds->topLeft);
            WinSetTextColorRGB(&oldColor, NULL);
    
        }
        return;
    }
    ModuleID* id = static_cast<ModuleID*>(TblGetItemPtr(table, row, column));
    TblGetSelection(table, &selectedRow, &selectedColumn);
    fSelected = false;
    if ((row == selectedRow) && (column == selectedColumn))
        fSelected = true;

    MoriartyModule* module = MoriartyApplication::instance().getModuleById(*id);

    ArsRectangle itemBounds = *bounds;
    Graphics graphics;
    
    Color highlighted = UIColorGetTableEntryIndex(UIObjectSelectedFill);
    Color normal = UIColorGetTableEntryIndex(UIObjectFill);
    
//    Color color = graphics.setBackgroundColor(fSelected ? highlighted : normal);

//    graphics.erase(itemBounds);    
        
    uint_t width = itemBounds.width();
    uint_t iconId = module->smallIconId;
    if (frmInvalidObjectId!=module->largeIconId)
        iconId = module->largeIconId;

    uint_t margin = 1;

    if (frmInvalidObjectId != iconId)
    {
        MemHandle handle = DmGet1Resource(bitmapRsc, iconId);
        if (handle)
        {
            BitmapType* bmp = static_cast<BitmapType*>(MemHandleLock(handle));
            if (bmp)
            {
                Coord bmpW, bmpH;
                UInt16 rowSize;
                BmpGetDimensions(bmp, &bmpW, &bmpH, &rowSize);
                int y = itemBounds.y();
                WinDrawBitmap(bmp, itemBounds.x()+margin, y);
                width -= (margin += bmpW + 4);
                MemHandleUnlock(handle);
            }
            DmReleaseResource(handle);
        }
    }

    const char_t* displayName = module->displayName;
    uint_t length = tstrlen(displayName);

    Graphics::FontSetter setFont(graphics, stdFont);
    graphics.charsInWidth(displayName, length, width);
    Point p = itemBounds.topLeft;
    p.x += margin;
    p.y = itemBounds.y();
    graphics.drawText(displayName, length, p);
    
//    graphics.setBackgroundColor(color);
}

enum {
    mainFormViewList = 0,
    mainFormViewTable = 1,
    mainFormViewRenderer = 2
};

MainForm::MainForm(MoriartyApplication& app):
    MoriartyForm(app, mainForm),
    smallModulesList_(*this),
    displayMode_(showSmallModulesList),
    ignoreEvents_(false),
    scrollBar_(*this),
    tableScrollBar_(*this),
    textRenderer_(*this, &scrollBar_),
    smallModulesTable_(*this, &tableScrollBar_),
    lastKeyPressedTime_(0),
    repeatCount_(0),
    smallListDrawHandler_(new ModulesListDrawHandler(MORIARTY_MODULES_COUNT, app.modules(), false))
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
    );
    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
}

MainForm::~MainForm()
{}

void MainForm::attachControls()
{
    MoriartyForm::attachControls();
    smallModulesList_.attach(smallModulesList);
    smallModulesList_.setUpBitmapId(upBitmap);
    smallModulesList_.setDownBitmapId(downBitmap);
    smallModulesList_.setItemHeight(14);

    tableScrollBar_.attach(tableScrollBar);
    smallModulesTable_.attach(smallModulesTable);
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(textRenderer);
}

bool MainForm::handleOpen()
{
    bool handled = MoriartyForm::handleOpen();

    smallModulesList_.setCustomDrawHandler(smallListDrawHandler_.get());

    uint_t itemToSelect = 0;
    if (0 != smallModulesList_.itemsCount())
    {
        if (MoriartyApplication::moduleNone!=application().selectedActiveModuleIndex())
            itemToSelect = application().selectedActiveModuleIndex();
    }
    if (application().isNewVersionAvailable())
        itemToSelect++;
    smallModulesList_.setSelection(itemToSelect, ExtendedList::redrawNot);

    setDisplayModeFromPreferences();
    updateTitle();

#ifndef SHIPPING
    if (!application().preferences().fServerSelected)
    {
        sendEvent(MoriartyApplication::appChangeServer);
    }
#endif

    return handled;
}

void MainForm::setDisplayModeFromPreferences()
{
    switch (application().preferences().mainFormView)
    {
        case mainFormViewList:
            setDisplayMode(showSmallModulesList);
            break;
        case mainFormViewTable:
            setDisplayMode(showSmallModulesTable);
            break;
        case mainFormViewRenderer:
            setDisplayMode(showTextRenderer);
            break;
        default:
            assert(false);
            break;
    }
}

void MainForm::prepareRenderer()
{
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement*        text;
    IconElement*        img;
    ParagraphElement*   paragraph;
    BulletElement*      bull;
    LineBreakElement*   lbr;

    MoriartyModule* modules = application().modules();
    
    if (application().isNewVersionAvailable())
    {
        String linkText;
        linkText.assign("Upgrade to version ");
        linkText.append(application().preferences().latestClientVersion);

        elems.push_back(text=new TextElement(linkText));
        text->setJustification(DefinitionElement::justifyCenter);
        text->setStyle(StyleGetStaticStyle(styleNameBoldRed));
        // url doesn't really matter, it's only to establish a hotspot
        String empty;
        text->setHyperlink(empty, hyperlinkCallback);
        text->setActionCallback(checkUpdatesActionCallback, this);

        elems.push_back(new LineBreakElement(1,3));
    }
    
    int modulesCounted = activeModulesCount(MORIARTY_MODULES_COUNT, modules);
    if (modulesCounted > 0)
    {
        const int maxIconsInLine = 8;
        assert(maxIconsInLine > 0);
        int iconsInLine = maxIconsInLine;
        int lines = 1;
        while (modulesCounted > maxIconsInLine*lines)
            lines++;
        assert(lines > 0);
        iconsInLine = (modulesCounted+lines-1)/lines;

        elems.push_back(paragraph = new ParagraphElement());
        paragraph->setJustification(DefinitionElement::justifyCenter);
        int modulesAdded = 0;
        for (uint_t i = 0; i<MORIARTY_MODULES_COUNT; ++i)
        {
            MoriartyModule& module = modules[i];
            if (module.active())
            {
                elems.push_back(img = new IconElement(module.smallIconId));
                img->setMargin(3);
                img->setParent(paragraph);
                DynStr* dyn = DynStrFromCharP3(urlSchemaRunModule,_T(":"),module.name);
                if (NULL != dyn)
                {
                    img->setHyperlink(DynStrGetCStr(dyn), hyperlinkUrl);
                    DynStrDelete(dyn);
                } // TODO: what to do if NULL == dyn? return? what about model?
                modulesAdded++;
                if (modulesAdded%iconsInLine == 0 && modulesAdded != modulesCounted)
                {
                    elems.push_back(lbr = new LineBreakElement());
                    lbr->setParent(paragraph);
                }
            }
        }

        for (uint_t i = 0; i<MORIARTY_MODULES_COUNT; ++i)
        {
            MoriartyModule& module = modules[i];
            if (module.active())
            {
                elems.push_back(bull = new BulletElement());
                elems.push_back(text = new TextElement(module.name));
                text->setParent(bull);
                DynStr* dyn = DynStrFromCharP3(urlSchemaRunModule,_T(":"),module.name);
                if (NULL != dyn)
                {
                    text->setHyperlink(DynStrGetCStr(dyn), hyperlinkUrl);
                    DynStrDelete(dyn);
                } // TODO: what to do if NULL == dyn? return? what about model?
                if (module.free)
                {
                    elems.push_back(text = new TextElement(_T(" (free)")));
                    // TODO: style? small?
                    text->setParent(bull);
                }

                if (module.tracksUpdateTime)
                {
                    if (moduleNeverUpdated != module.lastUpdateTime)
                    {
                        String updated;
                        UInt32 interval = TimGetSeconds() - module.lastUpdateTime;
                        char_t buffer[16] = {0};
                        uint_t len = fuzzyTimeInterval(interval, buffer);
                        updated.assign(buffer, len);
                        updated += _T(" ago");
                        elems.push_back(text = new TextElement(updated));
                        text->setStyle(StyleGetStaticStyle(styleNameSmallGray));
                        text->setJustification(DefinitionElement::justifyRightLastElementInLine);
                        text->setParent(bull);
                    }
                }
            }
        }
    }
    textRenderer_.setModel(model, Definition::ownModel);
}

void MainForm::prepareTable()
{
    ArsRectangle rect;
    smallModulesTable_.bounds(rect);
    smallModulesTable_.setColumnWidth(0, rect.width()/2);
    smallModulesTable_.setColumnWidth(1, rect.width()/2);
    smallModulesTable_.setColumnSpacing(0, 0);
    smallModulesTable_.setColumnSpacing(1, 0);

    int itemToSelect = -2;
    if (MoriartyApplication::moduleNone!=application().selectedActiveModuleIndex())
        itemToSelect = application().selectedActiveModuleIndex();

    MoriartyModule* modules = application().modules();
    UInt16 rowsCount = smallModulesTable_.rowsCount();
    UInt16 lineHeight = TABLE_LINE_HEIGHT;
    assert(MORIARTY_MODULES_COUNT < rowsCount);
    uint_t x=0, y=0, activeCount = 0;
    uint_t selX = 0, selY = 0;
    if (application().isNewVersionAvailable())
    {
        smallModulesTable_.setItemStyle(x, 1, customTableItem);
        smallModulesTable_.setItemPtr(x, 1, NULL);

        smallModulesTable_.setItemStyle(x, y, customTableItem);
        smallModulesTable_.setItemPtr(x, y, NULL);
        smallModulesTable_.setRowHeight(x, lineHeight);
        y++;
        activeCount++;
    }
    
    for (uint_t i = 0; i<MORIARTY_MODULES_COUNT; ++i)
    {
        MoriartyModule& module = modules[i];
        if (module.active())
        {
            smallModulesTable_.setItemStyle(x, 1, customTableItem);
            smallModulesTable_.setItemPtr(x, 1, NULL);

            smallModulesTable_.setItemStyle(x, y, customTableItem);
            smallModulesTable_.setItemPtr(x, y, &module.id);
            smallModulesTable_.setRowHeight(x, lineHeight);
            
            if (itemToSelect >= 0)
            {
                selX = x;
                selY = y;
                itemToSelect--;
            }
            y++;
            if (2 == y)
            {
                y = 0;
                x++;
            }
            activeCount++;
        }
    }
    for (uint_t i = x; i<rowsCount; ++i)
        smallModulesTable_.setRowHeight(i, lineHeight);

    smallModulesTable_.setColumnUsable(0, true);
    smallModulesTable_.setColumnUsable(1, true);
    smallModulesTable_.setItemsCount((activeCount+1)/2);
    smallModulesTable_.setCustomDrawFunction(0, ModuleNameDrawFunction);
    smallModulesTable_.setCustomDrawFunction(1, ModuleNameDrawFunction);
    smallModulesTable_.setTopItem(0, true);
    if (itemToSelect != -2)
        smallModulesTable_.setSelection(selX, selY);
    else
        smallModulesTable_.setSelection(0, 0);
    smallModulesTable_.redraw();
    smallModulesTable_.updateSelection();
}

void MainForm::updateTitle()
{
    DynStr *title = DynStrNew(32);
    if (NULL == title)
        return;
#ifdef SHIPPING
    DynStrAppendCharP(title, _T("InfoMan"));
    if (application().preferences().regCode.empty())
        DynStrAppendCharP(title, _T(" (unregistered)"));
#else
    if (application().preferences().regCode.empty())
        DynStrAppendCharP(title, _T("nr "));
    DynStrAppendCharP(title, application().preferences().serverAddress);
#endif
    setTitle(DynStrGetCStr(title));
    DynStrDelete(title);
}

void MainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(screenBounds);

    bounds=screenBounds;
    bounds.explode(0, 17, 0, -19);

    smallModulesList_.setBounds(bounds);
    smallModulesList_.adjustVisibleItems();

    smallModulesTable_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 17);
    smallModulesTable_.bounds(bounds);
   
    tableScrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 17);
    smallModulesTable_.adjustVisibleItems();

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 17);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 17);
    update();
}

/**
 *  This function make sth like that:
 *  1) if keys are pressed, we are searching using rules
 *     first "a" goes to first module starting with "A"
 *     than if we pressed "m" in short time, we go to first "Am" module
 *     else (time's up) we go to first "M" module
 *
 *  2) run module if perfect match ("a","b","o","u","t" runs About module)
 *
 *  3) "k" "k" goes to 2nd "K" module. third "k" goes to 3rd "K" module...
 *
 *  TODO: ??
 *  1) if Currency is only module starts with 'c' run it? ('am' runs Amazon, ...)
 *
 */
#define SECONDS_BETWEEN_KEYS 2

bool MainForm::handleKeyPressed(char_t key)
{
    // WORK IN PROGRESS
    // append pressedKeys_, or assign
    bool   wasRepeated = false;
    UInt32 currentTime = TimGetSeconds();
    if (currentTime - lastKeyPressedTime_ <= SECONDS_BETWEEN_KEYS)
    {
        if (1 >= pressedKeys_.length())
        {
            if (pressedKeys_[pressedKeys_.length()-1] == key)
            {
                wasRepeated = true;
            }
            else
                pressedKeys_.append(1,key);
        }
        else
            pressedKeys_.append(1,key);
    }
    else
    {
        pressedKeys_.assign(1,key);
    }
    if (wasRepeated)
        repeatCount_++;
    else
        repeatCount_ = 0;
    // get moduleId by pressedKeys
    MoriartyModule* modules = application().modules();
    int matchedModuleIndex              = -1;
    int firstMatchedModuleIndex         = -1;
    int matchedActiveModuleIndex        =  0;
    int firstMatchedActiveModuleIndex   =  0;
    int repeatDownCount                 = repeatCount_;

    for (int i=0; i<MORIARTY_MODULES_COUNT; i++)
    {
        if (modules[i].active())
        {
            if (startsWithIgnoreCase(modules[i].name, pressedKeys_.c_str()))
            {
                if (equalsIgnoreCase(modules[i].name, pressedKeys_.c_str()))
                {
                    // run module - equal matching
                    application().runModule(matchedActiveModuleIndex);
                    return true;
                }

                if (repeatDownCount > 0)
                {
                    if (-1 == firstMatchedModuleIndex)
                    {
                        // remember first repeated module (if we can't find 2nd,3rd,...,Nth)
                        firstMatchedActiveModuleIndex = matchedActiveModuleIndex;
                        firstMatchedModuleIndex = i;
                    }
                    --repeatDownCount;
                }
                else
                {
                    matchedModuleIndex = i;
                    break;
                }
            }
            matchedActiveModuleIndex++;
        }
    }
    if (-1 == matchedModuleIndex && -1 != firstMatchedModuleIndex)
    {
        assert(wasRepeated);
        matchedModuleIndex = firstMatchedModuleIndex;
        matchedActiveModuleIndex = firstMatchedActiveModuleIndex;
        // we have repeated all modules, so let's get back to start
        repeatCount_ = 0;
    }
    if (-1 == matchedModuleIndex)
    {
        // remove that key - what was that?
        if (!wasRepeated)
            pressedKeys_.erase(pressedKeys_.size()-1);
        return false;
    }

    // increase last key pressed time to current time
    lastKeyPressedTime_ = currentTime;
    // select pointed module...
    switch (displayMode_)
    {
        case showSmallModulesList:
            if (application().isNewVersionAvailable())
                smallModulesList_.setSelection(matchedActiveModuleIndex + 1, ExtendedList::redraw);
            else
                smallModulesList_.setSelection(matchedActiveModuleIndex, ExtendedList::redraw);
            break;

        case showSmallModulesTable:
        {
            Int16 row, col, rowCount, colCount;
            ModuleID selectedModuleId = modules[matchedActiveModuleIndex].id;
            ModuleID rowColModuleId;
            rowCount = smallModulesTable_.rowsCount();
            colCount = smallModulesTable_.columnsCount();
            for (row = 0; row < rowCount; row++)
            {
                for (col = 0; col < colCount; col++)
                {
                    if (NULL != smallModulesTable_.itemPtr(row, col))
                    {
                        rowColModuleId = *((ModuleID*)smallModulesTable_.itemPtr(row, col));
                        if (selectedModuleId == rowColModuleId)
                        {
                            smallModulesTable_.setSelection(row, col);
                            smallModulesTable_.invalidate();
                            return true;
                        }
                    }
                }
            }
            break;
        }

        case showTextRenderer:
        {
            Graphics graphics;
            if (application().isNewVersionAvailable())
                textRenderer_.definition().highlightHyperlink(graphics, matchedActiveModuleIndex + 1);
            else
                textRenderer_.definition().highlightHyperlink(graphics, matchedActiveModuleIndex);
            break;
        }
    }

    return true;
}

bool MainForm::handleEvent(EventType& event)
{
    bool                  handled = false;
    MoriartyApplication&  app = application();
    Preferences&          prefs = application().preferences();
    bool                  fKeyLaunchEnabled = prefs.fKeyboardLaunchEnabled;

    if (ignoreEvents_)
        return false;

    if (showSmallModulesTable == displayMode_ && smallModulesTable_.handleEventInForm(event))
        return true;
    if (showTextRenderer == displayMode_ && textRenderer_.handleEventInForm(event))
        return true;

    switch (event.eType)
    {
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            handled = true;
            break;

        case tblSelectEvent:
        {
            //TODO: move it to function.
            Int16 row, col;
            assert(smallModulesTable_.id() == event.data.tblSelect.tableID);
            row = event.data.tblSelect.row;
            col = event.data.tblSelect.column;
            ModuleID *id = (ModuleID*)smallModulesTable_.itemPtr(row, col);
            if (NULL != id)
                application().runModuleById(*id);
            else if (0 == row && 0 == col)
                checkForUpdates();
            handled = true;
            break;
        }

        case MoriartyApplication::appActiveModulesCountChangedEvent:
            ModulesListDrawHandler* handler = static_cast<ModulesListDrawHandler*>(smallListDrawHandler_.get());
            if (NULL != handler)
            {
                handler->updateActiveModules();
                smallModulesList_.adjustVisibleItems(ExtendedList::redraw);
            }
            setDisplayModeFromPreferences();
            handled = true;
            break;

        case MoriartyApplication::appRegistrationFinished:
            updateTitle();
            update();
            handled = true;
            break;
#ifndef SHIPPING
        case MoriartyApplication::appChangeServer:
            changeServer();
            handled = true;
            break;
#endif
        case keyDownEvent:
            handled = handleKeyPressed(event.data.keyDown.chr);
            if (handled)
                break;
            if (showSmallModulesList == displayMode_)
                handled = currentList().handleKeyDownEvent(event, List::optionFireListSelectOnCenter|List::optionScrollPagesWithLeftRight);
            if (showSmallModulesTable == displayMode_)
                handled = smallModulesTable_.handleKeyDownEvent(event);
            if (handled)
                break;
            // Fall through in case event isn't handled.

        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

void MainForm::handleListItemSelect(uint_t listId, uint_t item)
{
    assert(smallModulesList == listId);
    MoriartyApplication& app = application();
    if (app.isNewVersionAvailable())
    {
        if (item == 0)
        {
            checkForUpdates();
            return;
        }
        else
            item--;
    }
    assert(item<MORIARTY_MODULES_COUNT);
    app.runModule(item);
}

void MainForm::setDisplayMode(DisplayMode mode)
{
    smallModulesList_.hide();
    smallModulesTable_.hide();
    tableScrollBar_.hide();
    scrollBar_.hide();
    textRenderer_.hide();
    switch (mode)
    {
        case showSmallModulesList:
            application().preferences().mainFormView = mainFormViewList;
            smallModulesList_.show();
            smallModulesList_.focus();
            break;

        case showSmallModulesTable:
            application().preferences().mainFormView = mainFormViewTable;
            tableScrollBar_.show();
            smallModulesTable_.show();
            prepareTable();
            smallModulesTable_.focus();
            break;

        case showTextRenderer:
            application().preferences().mainFormView = mainFormViewRenderer;
            prepareRenderer();
            if (MoriartyApplication::moduleNone!=application().selectedActiveModuleIndex())
            {
                Graphics graphics;
                if (application().isNewVersionAvailable())
                    textRenderer_.definition().highlightHyperlink(graphics, application().selectedActiveModuleIndex()+1);
                else
                    textRenderer_.definition().highlightHyperlink(graphics, application().selectedActiveModuleIndex());
            }
            textRenderer_.show();
            textRenderer_.focus();
            break;

        default:
            assert(false);
    }
    displayMode_=mode;
    update();
}

int MainForm::showStringListForm(char_t* strList[], int strListSize)
{
    StringListForm* form = new StringListForm(application(), stringListForm, stringList, selectButton, cancelButton);
    form->initialize();
    form->SetStringList(application().strListSize, application().strList);
    ignoreEvents_ = true; // Strange things happen here and if we don't prevent MainForm from processing events we'll overflow the stack :-(
    int sel = form->showModalAndGetSelection();
    ignoreEvents_ = false;
    update();
    delete form;
    return sel;
}

#ifndef SHIPPING
#define SERVER_COUNT 8

void MainForm::changeServer()
{
    // construct a list of servers
    char_t **serverList = new char_t *[SERVER_COUNT];
    if (NULL == serverList)
        return;

    serverList[0] = StringCopy(SERVER_IM_KJK);
    serverList[1] = StringCopy(SERVER_IM_SZYMON);
    serverList[2] = StringCopy(SERVER_IM_ANDRZEJ);
    serverList[3] = StringCopy(SERVER_LOCALHOST);
    serverList[4] = StringCopy(SERVER_LOCAL);
    serverList[5] = StringCopy(SERVER_ANDRZEJ_BT);
    serverList[6] = StringCopy(SERVER_ANDRZEJ_INTERNET);
    serverList[7] = StringCopy(SERVER_ARSLEXIS);

    FreeStringList(application().strList, application().strListSize);

    application().strList = serverList;
    application().strListSize = SERVER_COUNT;

    int sel = showStringListForm(application().strList, application().strListSize);

    if (NOT_SELECTED==sel)
        return;

    char_t *server = NULL;
    switch (sel)
    {
        case 0:
            server = SERVER_IM_KJK;
            break;
        case 1:
            server = SERVER_IM_SZYMON;
            break;
        case 2:
            server = SERVER_IM_ANDRZEJ;
            break;
        case 3:
            server = SERVER_LOCALHOST;
            break;
        case 4:
            server = SERVER_LOCAL;
            break;
        case 5:
            server = SERVER_ANDRZEJ_BT;
            break;
        case 6:
            server = SERVER_ANDRZEJ_INTERNET;
            break;
        case 7:
            server = SERVER_ARSLEXIS;
            break;
        default:
            assert(0);
            return;
    }

    assert(NULL!=server);
    application().preferences().serverAddress = server;
    application().preferences().fServerSelected = true;
    application().preferences().cookie.clear();

    updateTitle();
}
#endif

bool MainForm::handleMenuCommand(UInt16 itemId)
{
    switch (itemId)
    {
        case preferencesMenuItem:
            Application::popupForm(preferencesForm);
            break;

        case aboutMenuItem:
            application().runModuleById(moduleIdAbout);
            break;

        case registerMenuItem:
            Application::popupForm(registrationForm);
            break;

        case arslexisWebsiteMenuItem:
            if (errNone != WebBrowserCommand(false, 0, sysAppLaunchCmdGoToURL, "http://www.arslexis.com/pda/palm.html",NULL))
            {
                FrmAlert(noWebBrowserAlert);
            }
            break;

#ifndef SHIPPING
        case changeServerMenuItem:
           changeServer();
           break;

        case clearCookieMenuItem:
            application().preferences().cookie.clear();
            break;
/*
        case tableMenuItem:
            setDisplayMode(showSmallModulesTable);
            break;

        case listMenuItem:
            setDisplayMode(showSmallModulesList);
            break;

        case rendererMenuItem:
            setDisplayMode(showTextRenderer);
            break;
*/
#endif

        case checkUpdatesMenuItem:
            checkForUpdates();
            break;

        default:
            assert(false);
    }
    return true;
}

bool MainForm::handleUpdate(UInt16 updateCode)
{
    bool ret = Form::handleUpdate(updateCode);

    smallModulesTable_.updateSelection();
    
    return ret;
}
