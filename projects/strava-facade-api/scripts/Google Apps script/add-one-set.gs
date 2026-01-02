class AddOneSetButton {
  click() {
    /**
     * Invoked when clicking on the "+1 set" button.
     * Add one to the selected set counter in Sheet.
     * Used by the +1 drawing button.
     */
    const sheet = SpreadsheetApp.getActiveSheet();

    // Get the position of the +1 button.
    // This works only if the "+1 set" drawing was added before the "Update Strava" drawing.
    // But in 2026 I created a new sheet and added the "+1 set" drawing after.
    // To avoid this issue, I changed the code to perform a for loop on every drawing and
    //  identify the "+1 set" drawing by its onAction.
    // let plusOneButton = sheet.getDrawings()[1];
    let plusOneButton;
    for (let btn of sheet.getDrawings()) {
      if (btn.getOnAction() == "addOneSetClickHandler")
        plusOneButton = btn;
    };
    const buttonRow = plusOneButton.getContainerInfo().getAnchorRow();
    const buttonCol = plusOneButton.getContainerInfo().getAnchorColumn();

    // Ensure the currently selected cell is on the same row and in a
    //  "reasonable" col.
    const selectedCell = sheet.getSelection().getCurrentCell();
    if (selectedCell.getRow() != buttonRow) {
      showAlert("Select a cell in the same row as the +1 button");
      return;
    }
    if (selectedCell.getColumn() >= buttonCol) {
      showAlert("Select a cell at the left of the +1 button");
      return;
    }

    // Finally increment the value.
    let currentValue = selectedCell.getValue();
    if (!currentValue) currentValue = 0;
    selectedCell.setValue(currentValue + 1);    
  }
}
