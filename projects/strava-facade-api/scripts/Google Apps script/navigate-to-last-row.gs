const navigateToLastRow = () => {
  /**
   * Navigate to the last filled row in the Sheet.
   * It is triggered by an item in the "Custom Menu".
   */
  let ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getActiveSheet();
  sheet.setActiveRange(sheet.getRange(1, 1));
  sheet.setActiveRange(sheet.getRange(sheet.getLastRow(),1));
}


const addGoToLastRowMenuItem = () => {
  customMenu.addItem('Go to last row', 'navigateToLastRow').addToUi();
}
