#include <Text.hpp>
#include <SysUtils.hpp>

#include <Definition.hpp>
#include <TextElement.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>
#include <BulletElement.hpp>
#include <ByteFormatParser.hpp>

#include "LookupManager.hpp"
#include "MoriartyPreferences.hpp"
#include "SimpleTextDoneForm.hpp"
#include "HyperlinkHandler.hpp"

#include "MoriartyStyles.hpp"

#pragma pcrelconstdata on

static void unregisteredActionCallback(void* data)
{
    SimpleTextDoneForm* form = static_cast<SimpleTextDoneForm*>(data);
    form->setDisplayMode(SimpleTextDoneForm::showAboutHowToRegister);
    form->update();
}

static void arsLexisHyperlinkActionCallback(void* data)
{
    if (errNone != WebBrowserCommand(false, 0, sysAppLaunchCmdGoToURL, "http://www.arslexis.com/pda/palm.html", NULL))
        FrmAlert(noWebBrowserAlert);    
}

static void palmGearHyperlinkActionCallback(void* data)
{
    if (errNone != WebBrowserCommand(false, 0, sysAppLaunchCmdGoToURL, "http://www.palmgear.com", NULL))
        FrmAlert(noWebBrowserAlert);    
}

static void checkUpdatesActionCallback(void* data)
{
    if (errNone != WebBrowserCommand(false, 0, sysAppLaunchCmdGoToURL, updateCheckURL, NULL))
        FrmAlert(noWebBrowserAlert);    
}

static void aboutActionCallback(void* data)
{
    SimpleTextDoneForm* form = static_cast<SimpleTextDoneForm*>(data);
    form->setDisplayMode(SimpleTextDoneForm::showAboutMain);
    form->update();
}

static void registerActionCallback(void* data)
{
    Application::popupForm(registrationForm);
}

SimpleTextDoneForm::SimpleTextDoneForm(MoriartyApplication& app, DisplayMode dm, int index, int level):
    MoriartyForm(app, simpleTextDoneForm),
    scrollBar_(*this),
    doneButton_(*this),
    textRenderer_(*this, &scrollBar_),
    displayMode_(dm),
    index_(index),
    level_(level),
    titleString_(NULL)    
{
    setFocusControlId(doneButton);
}

SimpleTextDoneForm::SimpleTextDoneForm(MoriartyApplication& app, const char_t* title, const char_t* definition):
    MoriartyForm(app, simpleTextDoneForm),
    scrollBar_(*this),
    doneButton_(*this),
    textRenderer_(*this, &scrollBar_),
    displayMode_(showSerializedDefinition),
    index_(0),
    level_(0)
{
    setFocusControlId(doneButton);
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    setupPopupMenu(testWikiPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);

    Definition::Elements_t elems;
    ByteFormatParser parser;
    parser.parseAll(definition,(UInt32)(-1));
    DefinitionModel* model = parser.releaseModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    textRenderer_.setModel(model, Definition::ownModel);            
    titleString_ = DynStrFromCharP(title, 64);
}

SimpleTextDoneForm::~SimpleTextDoneForm() 
{
    if (NULL != titleString_)
        DynStrDelete(titleString_);
}

void SimpleTextDoneForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneButton_.attach(doneButton);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);

}

bool SimpleTextDoneForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    setDisplayMode(displayMode_);
    return result;
}
    
void SimpleTextDoneForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(2, 2, screenBounds.width()-4, screenBounds.height()-4);
    setBounds(bounds);
    textRenderer_.anchor(screenBounds, anchorRightEdge, 12, anchorBottomEdge, 38);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 11, anchorBottomEdge, 38);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();
}

bool SimpleTextDoneForm::handleEvent(EventType& event)
{
    if (showNothing!=displayMode_ && textRenderer_.handleEventInForm(event))
        return true;
    bool handled = false;
    switch (event.eType) 
    {
        case MoriartyApplication::appRegistrationFinished:
            prepareAboutMain();
            update();
            break;
            
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
 
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void SimpleTextDoneForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            closePopup();
            break;
            
        default:
            assert(false);
    }
}

void SimpleTextDoneForm::prepareAboutMain()
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(NULL);

    String empty;

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement* text;

    elems.push_back(new LineBreakElement(1, 10));

    elems.push_back(text =new TextElement("ArsLexis InfoMan"));
    text->setJustification(DefinitionElement::justifyCenter);
    text->setStyle(StyleGetStaticStyle(styleNameBold));

    elems.push_back(new LineBreakElement(1,3));

    const char* version="Ver " appVersion
#ifndef SHIPPING
#ifdef DEBUG
    " (internal debug)"
#else
    " (internal)"
#endif
#endif
    ;
    elems.push_back(text=new TextElement(version));
    text->setJustification(DefinitionElement::justifyCenter);
    elems.push_back(new LineBreakElement(1,4));

    MoriartyApplication& app=application();
    if (app.preferences().regCode.empty())
    {
        elems.push_back(text=new TextElement("Unregistered ("));
        text->setJustification(DefinitionElement::justifyCenter);
        elems.push_back(text=new TextElement("how to register"));
        text->setJustification(DefinitionElement::justifyCenter);
        text->setHyperlink(empty, hyperlinkCallback);
        text->setActionCallback(unregisteredActionCallback, this);
        elems.push_back(text=new TextElement(")"));
        text->setJustification(DefinitionElement::justifyCenter);
        elems.push_back(new LineBreakElement(1,2));
    }
    else
    {
        elems.push_back(text=new TextElement("Registered"));
        text->setJustification(DefinitionElement::justifyCenter);
        elems.push_back(new LineBreakElement(1,2));
    }

    elems.push_back(text=new TextElement("Copyright \251 "));
    text->setJustification(DefinitionElement::justifyCenter);

    elems.push_back(text=new TextElement("ArsLexis"));
    text->setJustification(DefinitionElement::justifyCenter);
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(arsLexisHyperlinkActionCallback, this);

    elems.push_back(new LineBreakElement(2,3));

    bool fNewVersionAvailable = false;

    if ( !app.preferences().latestClientVersion.empty() )
    {
        // we better make sure to keep appVersion up-to-date
        const char_t *latestVersion = app.preferences().latestClientVersion.c_str();
        if (versionNumberCmp(latestVersion, appVersion) > 0)
        {
            fNewVersionAvailable = true;
        }
    }

    String linkText("Check for updates");
    if (fNewVersionAvailable)
    {
        linkText.assign("New version ");
        linkText.append(app.preferences().latestClientVersion);
        linkText.append(" available!");
    }

    elems.push_back(text=new TextElement(linkText));

    text->setJustification(DefinitionElement::justifyCenter);
    // url doesn't really matter, it's only to establish a hotspot
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(checkUpdatesActionCallback, this);

    elems.push_back(new LineBreakElement(1,3));

    if (app.preferences().regCode.empty())
    {
        elems.push_back(text=new TextElement("Enter registration code"));
        text->setJustification(DefinitionElement::justifyCenter);
        // url doesn't really matter, it's only to establish a hotspot
        text->setHyperlink(empty, hyperlinkCallback);
        text->setActionCallback(registerActionCallback, this);
    }

#ifndef SHIPPING
    String serverTxt = _T("Server: ");
    serverTxt.append(app.preferences().serverAddress);
    elems.push_back(new LineBreakElement(3,2));
    elems.push_back(text = new TextElement(serverTxt));
    text->setJustification(DefinitionElement::justifyCenter);
#endif
    textRenderer_.setModel(model, Definition::ownModel);            
}

void SimpleTextDoneForm::prepareAboutHowToRegister()
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(NULL);

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement* text;

    String empty;
    
    FontEffects fxBold;
    fxBold.setWeight(FontEffects::weightBold);

    elems.push_back(text=new TextElement("Home."));
    text->setJustification(DefinitionElement::justifyLeft);
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(aboutActionCallback, this);
    elems.push_back(new LineBreakElement(4,3));

    elems.push_back(text=new TextElement("Unregistered version of InfoMan limits access to some modules (modules marked as 'free' can be used without limitation)."));
    //elems.push_back(new LineBreakElement());

    elems.push_back(text=new TextElement(" To register InfoMan, please purchase registration code at "));

    //! @todo insert proper codes below

// those 3 #defines should be mutually exclusive
#ifdef PALMGEAR
    elems.push_back(text=new TextElement("palmgear.com"));
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(palmGearHyperlinkActionCallback, this);
#endif

#ifdef HANDANGO
    elems.push_back(text=new TextElement("handango.com/purchase, product id: "));
#endif

#ifdef ARSLEXIS_VERSION
    elems.push_back(text=new TextElement("our website "));
    elems.push_back(text=new TextElement("http://www.arslexis.com."));
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(arsLexisHyperlinkActionCallback, this);
    
#endif
    elems.push_back(new LineBreakElement());

    elems.push_back(text=new TextElement(" and "));

    elems.push_back(text=new TextElement("enter registration code"));
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(registerActionCallback, this);
    elems.push_back(text=new TextElement(" (or use menu item 'Options/Register'). "));

    elems.push_back(new LineBreakElement(4,3));
    elems.push_back(text=new TextElement("Home."));
    text->setJustification(DefinitionElement::justifyLeft);
    text->setHyperlink(empty, hyperlinkCallback);
    text->setActionCallback(aboutActionCallback, this);

    textRenderer_.setModel(model, Definition::ownModel);            
}

enum {
    gasListItemPriceIndex,
    gasListItemNameIndex,
    gasListItemAddressIndex,
    gasListItemAreaIndex,
    gasListItemTimeIndex,
    gasListElementsCount
};

#define priceText _T("Price:")
#define timeText _T("Last update:")
#define addressText _T("Address:")
#define areaText _T("Area:")

void SimpleTextDoneForm::prepareGasPricesDetails()
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );
    textRenderer_.setHyperlinkHandler(NULL);
    LookupManager* lookupManager = application().lookupManager;
    assert(NULL!=lookupManager);

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement* text;
    
    UniversalDataFormat& item = lookupManager->gasPrices;

    elems.push_back(text=new TextElement(item.getItemText(index_,gasListItemNameIndex)));
    text->setStyle(StyleGetStaticStyle(styleNamePageTitle));
    text->setJustification(DefinitionElement::justifyCenter);

    elems.push_back(new LineBreakElement());    
    elems.push_back(text=new TextElement(priceText));
    text->setStyle(StyleGetStaticStyle(styleNameBold));
    String price = _T("$");
    price += item.getItemText(index_,gasListItemPriceIndex);
    localizeNumber(price);
    elems.push_back(text=new TextElement(price));
    text->setJustification(DefinitionElement::justifyRightLastElementInLine);

    elems.push_back(new LineBreakElement());    
    elems.push_back(text=new TextElement(addressText));
    text->setStyle(StyleGetStaticStyle(styleNameBold));
    elems.push_back(new LineBreakElement());    
    elems.push_back(text=new TextElement(item.getItemText(index_,gasListItemAddressIndex)));

    elems.push_back(new LineBreakElement());    
    elems.push_back(text=new TextElement(areaText));
    text->setStyle(StyleGetStaticStyle(styleNameBold));
    elems.push_back(text=new TextElement(item.getItemText(index_,gasListItemAreaIndex)));
    text->setJustification(DefinitionElement::justifyRightLastElementInLine);

    elems.push_back(new LineBreakElement());    
    elems.push_back(text=new TextElement(timeText));
    text->setStyle(StyleGetStaticStyle(styleNameBold));
    elems.push_back(text=new TextElement(item.getItemText(index_,gasListItemTimeIndex)));
    text->setJustification(DefinitionElement::justifyRightLastElementInLine);

    textRenderer_.setModel(model, Definition::ownModel);            
}

void SimpleTextDoneForm::setDisplayMode(DisplayMode dm)
{
    switch (displayMode_=dm)
    {
        case showNothing:
            textRenderer_.hide();
            scrollBar_.hide();
            break;  

        case showGasPricesDetails:
            prepareGasPricesDetails();
            setTitle(_T("Gas Prices"));
            textRenderer_.show();
            scrollBar_.show();
            update();
            break;

        case showAboutMain:
            prepareAboutMain();
            setTitle(_T("About InfoMan"));
            textRenderer_.show();
            scrollBar_.show();
            update();
            break;

        case showAboutHowToRegister:
            prepareAboutHowToRegister();
            setTitle(_T("About InfoMan"));
            textRenderer_.show();
            scrollBar_.show();
            update();
            break;

        case showSerializedDefinition:
            setTitle(DynStrGetCStr(titleString_));
            update();
            break;
            
        default:
            assert(false);
    }
}

bool SimpleTextDoneForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    switch (event.data.keyDown.chr)
    {
        case chrLineFeed:
        case chrCarriageReturn:
            doneButton_.hit();
            handled = true;
    }
    return handled;
}
