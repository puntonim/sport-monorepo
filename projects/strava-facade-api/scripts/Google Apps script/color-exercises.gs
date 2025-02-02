const addColorSelectedExercisesMenuItem = () => {
  customMenu.addItem('Color selected exercises', 'colorSelectedExercisesClickHandler').addToUi();
}


class ColorSelectedExercisesMenuItem {
  click() {
    /**
     * Invoked by the menu item "Custom Menu > Color selected exercises".
     */
    // Debug: get the background color of a cell.
    // const bgHeader = sheet.getRange(609, 1).getBackground();

    const selection = SpreadsheetApp.getActiveSpreadsheet().getSelection();
    const activeRange = selection.getActiveRange();

    for (let row = 1; row <= activeRange.getHeight(); row++) {
      for (let col = 1; col <= activeRange.getWidth(); col++) {
        const absRow = activeRange.getCell(row, col).getRow();
        const absCol = activeRange.getCell(row, col).getColumn();
        const wasColored = this._colorIfExerciseCell(absRow, absCol);
        if (!(wasColored)) break;
      }
    }
  }

  _colorIfExerciseCell(row, col) {
    const triceps = ["#073763", "#cfe2f3"];
    const legs = ["#20124d", "#d9d2e9"];
    const calisthenics = ["#7f6000", "#fff2cc"];
    const chest = ["#660000", "#f4cccc"];
    const abs = ["#0c343d", "#d0e0e3"];
    const back = ["#000000", "#f3f3f3"];
    const biceps = ["#4c1130", "#ead1dc"];
    const shoulders = ["#274e13", "#d9ead3"];
    const generic = ["#666666", "#ffffff"];

    const sheet = SpreadsheetApp.getActiveSheet();
    let text = sheet.getRange(row, col).getValue();
    if (!(isString(text))) return false;
    text = text.toLowerCase();

    if (this._isTricepsExerciseText(text)) this._colorExercise(triceps, row, col);
    else if (this._isLegsExerciseText(text)) this._colorExercise(legs, row, col);
    else if (this._isCalisthenicsExerciseText(text)) this._colorExercise(calisthenics, row, col);
    else if (this._isChestExerciseText(text)) this._colorExercise(chest, row, col);
    else if (this._isAbsExerciseText(text)) this._colorExercise(abs, row, col);
    else if (this._isBackExerciseText(text)) this._colorExercise(back, row, col);
    else if (this._isBicepsExerciseText(text)) this._colorExercise(biceps, row, col);
    else if (this._isShouldersExerciseText(text)) this._colorExercise(shoulders, row, col);
    else if (this._isGenericExerciseText(text)) this._colorExercise(generic, row, col);
    else return false;

    return true;
  }

  _colorExercise(colors, row, col) {
    const sheet = SpreadsheetApp.getActiveSheet();
    sheet.getRange(row, col).setBackground(colors[0]);
    sheet.getRange(row+1, col).setBackground(colors[1]);
    sheet.getRange(row+2, col).setBackground(colors[1]);
  }

  _isTricepsExerciseText(text) {
    if (
      text.startsWith("ez bar tricep superset") ||
      text.includes("tricep extension") ||
      text === "resistance band tricep pull-down" ||
      text === "ez bar skull crusher" ||
      text === "db tricep kickback" ||
      text === "bench dip"
    ) return true;
    return false;
  }

  _isLegsExerciseText(text) {
    if (
      text === "high box 60cm step-up" ||
      text === "high box step-up" ||
      text === "single leg slider bridge" ||
      text === "nordic hamstring curl" ||
      text === "single leg hip thrust" ||
      text === "single leg bridge" ||
      text === "calf raise" ||
      text === "goblet squat" ||
      text == "plyometric vertical jump" ||
      text === "bulgarian split squat" ||
      text === "split soleus raise" ||
      text.includes("psoas march") ||
      text === "seated leg lift" ||
      text === "knee extension" ||
      text === "squat" ||
      text === "iliotibial band stretch" ||
      text === "half squat" ||
      text === "deep squat stretch" ||
      text === "elliptical trainer" ||
      text.includes("hack squat") ||
      text === "wall squat" ||
      text === "leg extension"
    ) return true;
    return false;
  }

  _isCalisthenicsExerciseText(text) {
    if (
      text.endsWith("front lever progression)") ||
      text === "tuck front lever pull-up" ||
      text === "straight bar dip" ||
      text === "parallel bar tricep dip" ||
      text === "resistance band high pull-up" ||
      text === "tuck front lever pull" ||
      text === "resistance band front lever"  ||
      text === "hanging l-sit"  ||
      text === "neutral grip tuck front lever pull-up"  ||
      text === "pull-up"  ||
      text.includes("dragon flag") ||
      text === "resistance band tuck front lever pull-up" ||
      text === "parallel bar false grip hold" ||
      text === "frog hold" ||
      text === "parallel bar l-sit hold" ||
      text === "false grip hold"
    ) return true;
    return false;
  }

  _isChestExerciseText(text) {
    if (
      text.includes("chest fly") ||
      text === "one-side push-up" ||
      text.includes("db decline bench press") ||
      text === "db 30deg bench press" ||
      text === "db 30deg bench chest fly" ||
      text === "parallel bar chest dip" ||
      text.startsWith("push-up") ||
      text.startsWith("resistance band bench press") ||
      text.startsWith("resistance band standing fly") ||
      text === "ez bar decline bench press" ||
      text === "lean-forward push-up"
    ) return true;
    return false;
  }

  _isAbsExerciseText(text) {
    if (
      text === "resistance band crunch" ||
      text === "decline crunch" ||
      text === "incline bench reverse crunch" ||
      text === "plank" ||
      text === "abs hiit 7min" ||
      text === "russian twist" ||
      text === "v-hold" ||
      text === "bicycle kicks" ||
      text === "parallel bar leg tuck" ||
      text === "parallel bar bicycle" ||
      text === "parallel bar leg raise"
    ) return true;
    return false;
  }

  _isBackExerciseText(text) {
    if (
      text.startsWith("l-sit pull-up") ||
      text === "resistance band lat pulldown" ||
      text.includes("db row") ||
      text === "australian pull-up" ||
      text === "ez bar row" ||
      text.startsWith("resistance band row") ||
      text.startsWith("pull-up") ||
      text === "seated resistance band row" ||
      text === "straight arm pushdown" ||
      text === "l-sit chin-up"
    ) return true;
    return false;
  }

  _isBicepsExerciseText(text) {
    if (
      text.includes("hammer curl") ||
      text === "preacher curl" ||
      text === "db curl" ||
      text === "ez bar curl" ||
      text === "db 30deg face-up curl" ||
      text.startsWith("resistance band curl") ||
      text.startsWith("resistance band hammer curl")
    ) return true;
    return false;
  }

  _isShouldersExerciseText(text) {
    if (
      text.startsWith("lateral raise") ||
      text.endsWith("lateral raise") ||
      text.endsWith("front raise") ||
      text === "resistance band high pull" ||
      text === "seated shoulder press" ||
      text === "db zanetti press" ||
      text === "piked shoulder taps" ||
      text.includes("shoulder press") ||
      text === "pike push-up" ||
      text === "behind body resistance band lateral raise" ||
      text === "resistance band bent-over pulls"
    ) return true;
    return false;
  }

  _isGenericExerciseText(text) {
    if (
      text === "finger rehab"
    ) return true;
    return false;
  }
}
