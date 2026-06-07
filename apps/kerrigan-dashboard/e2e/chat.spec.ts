import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.__KERRIGAN_CHAT_FIXTURE__ = {
      turns: [
        {
          request: "hello",
          events: [
            { type: "message_chunk", text: "Hi " },
            { type: "message_chunk", text: "there" },
            { type: "tool_call", name: "search", input: { q: "status" } },
            { type: "tool_result", name: "search", output: { ok: true } },
            { type: "turn_end", reason: "done" },
          ],
        },
      ],
    };
  });
});

test("chat-smoke-exchange", async ({ page }) => {
  await page.goto("/chat-smoke.html");

  await page.getByTestId("chat-input").fill("hello");
  await page.getByTestId("chat-submit").click();

  await expect(page.getByTestId("chat-user-turn")).toContainText("hello");
  await expect(page.getByTestId("chat-event-message-chunk")).toContainText("Hi there");
  await expect(page.getByTestId("chat-event-tool-call-name")).toContainText("search");
  await expect(page.getByTestId("chat-event-tool-result-name")).toContainText("search");
  await expect(page.getByTestId("chat-event-turn-end")).toContainText("Turn complete: done");
});

declare global {
  interface Window {
    __KERRIGAN_CHAT_FIXTURE__?: {
      turns: Array<{
        request: string;
        events: unknown[];
      }>;
    };
  }
}
