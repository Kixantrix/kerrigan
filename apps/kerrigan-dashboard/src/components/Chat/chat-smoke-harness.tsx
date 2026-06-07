import React from "react";
import ReactDOM from "react-dom/client";
import { ChatPane } from "./ChatPane.js";
import { AcpClientError, type AcpClient, type AcpEvent } from "../../lib/acp-client.js";

interface ChatFixtureTurn {
  request: string;
  events: AcpEvent[];
}

interface ChatFixture {
  turns: ChatFixtureTurn[];
}

declare global {
  interface Window {
    __KERRIGAN_CHAT_FIXTURE__?: ChatFixture;
  }
}

class FixtureClient implements AcpClient {
  constructor(private readonly fixture: ChatFixture) {}

  sendUserTurn(text: string): AsyncIterable<AcpEvent> {
    const matchingTurn = this.fixture.turns.find((turn) => turn.request === text);
    if (matchingTurn === undefined) {
      return {
        async *[Symbol.asyncIterator](): AsyncIterator<AcpEvent> {
          yield {
            type: "error",
            error: new AcpClientError(
              "fixture-missing-turn",
              `No chat fixture configured for request: ${text}`,
            ),
          };
        },
      };
    }

    return {
      async *[Symbol.asyncIterator](): AsyncIterator<AcpEvent> {
        for (const event of matchingTurn.events) {
          yield event;
        }
      },
    };
  }

  async dispose(): Promise<void> {
    // no-op for fixture client
  }
}

const fixture: ChatFixture =
  window.__KERRIGAN_CHAT_FIXTURE__ ??
  ({
    turns: [
      {
        request: "hello",
        events: [
          { type: "message_chunk", text: "Hi" },
          { type: "turn_end", reason: "done" },
        ],
      },
    ],
  } satisfies ChatFixture);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <div className="h-screen bg-neutral-bg p-5 text-neutral-fg">
      <ChatPane client={new FixtureClient(fixture)} />
    </div>
  </React.StrictMode>,
);
