const showAlert = (text) => {
  /**
   * Send an alert message in Sheet.
   */
  SpreadsheetApp.getUi().alert(text);
}

const showYesNoAlert = (text) => {
  /**
   * Ask a YES/NO question with an alert message in Sheet and get the response.
   */
  const ui = SpreadsheetApp.getUi();
  let result = ui.alert(text, ui.ButtonSet.YES_NO);
  SpreadsheetApp.getActive().toast(`Answer: ${result}`);
  if(result === ui.Button.YES) return true;
  return false;
}

class CancelButton extends BaseError { }
const showPrompt = (mainText, inputLabel) => {
  const ui = SpreadsheetApp.getUi();

  const result = ui.prompt(
      mainText,
      inputLabel,
      ui.ButtonSet.OK_CANCEL);

  const selectedButton = result.getSelectedButton();
  const response = result.getResponseText();
  if (selectedButton == ui.Button.OK) {
    return response
  } else {
    throw new CancelButton();
  }
}

let customMenu = null;
const createCustomMenu = () => {
  const ui = SpreadsheetApp.getUi();
  customMenu = ui.createMenu('Custom Menu');
}

const openUrlInNewBrowserTab = (url, message) => {
  /**
   * Open a URL in a new tab.
   * https://gist.github.com/smhmic/e7f9a8188f59bb1d9f992395c866a047
   */
  const html = HtmlService.createHtmlOutput('<!DOCTYPE html><html><script>'
  +'window.close = function(){window.setTimeout(function(){google.script.host.close()},9)};'
  +'var a = document.createElement("a"); a.href="'+url+'"; a.target="_blank";'
  +'if(document.createEvent){'
  +'  var event=document.createEvent("MouseEvents");'
  +'  if(navigator.userAgent.toLowerCase().indexOf("firefox")>-1){window.document.body.append(a)}'
  +'  event.initEvent("click",true,true); a.dispatchEvent(event);'
  +'}else{ a.click() }'
  +'close();'
  +'</script>'
  // Offer URL as clickable link in case above code fails.
  +'<body style="word-break:break-word;font-family:sans-serif;">Failed to open automatically.  Click below:<br/><a href="'+url+'" target="_blank" onclick="window.close()">Click here to proceed</a>.</body>'
  +'<script>google.script.host.setHeight(55);google.script.host.setWidth(410)</script>'
  +'</html>')
  .setWidth(90).setHeight(1);

  if (!message) {
    message = "Opening " + url + "...";
  }
  SpreadsheetApp.getUi().showModalDialog(html, message);
}
