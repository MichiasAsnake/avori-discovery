import type { DiscoveryJob } from "@/types/avori";

type PollOptions = {
  intervalMs?: number;
  timeoutMs?: number;
};

export async function pollDiscoveryJob(
  fetchJob: () => Promise<DiscoveryJob>,
  options: PollOptions = {},
) {
  const intervalMs = options.intervalMs ?? 1500;
  const timeoutMs = options.timeoutMs ?? 45_000;
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const job = await fetchJob();
    if (job.status === "completed" || job.status === "failed") {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Timed out while waiting for discovery job");
}
