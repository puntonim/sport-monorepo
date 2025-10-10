class InvalidSelection extends BaseError { }
class NotADate extends BaseError { }
class ActivityAlreadyHasDescription extends BaseError { }
class ActivityNotFound extends BaseError { }
class ResponseError extends BaseError { }
class FormatError extends BaseError { }
class InvalidHour extends BaseError { }
class InvalidMinute extends BaseError { }


class UpdateStravaButton {
  constructor() {
    /// Cached data.
    // Data from the Sheet.
    this.__parsedDate = null; // [ParsedDate] <------------------ this._parseDate();
    this.__parsedTitle = null; // [str] <------------------------ this._parseTitle();
    this.__parsedNote = null; // [str] <------------------------- this._parseNote();
    // list[obj{name: [str], reps: [str], sets: [num]}]
    this.__parsedExercises = null; // <-------------------------- this._parseExercises();
    // Detect the kind of activity in the Sheet.
    this.__isCalisthenicsClass = null; // [bool] <--------------- this._isCalisthenicsClass();
    this.__isPowerliftingClass = null; // [bool] <--------------- this._isPowerliftingClass();
    // Data for the Strava activity to update/create.
    this.__newDescriptionForStravaActivity = null; // [str] <---- this._makeNewDescriptionForStravaActivity();
    this.__newNameForStravaActivity = null; // [str] <----------- this._makeNewNameForStravaActivity();

    this.stravaFacadeApiClient = new StravaFacadeApiClient();
  }

  click() {
    /**
     * Invoked when clicking on the "Update Strava" button.
     * Get the selected gym session log and post to my strava-facade-api Lambda
     *  in order to update an existing Strava activity's description
     *  or to create a new Strava activity.
     */
    // Collect the selected cells' content.
    const selection = SpreadsheetApp.getActiveSpreadsheet().getSelection();
    this.activeRange = selection.getActiveRange();

    // Ensure the selected range "seems" valid.
    try {
      this._ensureSelectionIsValid()
    } catch (err) {
      return;
    }

    // Search for an existing activity at the parsed date.
    let existingActivities = null;
    try {
      existingActivities = this.stravaFacadeApiClient.listActivities({
        afterTs: dateToTimestamp(this._parseDate().getStartDate()),
        beforeTs: dateToTimestamp(this._parseDate().getEndDate())
      });
    } catch (err) {
      throw err;
    }

    // No existing activity was found in Strava.
    if (!existingActivities.length) {
      // If it's a regular activity (NOT a cali|power class), then show a WARNING msg as we expect the activity to exist already in Strava.
      if (!this._isCalisthenicsClass() && !this._isPowerliftingClass()) {
        const isConfirmed = this._warnExistingActivityExpectedMsg();
        if (!isConfirmed) return;
      }

      // Ask the user for the start time and duration: it updates this.__parsedDate.
      this._askStartTimeAndDurationMsg();

      // Create the new activity in Strava.
      this._createNewStravaActivity();
    }

    // At least 1 existing activity was found in Strava.
    else {
      // Ask the user if he really wants to update the first (or the only one) activity found in Strava (the most recent).
      const isConfirmed = this._confirmUpdateExistingActivityMsg(existingActivities);
      if (!isConfirmed) return;
      const existingActivity = existingActivities[0];

      // If it's a cali|power class, then show a WARNING msg as we do not expect the activity to exist already in Strava.
      if (this._isCalisthenicsClass() || this._isPowerliftingClass()) {
        const isConfirmed = this._warnNonExistingActivityExpectedMsg(existingActivity);
        if (!isConfirmed) return;
      }

      // Update the existing activity in Strava.
      this._updateExistingStravaActivity(existingActivity.id);
    }
  }

  _ensureSelectionIsValid() {
    /**
     * Ensure the selected range "seems" valid.
     */
    if (this.activeRange.getHeight() == 4) {
      // A regular gym session log.
      if (this.activeRange.getWidth() < 1 || this.activeRange.getWidth() > 20 ) {
        showAlert("The selected range does not seem a valid session log: 1 > width > 20");
        throw new InvalidSelection();
      }
    } else if (this.activeRange.getHeight() == 1) {
      // A special gym session log like a calisthenics session at Reborn.
      if (this.activeRange.getWidth() != 4 ) {
        showAlert("The selected range does not seem a valid session log: width != 4");
        throw new InvalidSelection();
      }
    } else {
      showAlert("The selected range does not seem a valid session log: height != 4");
      throw new InvalidSelection();
    }
  }

  _parseDate() {
    /**
     * Parse data: date.
     */
    if (this.__parsedDate !== null) return this.__parsedDate;

    const originalParsedDate = this.activeRange.getCell(1, 1).getValue();

    if (!(originalParsedDate instanceof Date)) {
      showAlert("Not a valid date: " + originalParsedDate);
      throw new NotADate();
    }

    this.__parsedDate = new ParsedDate({originalParsedDate: originalParsedDate});
    return this.__parsedDate;
  }

  _parseTitle() {
    /**
     * Parse data: title.
     */
    if (this.__parsedTitle !== null) return this.__parsedTitle;

    // Old code that used to pre-pend "Weight training".
    // const title = this.activeRange.getCell(1, 2).getValue();
    // this.__parsedTitle = "Weight training: " + title[0].toLowerCase() + title.slice(1);
    // return this.__parsedTitle;

    this.__parsedTitle = this.activeRange.getCell(1, 2).getValue();
    return this.__parsedTitle;
  }

  _parseNote() {
    /**
     * Parse data: note.
     */
    if (this.__parsedNote !== null) return this.__parsedNote;

    try {
      this.__parsedNote = this.activeRange.getCell(1, 4).getValue() || null;
    } catch (err) {
      // If there are less 4 exercises in the workout, then the note is out of the selected
      //  range. In this case we just try to get the cell outside the selected range.
      if (err.message.includes("Cell reference out of range")) {
        const dateCell = this.activeRange.getCell(1, 1);
        const c = dateCell.getColumn() + 3;
        const r = dateCell.getRow();
        this.__parsedNote = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet().getRange(r, c).getValue() || null;
      }
    }
    return this.__parsedNote;
  }

  _parseExercises() {
    /**
     * Parse data: exercises.
     */
    if (this.__parsedExercises !== null) return this.__parsedExercises;

    this.__parsedExercises = [];
    if (!(this._isCalisthenicsClass())) {
      for (let col = 1; col <= this.activeRange.getWidth(); col++) {
        const name = this.activeRange.getCell(2, col).getValue();
        // Note: reps is not alwyas a number, it can be a str like "30s".
        const reps = this.activeRange.getCell(3, col).getValue();
        const sets = this.activeRange.getCell(4, col).getValue();
        if (!Number.isInteger(sets) || sets < 1 || sets > 90) {
          showAlert("Not a valid sets counter: " + sets);
          return;
        }
        this.__parsedExercises.push({name: name, reps: reps, sets: sets});
      }
    }
    return this.__parsedExercises;
  }

  _isCalisthenicsClass() {
    /**
     * Detect if the session log is a CALISTHENICS class at Reborn.
     * It happens if:
     *  - the title includes "Calisthenics" (it's usually "Calisthenics class" or (old) "Calisthenics").
     *  - the note includes "Reborn" (it's usually "Corso palestra Reborn: handstand" or "Corso YouReborn: handstand").
     */
    if (this.__isCalisthenicsClass !== null) return this.__isCalisthenicsClass;

    if (this._parseTitle() && this._parseTitle().toLowerCase().includes("calisthenics") &&
        this._parseNote() && this._parseNote().toLowerCase().includes("reborn")) {
      this.__isCalisthenicsClass = true;
    } else {
      this.__isCalisthenicsClass = false;
    }
    return this.__isCalisthenicsClass;
  }

  _isPowerliftingClass() {
    /**
     * Detect if the session log is a POWERLIFTING class at Reborn.
     * It happens if:
     *  - the title includes "Powerlifting" (it's usually "Powerlifting class" or (old) "Powerlifting").
     *  - the note includes "Reborn" (it's usually "Corso palestra Reborn" or "Corso YouReborn").
     */
    if (this.__isPowerliftingClass !== null) return this.__isPowerliftingClass;

    if (this._parseTitle() && this._parseTitle().toLowerCase().includes("powerlifting") &&
        this._parseNote() && this._parseNote().toLowerCase().includes("reborn")) {
      this.__isPowerliftingClass = true;
    } else {
      this.__isPowerliftingClass = false;
    }
    return this.__isPowerliftingClass;
  }

  _updateExistingStravaActivity(activityId) {
    /**
     * Update an existing activity in Strava.
     */
    const data = {
          activityId: activityId,
          description: this._makeNewDescriptionForStravaActivity(),
          name: this._makeNewNameForStravaActivity(),
          doStopIfDescriptionNotNull: true,
    };
    let response = null;
    try {
      response = this.stravaFacadeApiClient.updateActivityDescription(data);
    } catch (err) {
      if (err instanceof ActivityAlreadyHasDescription) {
        const tokens = err.toString().split("description=");
        // Display the error msg got from the BE in a nicer way (replacing \r\n with actual line breaks).
        const text = tokens[0] + "\n\n" + tokens[1].replaceAll("\\n", "\n").replaceAll("\\r", "") + "\n\nOverwrite?";
        const yesOrNo = showYesNoAlert(text);
        if (!yesOrNo) return; // "no" answer.
        response = this.stravaFacadeApiClient.updateActivityDescription({...data, doStopIfDescriptionNotNull: false});
      } else {
        throw err;
      }
    }

    // Open a new browser tab with the Strava activity.
    openUrlInNewBrowserTab("https://www.strava.com/activities/" + response.id, "Opening Strava...");
  }

  _createNewStravaActivity() {
    /**
     * Create a new activity in Strava.
     */
    const durationSeconds = this._parseDate().getDuration().min * 60 + this._parseDate().getDuration().hour * 60 * 60;
    const response = this.stravaFacadeApiClient.createActivity({
      startDateString: dateToIsoString(this._parseDate().getStartDate()),
      durationSeconds: durationSeconds,
      description: this._makeNewDescriptionForStravaActivity(),
      name: this._makeNewNameForStravaActivity(),
    });

    // Open a new browser tab with the Strava activity.
    const activityId = response.id;
    openUrlInNewBrowserTab("https://www.strava.com/activities/" + activityId, "Opening Strava...");
  }

  _makeNewNameForStravaActivity() {
    if (this.__newNameForStravaActivity !== null) return this.__newNameForStravaActivity;

    this.__newNameForStravaActivity = this._parseTitle();
    return this.__newNameForStravaActivity;
  }

  _makeNewDescriptionForStravaActivity() {
    if (this.__newDescriptionForStravaActivity !== null) return this.__newDescriptionForStravaActivity;

    let desc = "";
    const note = this._parseNote();

    if (this._isCalisthenicsClass()) {
      if (note) {
        const noteTokens = note.split(": ");
        desc = noteTokens[1].substring(0, 1).toUpperCase() + noteTokens[1].substring(1);
        desc += "\n\nNote: " + noteTokens[0].substring(0, 1).toLowerCase() + noteTokens[0].substring(1);
      }
    } else {
      for (let exercise of this._parseExercises()) {
        desc += exercise.name + ": " + exercise.reps + " reps x " + exercise.sets + " sets\n"
      }
      if (note) desc += "\n\nNote: " + note.substring(0, 1).toLowerCase() + note.substring(1);
    }

    this.__newDescriptionForStravaActivity = desc;
    return this.__newDescriptionForStravaActivity;
  }

  _confirmUpdateExistingActivityMsg(existingActivities) {
    /**
     * Ask, with a GUI message, to confirm the update of the first (or the only one) activity found in Strava (the most recent).
     */
    let text = "Found #" + existingActivities.length + " activities:";
    for (let activity of existingActivities) {
      text += "\n\nId: " + activity.id;
      text += "\nName: " + activity.name;
      text += "\nTs: " + activity.start_date_local;
    }
    if (existingActivities.length > 1) text += `\n\nUpdate the 1st one: ${existingActivities[0].name}?`;
    else text += "\n\nUpdate it?";
    return showYesNoAlert(text);
  }

  _askStartTimeAndDurationMsg() {
    /**
     * Ask, with a GUI message, for the start time and duration. And update this.__parsedDate.
     */
    const parsedDate = this._parseDate();

    // Set default values for the start time at 20:00 and duration 1 hour.
    let startHour = 20;
    let startMin = 0;
    let durationHour = 1;
    let durationMin = 0;
    // The power class starts at 19:00 and the cali at 20:00.
    startHour = this._isPowerliftingClass() ? 19 : startHour;
    startHour = this._isCalisthenicsClass() ? 20 : startHour;
    // If the parsed date included precise start hour and min, then use them.
    if (parsedDate.hasPreciseHourAndMin()) {
      startHour = parsedDate.getOriginalParsedDate().getHours();
      startMin = parsedDate.getOriginalParsedDate().getMinutes();
    }

    // Ask with GUI to type the start time and duration.
    let text = "Default (leave blank): ";
    text += startHour.toLocaleString("en-US", {
      minimumIntegerDigits: 2,
      useGrouping: false
    });
    text += ":";
    text += startMin.toLocaleString("en-US", {
      minimumIntegerDigits: 2,
      useGrouping: false
    });
    text += ` ${durationHour}:`;
    text += durationMin.toLocaleString("en-US", {
      minimumIntegerDigits: 2,
      useGrouping: false
    });
    let response = showPrompt("Start time and duration?", text);

    // The user confirmed the default values.
    if (response === "") {
      this.__parsedDate = new ParsedDate({
        originalParsedDate: parsedDate.getOriginalParsedDate(),
        startHourInput: startHour,
        startMinInput: startMin,
        durationHourInput: durationHour,
        durationMinInput: durationMin,
      });
      return;
    }

    // Split start time and duration.
    response = response.split(" ");
    if (!(response[0]) || !(response[1])) {
      throw new FormatError("Must be in the format: 20:00 1:00");
    }
    const startTimeString = response[0];
    const durationString = response[1];

    // Parse start time.
    const startTimeTokens = startTimeString.split(":");
    if (!(startTimeTokens[0]) || !(startTimeTokens[1])) {
      throw new FormatError("Must be in the format: 20:00 1:00");
    }
    startHour = parseInt(startTimeTokens[0]);
    startMin = parseInt(startTimeTokens[1]);
    if (isNaN(startHour) || startHour < 0 || startHour > 23) {
      throw new InvalidHour(hour);
    }
    if (isNaN(startMin) || startMin < 0 || startMin > 59) {
      throw new InvalidMinute(startMin);
    }

    // Parse duration.
    const durationTokens = durationString.split(":");
    if (!(durationTokens[0]) || !(durationTokens[1])) {
      throw new FormatError("Must be in the format: 20:00 1:00");
    }
    durationHour = parseInt(durationTokens[0]);
    durationMin = parseInt(durationTokens[1]);
    if (isNaN(durationHour) || durationHour < 0 || durationHour > 23) {
      throw new InvalidHour(durationHour);
    }
    if (isNaN(durationMin) || durationMin < 0 || durationMin > 59) {
      throw new InvalidMinute(durationMin);
    }

    // Finally set this.__parsedDate.
    this.__parsedDate = new ParsedDate({
      originalParsedDate: parsedDate.getOriginalParsedDate(),
      startHourInput: startHour,
      startMinInput: startMin,
      durationHourInput: durationHour,
      durationMinInput: durationMin,
    });
  }

  _warnExistingActivityExpectedMsg() {
    /**
     * Show a GUI WARNING msg as we expect the activity to exist already in Strava, but it doesn't exist.
     * It's useful only for regular (non cali|power) activities.
     */
    let text = "\n********************************  W A R N I N G ********************************\n\n";
    text += "For a regular activity, we expect it to EXIST ALREADY in Strava, yet it does NOT exists in this case.\n\n";
    text += "Continue with the *CREATION*?";
    return showYesNoAlert(text);
  }

  _warnNonExistingActivityExpectedMsg(existingActivity) {
    /**
     * Show a GUI WARNING msg as we do NOT expect the activity to exist already in Strava, but it does exist.
     * It's useful only for cali|power classes.
     */
    // If it's a cali|power class, then
    let text = "\n********************************  W A R N I N G ********************************\n\n";
    text += "For a Cali or Power class, we do NOT expect the activity to EXIST ALREADY in Strava, yet it exists in this case.\n\n";
    text += `Name: ${existingActivity.name}\n`;
    text += `https://www.strava.com/activities/${existingActivity.id}\n\n`;
    text += "Continue with the *UPDATE*?";
    return showYesNoAlert(text);
  }

} // End class UpdateStravaButton.


class ParsedDate {
  constructor({originalParsedDate, startHourInput = null, startMinInput = null, durationHourInput = null, durationMinInput = null}) {
    // Date object, eg. Sun Sep 28 00:00:00 GMT+02:00 2025 or Sun Sep 28 19:30:00 GMT+02:00 2025.
    this.__originalParsedDate = originalParsedDate;
    this.__startHourInput = startHourInput; // eg. 19.
    this.__startMinInput = startMinInput;  // eg. 0 or 30.
    this.__durationHourInput = durationHourInput;  // eg. 1.
    this.__durationMinInput = durationMinInput;  // eg. 0.
  }

  getDuration() {
    return {hour: this.__durationHourInput, min: this.__durationMinInput};
  }

  hasPreciseHourAndMin() {
    if (this.getOriginalParsedDate().getHours()+this.getOriginalParsedDate().getMinutes() !== 0) return true;
    else return false;
  }

  getOriginalParsedDate() {
    return this.__originalParsedDate;
  }

  getStartDate() {
    /**
     * Get the start date (type Date) of the activity. The hours and mins are
     *  either taken from the Sheet (if it has precise hour and min written)
     *  or requested with a GUI message (if the activity does not exist in Strava yet),
     *  or set to 0:00:00.
     */
    let startDate = new Date(this.getOriginalParsedDate().valueOf());
    if ((this.__startHourInput != null) && (this.__startMinInput != null)) {
      startDate.setHours(this.__startHourInput, this.__startMinInput, 0);
    }
    return startDate; // type Date.
  }

  getEndDate() {
    /**
     * Get the end date (type Date) of the activity. The duration hour and mins are
     *  either requested with a GUI message (if the activity does not exist in Strava yet),
     *  or set to 23:59:59.
     */
    let endDate = new Date(this.getStartDate().valueOf());
    if ((this.__durationHourInput != null) && (this.__durationMinInput != null)) {
      endDate.setHours(
        endDate.getHours()+this.__durationHourInput,
        endDate.getMinutes()+this.__durationMinInput);
    } else {
      // Set the time to 23:59:59.
      endDate.setHours(23, 59, 59);
    }
    return endDate; // type Date.
  }

} // End class ParsedDate.


class StravaFacadeApiClient {
  listActivities ({afterTs, beforeTs}) {
    /**
     * GET request to my strava-facade-api Lambda
     *  in order to list Strava activities.
     *
     * Example:
     *  $ curl "https://ejxyxviele.execute-api.eu-south-1.amazonaws.com/activity?after-ts=1739374800&before-ts=1739376800&activity-type=WeightTraining&n-results-per-page=10&page-n=1" \
     *       -H 'Authorization: XXX'
     */
    Logger.log("START request to Lambda");

    // Make a GET request with query string.
    const options = {
      "method": "get",
      "headers": {
        "authorization": STRAVA_FACADE_API_SECRET,
      },
      "muteHttpExceptions": true,
    };
    let url = STRAVA_FACADE_API_BASE_URL + "/activity?after-ts=" + afterTs;
    url += "&before-ts=" + beforeTs;
    url += "&activity-type=WeightTraining";
    url += "&n-results-per-page=10&page-n=1";
    // Docs: https://developers.google.com/apps-script/reference/url-fetch/url-fetch-app
    const response = UrlFetchApp.fetch(url, options);
    const responseBody = response.getContentText();
    const responseCode = response.getResponseCode();
    Logger.log(responseBody);

    if (responseCode > 299) {
      const msg = "Status code: " + responseCode + "\nBody: " + responseBody;
      showAlert(`\n************************ E R R O R ************************\n\nError response from Lambda strava-facade-api-*!\n\n${msg}`);
      throw new ResponseError(msg);
    }
    Logger.log("END request to Lambda");
    return JSON.parse(responseBody);
  }

  updateActivityDescription({activityId, description, name, doStopIfDescriptionNotNull=true}) {
    /**
     * POST request to my strava-facade-api Lambda
     *  in order to update an existing Strava activity's description.
     */
    Logger.log("START request to Lambda");

    // doStopIfDescriptionNotNull must be a string and not a bool.
    if (doStopIfDescriptionNotNull) doStopIfDescriptionNotNull = "true";
    else doStopIfDescriptionNotNull = "false";

    // Make a POST request with a JSON payload.
    const data = {
      "activityId": activityId,
      "description": description,
      "activityType": "WeightTraining",
      "name": name,
      "doStopIfDescriptionNotNull": doStopIfDescriptionNotNull,
    };
    const options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(data),
      "headers": {
        "authorization": STRAVA_FACADE_API_SECRET,
      },
      "muteHttpExceptions": true,
    };
    // Docs: https://developers.google.com/apps-script/reference/url-fetch/url-fetch-app
    const response = UrlFetchApp.fetch(STRAVA_FACADE_API_BASE_URL + "/update-activity-description", options);
    const responseBody = response.getContentText();
    const responseCode = response.getResponseCode();
    Logger.log(responseBody);

    if ((responseCode === 400) && (responseBody.includes("The activity found already has a description"))) {
      throw new ActivityAlreadyHasDescription(responseBody);
    } else if (responseCode === 404) {
      throw new ActivityNotFound();
    } else if (responseCode > 299) {
      const msg = "Status code: " + responseCode + "\nBody: " + responseBody;
      showAlert(`** Error response from Lambda strava-facade-api-*! **\n\n${msg}`);
      throw new ResponseError(msg);
    }
    Logger.log("END request to Lambda");
    return JSON.parse(responseBody);
  }

  createActivity({startDateString, durationSeconds, description, name}) {
    /**
     * POST request to my strava-facade-api Lambda
     *  in order to create a new Strava activity.
     *
     * Example:
     *  $ curl -X POST https://ejxyxviele.execute-api.eu-south-1.amazonaws.com/create-activity \
     *       -H 'Authorization: XXX' \
     *       -d '{"name": "test1", "activityType": "WeightTraining", "startDate": "2024-07-25T18:17:33.983+02:00" "durationSeconds": 3960, "description": "My new descr"}'
     */
    Logger.log("START request to Lambda");

    // Make a POST request with a JSON payload.
    const data = {
      "startDate": startDateString,
      "durationSeconds": durationSeconds,
      "description": description,
      "activityType": "WeightTraining",
      "name": name,
    };
    const options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(data),
      "headers": {
        "authorization": STRAVA_FACADE_API_SECRET,
      },
      "muteHttpExceptions": true,
    };
    // Docs: https://developers.google.com/apps-script/reference/url-fetch/url-fetch-app
    const response = UrlFetchApp.fetch(STRAVA_FACADE_API_BASE_URL + "/create-activity", options);
    const responseBody = response.getContentText();
    const responseCode = response.getResponseCode();
    Logger.log(responseBody);

    if (responseCode > 299) {
      const msg = "Status code: " + responseCode + "\nBody: " + responseBody;
      showAlert(`** Error response from Lambda strava-facade-api-*! **\n\n${msg}`);
      throw new ResponseError(msg);
    }
    Logger.log("END request to Lambda");
    return JSON.parse(responseBody);
  }
} // End class UpdateStravaButton.
