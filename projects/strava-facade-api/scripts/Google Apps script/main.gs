/**
 * This is a copy of the Google App Script used by the Google Sheet
 *  named "Gym sessions log". This script invokes the strava-importer-api"s
 *  Lambda function in order to update Strava.
 *
 * The source of this project is at: https://github.com/puntonim/strava-monorepo/tree/main/projects/strava-facade-api/scripts/Google%20Apps%20script
 */

class BaseError extends Error {
  constructor(message) {
    super(message);
    this.name = this.constructor.name;
  }
}

const onOpen = () => {
  /**
   * Special function run automatically when the Sheet is open.
   */

  // Navigate to the last row right when opening the sheet.
  navigateToLastRow();

  // Create the "Custom Menu".
  createCustomMenu();
  // And add the menu items:
  //  to navigate to the last row;
  //  and to color to the selected exercises.
  addGoToLastRowMenuItem();
  addColorSelectedExercisesMenuItem();
}

const addOneSetClickHandler = () => {
  /**
   * Invoked when clicking on the "+1 set" drawing button.
   */
  const button = new AddOneSetButton();
  button.click();
}

const updateStravaClickHandler = () => {
  /**
   * Invoked when clicking on the "Update Strava" drawing button.
   */
  const button = new UpdateStravaButton();
  button.click();
}

const colorSelectedExercisesClickHandler = () => {
  /**
   * Invoked by the menu item "Custom Menu > Color selected exercises".
   */
  const button = new ColorSelectedExercisesMenuItem();
  button.click();
}
