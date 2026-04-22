import { describe, expect, it } from "vitest";

import { candidatesToCsv } from "./csv";

describe("candidatesToCsv", () => {
  it("serializes candidate rows with headers", () => {
    const csv = candidatesToCsv([
      {
        rank: 1,
        title: "Travel Hanging Toiletry Organizer",
        price: 29.99,
        sold_count: 2400,
        review_count: 18,
        score: 88.08,
        early_window: true,
        keyword: "travel organizer",
        seller: "Avori Demo Shop",
      },
    ]);

    expect(csv).toContain("title,price,sold_count");
    expect(csv).toContain("Travel Hanging Toiletry Organizer");
  });
});
