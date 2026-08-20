const onDocumentReady = () => {
  main();
};
document.addEventListener("DOMContentLoaded", onDocumentReady);

const main = () => {
  const containerEl = document.querySelector("#test-container");

  // TODO these dates will be arguments to this function.
  const dateStart = new Date("2026-03-12T23:35:00.150993+02:00");
  const dateEnd = new Date("2026-11-10T23:35:00.150993+02:00");

  const date = dateStart;
  // Create the month calendar for the given date.
  while (true) {
    insertMonthCalendar(date, containerEl);
    // Incrementing the date to the next month (and day 1).
    date.setMonth(date.getMonth() + 1, 1);
    if (date > dateEnd) break;
  }

  insertActivities(CALENDAR_DATA);
};

const insertMonthCalendar = (date, containerEl) => {
  const firstDayOfMonth = getFirstDayOfMonth(date);
  const lastDayOfMonth = getLastDayOfMonth(date);
  const firstDayInMonthCalendar = getPrecedingMonday(firstDayOfMonth);
  const lastDayInMonthCalendar = getSucceedingSunday(lastDayOfMonth);

  // Relative to the monthly calendar being created.
  const yearInt = date.getFullYear();
  const monthShort = getMonthName(date, "short");
  const monthInt = date.getMonth() + 1; // Jan = 1.

  // Add month title.
  let html = `<div class="month-title">${monthShort} ${yearInt}</div>\n`;
  // Add grid div.
  html += `<div class="grid month-${monthInt}-${yearInt}">\n`;

  // Iterate over all days shown in the month calendar.
  const d = new Date(firstDayInMonthCalendar);
  let i = 1;
  let row = 1;
  let col = 1;
  while (d <= lastDayInMonthCalendar) {
    // Relative to the single day being created.
    const curDayInt = d.getDate();
    const curMonthInt = d.getMonth() + 1; // Jan = 1.
    const curMonthShort = getMonthName(d, "short");
    const curYearInt = d.getFullYear();

    // Check for outsider days (do not belong to the current month).
    let isOutsider = false;
    if (d < firstDayOfMonth || d > lastDayOfMonth) isOutsider = true;

    // Add the single day.
    html += `<div class="item row-${row} col-${col} day-${curDayInt}-${curMonthInt}-${curYearInt}${isOutsider ? " outsider" : ""}">\n`;
    // Add "MON", "TUE", ...
    if (row == 1) {
      html += `<div class="dow">${getDayOfWeekName(d, "short").toUpperCase()}</div>\n`;
    }
    // Add the date like 30, 31, 1, 2, ...
    let doAddMonthName = false;
    if (
      getNextDay(d).getTime() === firstDayOfMonth.getTime() ||
      d.getTime() === firstDayOfMonth.getTime() ||
      getPrevDay(d).getTime() === lastDayOfMonth.getTime()
    ) {
      doAddMonthName = true;
    }
    html += `<div class="date">${curDayInt}${doAddMonthName ? " " + curMonthShort.toLowerCase() : ""}</div>\n`;

    html += `</div>\n`;

    // If it's Sunday, add the weekly recap and increment the row.
    if ((i !== 1) & (i % 7 === 0)) {
      html += `<div class="item row-${row} col-8 recap-week">\n`;
      html += `</div>\n`;
      row++;
    }

    // Increment all counters.
    i++;
    col++;
    if (col >= 8) col = 1;
    setNextDayInPlace(d);
  }

  // Add end grid div.
  html += `</div><!-- end ${monthShort} ${yearInt} -->\n\n`;

  // Append the month calendar HTML.
  containerEl.insertAdjacentHTML("beforeend", html);

  // Add the class .row-last to the last row.
  for (let divEl of containerEl.querySelectorAll(
    `.month-${monthInt}-${yearInt} .row-${row - 1}`,
  )) {
    divEl.classList.add("row-last");
  }
};

const insertActivities = (calendarData) => {
  for (let item of calendarData) {
    // TODO handle WEEKLY_RECAP
    if (item.itemType !== "DAY") continue;

    const date = new Date(item.date);

    // TODO TEMP filter just to fill this calendar.........
    if (date < new Date("2026-02-23T00:00:00+02:00")) continue;

    // Get all DIVs for the current day.
    // Note: a day can be shown 2 times: fi. thu 30 April 2026 is shown in April month
    //  calendar, but also in May as grayed out outsider day.
    for (let dayEl of document.querySelectorAll(
      `.day-${date.getDate()}-${date.getMonth() + 1}-${date.getFullYear()}`,
    )) {
      // Insert the activities HTML for the current day.
      let html = `<div class="activities-container">\n`;
      for (let activity of item.activities) {
        html += `<div class="activity ${activity.sport}">${activity.shortDescription}</div>\n`;
      }
      html += "</div>\n";
      dayEl.insertAdjacentHTML("beforeend", html);
    }
  }
};
