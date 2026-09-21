export function summarizeMonths(months) {
  let positions = 0;
  let wins = 0;
  let takes = 0;
  let stops = 0;
  const net = {};
  for (const row of months) {
    positions += row.positions;
    wins += row.wins;
    takes += row.takes;
    stops += row.stops;
    net[row.currency] = (net[row.currency] || 0) + row.net_result;
  }
  return {
    takes, stops, net,
    winRate: positions ? wins / positions * 100 : null,
    cleanWinRate: takes + stops ? takes / (takes + stops) * 100 : null,
  };
}
