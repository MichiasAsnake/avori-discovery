import type { CandidateRow } from "@/types/avori";

const CSV_HEADERS: Array<keyof CandidateRow> = [
  "rank",
  "title",
  "price",
  "sold_count",
  "review_count",
  "score",
  "early_window",
  "keyword",
  "seller",
];

function escapeCsv(value: string | number | boolean) {
  const rendered = String(value);
  if (rendered.includes(",") || rendered.includes("\"") || rendered.includes("\n")) {
    return `"${rendered.replaceAll("\"", "\"\"")}"`;
  }
  return rendered;
}

export function candidatesToCsv(rows: CandidateRow[]) {
  const lines = [
    CSV_HEADERS.join(","),
    ...rows.map((row) => CSV_HEADERS.map((header) => escapeCsv(row[header])).join(",")),
  ];
  return lines.join("\n");
}
