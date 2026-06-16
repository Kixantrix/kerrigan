// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  AcpClientError,
  AcpDisposedError,
  CopilotCliNotFoundError,
  CopilotCliTooOldError,
  type AcpClient,
  type AcpEvent,
} from "../../lib/acp-client.js";
import { ChatPane } from "./ChatPane.js";

afterEach(() => {
  cleanup();
});

class FakeAcpClient implements AcpClient {
  readonly sendUserTurn = vi.fn((text: string): AsyncIterable<AcpEvent> => {
    const next = this.turns.shift();
    if (next === undefined) {
      throw new AcpClientError("missing-turn", `No fake turn configured for: ${text}`);
    }
    return next(text);
  });

  readonly dispose = vi.fn(async (): Promise<void> => {
    this.disposeHandler?.();
  });

  private disposeHandler: (() => void) | undefined;

  constructor(
    private readonly turns: Array<(text: string) => AsyncIterable<AcpEvent>>,
    disposeHandler?: () => void,
  ) {
    this.disposeHandler = disposeHandler;
  }
}

function streamEvents(events: AcpEvent[]): AsyncIterable<AcpEvent> {
  return {
    async *[Symbol.asyncIterator](): AsyncIterator<AcpEvent> {
      for (const event of events) {
        yield event;
      }
    },
  };
}

describe("ChatPane", () => {
  it("renders each ACP event variant and coalesces message chunks", async () => {
    const fakeClient = new FakeAcpClient([
      () =>
        streamEvents([
          { type: "message_chunk", text: "Hello " },
          { type: "message_chunk", text: "world" },
          { type: "thought", text: "planning" },
          { type: "tool_call", name: "search", input: { query: "q" } },
          { type: "tool_result", name: "search", output: { ok: true } },
          { type: "turn_end", reason: "done" },
          { type: "error", error: new AcpClientError("offline", "Offline. Retry when connected.") },
        ]),
    ]);

    render(<ChatPane client={fakeClient} />);

    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByTestId("chat-submit"));

    expect(await screen.findByTestId("chat-event-message-chunk")).toHaveTextContent("Hello world");
    expect(screen.getByTestId("chat-event-thought")).toHaveTextContent("planning");
    expect(screen.getByTestId("chat-event-tool-call-name")).toHaveTextContent("search");
    expect(screen.getByTestId("chat-event-tool-result-name")).toHaveTextContent("search");
    expect(screen.getByTestId("chat-event-turn-end")).toHaveTextContent("Turn complete: done");
    expect(screen.getByTestId("chat-event-error")).toHaveTextContent("Offline. Retry when connected.");
    expect(screen.getByTestId("chat-error-banner")).toHaveTextContent("Offline. Retry when connected.");
  });

  it("shows actionable banner for missing CLI", async () => {
    const fakeClient = new FakeAcpClient([
      () => {
        throw new CopilotCliNotFoundError();
      },
    ]);

    render(<ChatPane client={fakeClient} />);

    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByTestId("chat-submit"));

    expect(await screen.findByTestId("chat-error-banner")).toHaveTextContent(
      "Copilot CLI not found",
    );
  });

  it("shows actionable banner for too-old CLI", async () => {
    const fakeClient = new FakeAcpClient([
      () => {
        throw new CopilotCliTooOldError();
      },
    ]);

    render(<ChatPane client={fakeClient} />);

    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByTestId("chat-submit"));

    expect(await screen.findByTestId("chat-error-banner")).toHaveTextContent(
      "Copilot CLI v1.0+ required for ACP",
    );
  });

  it("cancels an in-flight turn and re-enables submit", async () => {
    let allowDispose: (() => void) | undefined;

    const fakeClient = new FakeAcpClient(
      [
        () => ({
          async *[Symbol.asyncIterator](): AsyncIterator<AcpEvent> {
            yield { type: "message_chunk", text: "partial" };
            await new Promise<void>((resolve) => {
              allowDispose = resolve;
            });
            throw new AcpDisposedError();
          },
        }),
      ],
      () => {
        allowDispose?.();
      },
    );

    render(<ChatPane client={fakeClient} />);

    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "stream" } });
    fireEvent.click(screen.getByTestId("chat-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("chat-submit")).toBeDisabled();
    });

    fireEvent.click(screen.getByTestId("chat-cancel"));

    await waitFor(() => {
      expect(screen.getByTestId("chat-submit")).not.toBeDisabled();
    });

    expect(fakeClient.dispose).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("chat-error-banner")).toBeNull();
  });

  it("renders startup errors from the runtime wiring", () => {
    const fakeClient = new FakeAcpClient([() => streamEvents([{ type: "turn_end", reason: "done" }])]);
    render(<ChatPane client={fakeClient} startupError="Kerrigan MCP server failed to start." />);
    expect(screen.getByTestId("chat-error-banner")).toHaveTextContent(
      "Kerrigan MCP server failed to start.",
    );
  });
});
