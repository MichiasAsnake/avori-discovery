import { describe, expect, it } from "vitest";

import { scoreTier } from "./score";

describe("scoreTier", () => {
  it("maps strong scores to high", () => {
    expect(scoreTier(90)).toBe("high");
  });

  it("maps middling scores to medium", () => {
    expect(scoreTier(52)).toBe("medium");
  });

  it("maps low scores to low", () => {
    expect(scoreTier(15)).toBe("low");
  });
});
