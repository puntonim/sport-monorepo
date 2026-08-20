/**
 * Given a date (as ISO string or Date), return the first day of the same month.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getFirstDayOfMonth = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  // Setting the day to 1.
  date.setDate(1);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the preceding Monday.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getPrecedingMonday = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  const dayOfWeek = date.getDay();

  // Calculate how many days to subtract to find the preceding Monday.
  // If the 1st is:
  // - a Sunday (0): subtract 6 days;
  // - a Monday (1) through Saturday (6): subtract dayOfWeek-1 days.
  const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
  date.setDate(date.getDate() - daysToSubtract);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the last day of the same month.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getLastDayOfMonth = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);

  // Trick: setting the day parameter to 0 rolls the date back to the last
  //  day of the previous month.
  date.setMonth(date.getMonth() + 1, 0);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the succeeding Sunday.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getSucceedingSunday = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  const dayOfWeek = date.getDay();

  // Calculate how many days to add to find the succeeding Sunday.
  // If the date is:
  // - a Sunday (0): add 0 days (it's already Sunday);
  // - a Monday (1) through Saturday (6): add 7 - dayOfWeek days.
  const daysToAdd = dayOfWeek === 0 ? 0 : 7 - dayOfWeek;
  date.setDate(date.getDate() + daysToAdd);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the next day.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getNextDay = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  date.setDate(date.getDate() + 1);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the previous day.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const getPrevDay = (isoStringOrDate) => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  date.setDate(date.getDate() - 1);
  return date;
};

/**
 * Given a date, change it in-placere to the next day.
 * @param {Date} eg. new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const setNextDayInPlace = (date) => {
  date.setDate(date.getDate() + 1);
  return date;
};

/**
 * Given a date, change it in-placere to the previous day.
 * @param {Date} eg. new Date("2026-07-15T23:35:00.150993+02:00");
 * @returns {Date}
 */
const setPrevDayInPlace = (date) => {
  date.setDate(date.getDate() - 1);
  return date;
};

/**
 * Given a date (as ISO string or Date), return the day of week name.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @param {string} format, either "long" or "short";
 * @returns {string} eg. "Monday".
 */
const getDayOfWeekName = (isoStringOrDate, format = "long") => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  if (format !== "long" && format !== "short") {
    throw new Error("Only 'long' and 'short' format allowed!");
  }
  return date.toLocaleString("default", { weekday: format });
};

/**
 * Given a date (as ISO string or Date), return the month name.
 * @param {string or Date} eg. "2026-07-15T23:35:00.150993+02:00" or new Date("2026-07-15T23:35:00.150993+02:00");
 * @param {string} format, either "long" or "short";
 * @returns {string} eg. "January".
 */
const getMonthName = (isoStringOrDate, format = "long") => {
  // Convert ISO string (or Date) to a Date object.
  const date = new Date(isoStringOrDate);
  if (format !== "long" && format !== "short") {
    throw new Error("Only 'long' and 'short' format allowed!");
  }
  return date.toLocaleString("default", { month: format });
};

// /**
//  * Tests for getFirstDayOfMonth -----------------------------------------------------
//  */
// // A random day (15).
// getFirstDayOfMonth("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-01T23:35:00.150993+02:00").getTime();
// // Date object input.
// getFirstDayOfMonth(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-01T23:35:00.150993+02:00").getTime();
// // The 1st day of month.
// getFirstDayOfMonth("2026-07-01T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-01T23:35:00.150993+02:00").getTime();
// // The last day of month.
// getFirstDayOfMonth("2026-07-31T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-01T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getFirstDayOfMonth("2026-07-15T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-01T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getFirstDayOfMonth("2026-07-31T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-08-01T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getPrecedingMonday -----------------------------------------------------
//  */
// // A Tuesday.
// getPrecedingMonday("2026-08-18T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-08-17T23:35:00.150993+02:00").getTime();
// // Date object input.
// getPrecedingMonday(new Date("2026-08-18T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-08-17T23:35:00.150993+02:00").getTime();
// // A Wednesday.
// getPrecedingMonday("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-13T23:35:00.150993+02:00").getTime();
// // A Thursday, changing month.
// getPrecedingMonday("2026-04-02T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-03-30T23:35:00.150993+02:00").getTime();
// // A Friday, changing month and year.
// getPrecedingMonday("2026-01-02T23:35:00.150993+02:00").getTime() ===
//   new Date("2025-12-29T23:35:00.150993+02:00").getTime();
// // A Saturday.
// getPrecedingMonday("2026-12-05T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-11-30T23:35:00.150993+02:00").getTime();
// // A Sunday.
// getPrecedingMonday("2026-07-26T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-20T23:35:00.150993+02:00").getTime();
// // A Monday.
// getPrecedingMonday("2026-07-27T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-27T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getPrecedingMonday("2026-07-15T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-13T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getPrecedingMonday("2026-07-31T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-27T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getLastDayOfMonth ------------------------------------------------------
//  */
// // A random day (15).
// getLastDayOfMonth("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // Date object input.
// getLastDayOfMonth(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // The 1st day of the month.
// getLastDayOfMonth("2026-07-01T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // The last day of month.
// getLastDayOfMonth("2026-07-31T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getLastDayOfMonth("2026-07-15T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-31T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getLastDayOfMonth("2026-07-31T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-08-31T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getSucceedingSunday ----------------------------------------------------
//  */
// // A Tuesday.
// getSucceedingSunday("2026-08-18T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-08-23T23:35:00.150993+02:00").getTime();
// // Date object input.
// getSucceedingSunday(new Date("2026-08-18T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-08-23T23:35:00.150993+02:00").getTime();
// // A Wednesday.
// getSucceedingSunday("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-19T23:35:00.150993+02:00").getTime();
// // A Thursday, changing month.
// getSucceedingSunday("2026-04-30T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-05-03T23:35:00.150993+02:00").getTime();
// // A Friday, changing month and year.
// getSucceedingSunday("2021-12-31T23:35:00.150993+02:00").getTime() ===
//   new Date("2022-01-02T23:35:00.150993+02:00").getTime();
// // A Saturday.
// getSucceedingSunday("2026-12-05T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-12-06T23:35:00.150993+02:00").getTime();
// // A Sunday.
// getSucceedingSunday("2026-08-02T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-08-02T23:35:00.150993+02:00").getTime();
// // A Monday, changing month.
// getSucceedingSunday("2026-06-29T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-05T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getSucceedingSunday("2026-07-15T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-19T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getSucceedingSunday("2026-07-31T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-08-02T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getNextDay -------------------------------------------------------------
//  */
// // A random day (15).
// getNextDay("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-16T23:35:00.150993+02:00").getTime();
// // // Date object input.
// getNextDay(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-16T23:35:00.150993+02:00").getTime();
// // Last day of the month.
// getNextDay("2026-07-31T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-08-01T23:35:00.150993+02:00").getTime();
// // Last day of the year.
// getNextDay("2026-12-31T23:35:00.150993+02:00").getTime() ===
//   new Date("2027-01-01T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getNextDay("2026-07-15T23:35:00.150993+00:00").getTime() ===
//   new Date("2026-07-17T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getNextDay("2026-12-30T23:35:00.150993+00:00").getTime() ===
//   new Date("2027-01-01T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getPrevDay ----------------------------------------------------------------
//  */
// // A random day (15).
// getPrevDay("2026-07-15T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-14T23:35:00.150993+02:00").getTime();
// // Date object input.
// getPrevDay(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-14T23:35:00.150993+02:00").getTime();
// // First day of the month.
// getPrevDay("2026-08-01T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // First day of the year.
// getPrevDay("2027-01-01T23:35:00.150993+02:00").getTime() ===
//   new Date("2026-12-31T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// getPrevDay("2026-07-17T01:35:00.150993+02:00").getTime() ===
//   new Date("2026-07-15T23:35:00.150993+00:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// getPrevDay("2027-01-01T01:35:00.150993+02:00").getTime() ===
//   new Date("2026-12-30T23:35:00.150993+00:00").getTime();

// /**
//  * Tests for setNextDayInPlace ------------------------------------------------------
//  */
// // A random day (15).
// setNextDayInPlace(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-16T23:35:00.150993+02:00").getTime();
// // String object input.
// try {
//   setNextDayInPlace("2026-07-15T23:35:00.150993+02:00");
// } catch (e) {
//   e.name === "TypeError";
// }
// // Last day of the month.
// setNextDayInPlace(new Date("2026-07-31T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-08-01T23:35:00.150993+02:00").getTime();
// // Last day of the year.
// setNextDayInPlace(new Date("2026-12-31T23:35:00.150993+02:00")).getTime() ===
//   new Date("2027-01-01T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// setNextDayInPlace(new Date("2026-07-15T23:35:00.150993+00:00")).getTime() ===
//   new Date("2026-07-17T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// setNextDayInPlace(new Date("2026-12-30T23:35:00.150993+00:00")).getTime() ===
//   new Date("2027-01-01T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for setPrevDayInPlace ------------------------------------------------------
//  */
// // A random day (15).
// setPrevDayInPlace(new Date("2026-07-15T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-14T23:35:00.150993+02:00").getTime();
// // String object input.
// try {
//   setPrevDayInPlace("2026-07-15T23:35:00.150993+02:00");
// } catch (e) {
//   e.name === "TypeError";
// }
// // First day of the month.
// setPrevDayInPlace(new Date("2026-08-01T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-07-31T23:35:00.150993+02:00").getTime();
// // First day of the year.
// setPrevDayInPlace(new Date("2027-01-01T23:35:00.150993+02:00")).getTime() ===
//   new Date("2026-12-31T23:35:00.150993+02:00").getTime();
// // Different timezone: it converts to the local timezone.
// setPrevDayInPlace(new Date("2026-07-15T23:35:00.150993+00:00")).getTime() ===
//   new Date("2026-07-15T01:35:00.150993+02:00").getTime();
// // Different timezone with month change: first it converts to the local
// //  timezone, which results in the next month.
// setPrevDayInPlace(new Date("2027-01-01T23:35:00.150993+00:00")).getTime() ===
//   new Date("2027-01-01T01:35:00.150993+02:00").getTime();

// /**
//  * Tests for getDayOfWeekName --------------------------------------------------------------
//  */
// // July.
// getDayOfWeekName("2026-07-15T23:35:00.150993+02:00", "long") === "Wednesday";
// // Short.
// getDayOfWeekName("2026-07-15T23:35:00.150993+02:00", "short") === "Wed";
// // A Date.
// getDayOfWeekName(new Date("2026-07-15T23:35:00.150993+02:00"), "long") ===
//   "Wednesday";
// // Wrong format.
// try {
//   getDayOfWeekName("2026-07-15T23:35:00.150993+02:00", "xxx");
// } catch (e) {
//   e.name === "Error";
// }

// /**
//  * Tests for getMonthName --------------------------------------------------------------
//  */
// // July.
// getMonthName("2026-07-15T23:35:00.150993+02:00", "long") === "July";
// // Short.
// getMonthName("2026-07-15T23:35:00.150993+02:00", "short") === "Jul";
// // A Date.
// getMonthName(new Date("2026-07-15T23:35:00.150993+02:00"), "long") === "July";
// // Wrong format.
// try {
//   getMonthName("2026-07-15T23:35:00.150993+02:00", "xxx");
// } catch (e) {
//   e.name === "Error";
// }
