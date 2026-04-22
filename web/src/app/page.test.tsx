import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardShell } from "@/components/dashboard-shell";

const products = [
  {
    product_id: "p1",
    title: "Travel Hanging Toiletry Organizer",
    price: 29.99,
    sold_count: 2400,
    review_count: 18,
    score: 88.08,
    early_window: true,
    seller_name: "Avori Demo Shop",
    image_url: "https://example.com/p1.jpg",
    discovered_keywords: ["travel organizer"],
    review_summary: { review_count: 18, average_rating: 4.8 },
    supplementary_signals: { shop_follower_count: 1200 },
  },
];

describe("DashboardShell", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:avori"),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders onboarding empty state when there are no products", () => {
    render(<DashboardShell initialCandidates={[]} initialWatchlist={[]} />);

    expect(screen.getByText("Get started")).toBeInTheDocument();
    expect(
      screen.getByText(/pull today's TikTok Shop candidates/i),
    ).toBeInTheDocument();
  });

  it("renders candidates and watchlist tabs with score help and csv export", () => {
    render(<DashboardShell initialCandidates={products} initialWatchlist={[]} />);

    expect(screen.getByRole("tab", { name: "Candidates" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Watchlist" })).toBeInTheDocument();
    expect(screen.getByText(/Early window products get \+12 boost/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export CSV/i })).toBeInTheDocument();
  });

  it("shows the product image and visible review summary in the detail panel", () => {
    render(<DashboardShell initialCandidates={products} initialWatchlist={[]} />);

    expect(screen.getByRole("img", { name: "Travel Hanging Toiletry Organizer" })).toBeInTheDocument();
    expect(screen.getByText("Review summary")).toBeInTheDocument();
    expect(screen.getByText("Average Rating")).toBeInTheDocument();
  });

  it("runs discovery through the async job endpoints", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ job_id: "job-1", status: "queued" }), { status: 202 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            job_id: "job-1",
            status: "completed",
            payload: { products },
          }),
          { status: 200 },
        ),
      );

    render(<DashboardShell initialCandidates={[]} initialWatchlist={[]} />);

    fireEvent.click(screen.getAllByRole("button", { name: "Run Discovery" })[0]);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/discovery/run", { method: "POST" });
    });
    await waitFor(() => {
      expect(screen.getAllByText("Travel Hanging Toiletry Organizer")).toHaveLength(2);
    });
  });

  it("sends discuss-in-chat prompts as natural language and renders the reply", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ reply: "Strong travel category fit", session_id: "session-1" }), {
        status: 200,
      }),
    );

    render(<DashboardShell initialCandidates={products} initialWatchlist={[]} />);

    fireEvent.click(screen.getByRole("button", { name: "Discuss in Chat" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/chat", expect.any(Object));
    });
    await waitFor(() => {
      expect(screen.getByText("Strong travel category fit")).toBeInTheDocument();
    });
    expect(screen.getByText(/Can you assess Travel Hanging Toiletry Organizer as an Avori candidate/i)).toBeInTheDocument();
  });

  it("searches products from the sidebar", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ products }), { status: 200 }),
    );

    render(<DashboardShell initialCandidates={[]} initialWatchlist={[]} />);

    fireEvent.change(screen.getByLabelText("Keyword Search"), {
      target: { value: "travel organizer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search Keyword" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/products/search?keyword=travel%20organizer",
      );
    });
    expect(screen.getAllByText("Travel Hanging Toiletry Organizer")).toHaveLength(2);
  });

  it("saves a candidate to the watchlist and renders it in the watchlist tab", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: "saved",
          entry: {
            product_id: "p1",
            title: "Travel Hanging Toiletry Organizer",
            reason: "Early window candidate from Avori discovery.",
            added_at: "2026-04-22",
            track: true,
            graduated: false,
            velocity: null,
            snapshots_count: 1,
          },
        }),
        { status: 200 },
      ),
    );

    render(<DashboardShell initialCandidates={products} initialWatchlist={[]} />);

    fireEvent.click(screen.getByRole("button", { name: "Save To Watchlist" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/watchlist", expect.any(Object));
    });

    fireEvent.click(screen.getByRole("tab", { name: "Watchlist" }));

    expect(screen.getByText("Early window candidate from Avori discovery.")).toBeInTheDocument();
  });

  it("loads product detail when a candidate row is selected", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          product_id: "p1",
          category_names: ["Travel Storage"],
          review_summary: { review_count: 18, average_rating: 4.8 },
          supplementary_signals: { shop_follower_count: 1200 },
        }),
        { status: 200 },
      ),
    );

    render(<DashboardShell initialCandidates={products} initialWatchlist={[]} />);

    fireEvent.click(screen.getAllByRole("button", { name: "Travel Hanging Toiletry Organizer" })[0]);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/products/p1");
    });
    expect(screen.getByText("Travel Storage")).toBeInTheDocument();
  });
});
