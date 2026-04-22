export type ScoreTier = "high" | "medium" | "low";

export function scoreTier(score: number): ScoreTier {
  if (score >= 75) {
    return "high";
  }
  if (score >= 35) {
    return "medium";
  }
  return "low";
}

export function scoreLegend() {
  return "Score = sold velocity + rating + early window bonus. Higher is stronger. Early window products get +12 boost.";
}
