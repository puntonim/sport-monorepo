const isString = (value) => {
  return typeof value === 'string';
}

const dateToIsoString = (date) => {
  /**
   * Convert a date like:
   *   Mon Jul 29 2024 12:52:35 GMT+0200 (Central European Summer Time)
   * to the ISO string with the right timezone: '2024-07-29T12:52:35+02:00'.
   *
   * Note that date.toISOString() converts to GMT automatically: '2024-07-29T10:52:35.339Z'.
   */
  // Src: https://stackoverflow.com/a/17415677/1969672.
  const tzo = -date.getTimezoneOffset();
  const dif = tzo >= 0 ? '+' : '-';
  const pad = (num) => {
    return (num < 10 ? '0' : '') + num;
  };

  return date.getFullYear() +
    '-' + pad(date.getMonth() + 1) +
    '-' + pad(date.getDate()) +
    'T' + pad(date.getHours()) +
    ':' + pad(date.getMinutes()) +
    ':' + pad(date.getSeconds()) +
    dif + pad(Math.floor(Math.abs(tzo) / 60)) +
    ':' + pad(Math.abs(tzo) % 60);
}
