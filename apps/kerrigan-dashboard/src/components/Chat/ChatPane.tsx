import { type FormEvent, type ReactElement, useEffect, useMemo, useRef, useState } from "react";
import {
  AcpClientError,
  AcpDisposedError,
  createAcpClient,
  type AcpClient,
  type AcpEvent,
} from "../../lib/acp-client.js";

interface ChatPaneProps {
  client?: AcpClient;
  createClient?: () => AcpClient;
  startupError?: string | null;
}

type TranscriptEntry =
  | {
      id: number;
      type: "user";
      text: string;
    }
  | {
      id: number;
      type: "event";
      event: AcpEvent;
    };

function UserTurn({ text }: { text: string }) {
  return (
    <div className="self-end rounded border border-brand/40 bg-brand/10 px-3 py-2 text-body text-neutral-fg" data-testid="chat-user-turn">
      {text}
    </div>
  );
}

function MessageChunkEvent({ text }: { text: string }) {
  return (
    <div className="rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-body text-neutral-fg" data-testid="chat-event-message-chunk">
      {text}
    </div>
  );
}

function ToolCallEvent({ name, input }: { name: string; input: unknown }) {
  return (
    <div className="rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-micro text-neutral-soft" data-testid="chat-event-tool-call">
      <p className="text-nano uppercase tracking-wide text-neutral-muted">Tool call</p>
      <p data-testid="chat-event-tool-call-name">{name}</p>
      <pre className="mt-1 overflow-x-auto text-nano whitespace-pre-wrap text-neutral-muted" data-testid="chat-event-tool-call-input">
        {safeJson(input)}
      </pre>
    </div>
  );
}

function ToolResultEvent({ name, output }: { name: string; output: unknown }) {
  return (
    <div className="rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-micro text-neutral-soft" data-testid="chat-event-tool-result">
      <p className="text-nano uppercase tracking-wide text-neutral-muted">Tool result</p>
      <p data-testid="chat-event-tool-result-name">{name}</p>
      <pre className="mt-1 overflow-x-auto text-nano whitespace-pre-wrap text-neutral-muted" data-testid="chat-event-tool-result-output">
        {safeJson(output)}
      </pre>
    </div>
  );
}

function ThoughtEvent({ text }: { text: string }) {
  return (
    <div className="rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-micro text-neutral-soft" data-testid="chat-event-thought">
      <p className="text-nano uppercase tracking-wide text-neutral-muted">Thought</p>
      <p>{text}</p>
    </div>
  );
}

function TurnEndEvent({ reason }: { reason?: string }) {
  return (
    <div className="rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-nano text-neutral-muted" data-testid="chat-event-turn-end">
      Turn complete{reason !== undefined ? `: ${reason}` : ""}
    </div>
  );
}

function ErrorEvent({ error }: { error: AcpClientError }) {
  return (
    <div className="rounded border border-accent/40 bg-accent/10 px-3 py-2 text-micro text-accent" data-testid="chat-event-error">
      {error.message}
    </div>
  );
}

function renderAcpEvent(event: AcpEvent): ReactElement {
  switch (event.type) {
    case "message_chunk":
      return <MessageChunkEvent text={event.text} />;
    case "tool_call":
      return <ToolCallEvent name={event.name} input={event.input} />;
    case "tool_result":
      return <ToolResultEvent name={event.name} output={event.output} />;
    case "thought":
      return <ThoughtEvent text={event.text} />;
    case "turn_end":
      return event.reason === undefined ? <TurnEndEvent /> : <TurnEndEvent reason={event.reason} />;
    case "error":
      return <ErrorEvent error={event.error} />;
  }
}

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function coalesceMessageChunk(entries: TranscriptEntry[], chunk: AcpEvent): TranscriptEntry[] {
  if (chunk.type !== "message_chunk") {
    return [...entries, { id: nextEntryId(entries), type: "event", event: chunk }];
  }

  const lastEntry = entries[entries.length - 1];
  if (lastEntry?.type === "event" && lastEntry.event.type === "message_chunk") {
    const merged: TranscriptEntry = {
      ...lastEntry,
      event: {
        type: "message_chunk",
        text: `${lastEntry.event.text}${chunk.text}`,
      },
    };
    return [...entries.slice(0, -1), merged];
  }

  return [...entries, { id: nextEntryId(entries), type: "event", event: chunk }];
}

function nextEntryId(entries: TranscriptEntry[]): number {
  const lastId = entries.length > 0 ? entries[entries.length - 1]?.id : undefined;
  return typeof lastId === "number" ? lastId + 1 : 1;
}

function toBannerMessage(error: unknown): string {
  if (error instanceof AcpClientError) {
    return error.message;
  }
  return "Chat failed unexpectedly. Restart chat and try again.";
}

export function ChatPane({
  client: injectedClient,
  createClient = createAcpClient,
  startupError = null,
}: ChatPaneProps) {
  const [ownedClient, setOwnedClient] = useState<AcpClient>(() => createClient());
  const client = useMemo(() => injectedClient ?? ownedClient, [injectedClient, ownedClient]);
  const [draft, setDraft] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const turnIdRef = useRef(0);
  const cancelRequestedRef = useRef(false);
  const activeErrorBanner = errorBanner ?? startupError;

  useEffect(() => {
    return () => {
      if (injectedClient === undefined) {
        void ownedClient.dispose();
      }
    };
  }, [injectedClient, ownedClient]);

  const resetOwnedClient = (): void => {
    if (injectedClient !== undefined) return;
    const previousClient = ownedClient;
    setOwnedClient(createClient());
    void previousClient.dispose();
  };

  const submitTurn = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (isStreaming) return;

    const text = draft.trim();
    if (text.length === 0) return;

    cancelRequestedRef.current = false;
    setDraft("");
    setErrorBanner(null);
    setIsStreaming(true);
    setTranscript((previous) => [...previous, { id: nextEntryId(previous), type: "user", text }]);

    const currentTurnId = turnIdRef.current + 1;
    turnIdRef.current = currentTurnId;

    let stream: AsyncIterable<AcpEvent>;
    try {
      stream = client.sendUserTurn(text);
    } catch (error) {
      setErrorBanner(toBannerMessage(error));
      setIsStreaming(false);
      return;
    }

    void (async () => {
      try {
        for await (const eventChunk of stream) {
          setTranscript((previous) => coalesceMessageChunk(previous, eventChunk));
          if (eventChunk.type === "error") {
            setErrorBanner(eventChunk.error.message);
          }
        }
      } catch (error) {
        if (cancelRequestedRef.current && error instanceof AcpDisposedError) {
          return;
        }
        setErrorBanner(toBannerMessage(error));
      } finally {
        if (turnIdRef.current === currentTurnId) {
          setIsStreaming(false);
        }
      }
    })();
  };

  const cancelTurn = (): void => {
    if (!isStreaming) return;
    cancelRequestedRef.current = true;
    setIsStreaming(false);

    if (injectedClient === undefined) {
      resetOwnedClient();
      return;
    }

    void injectedClient.dispose();
  };

  return (
    <section className="flex h-full min-h-0 flex-col rounded-lg border border-neutral-border bg-neutral-bg p-4" data-testid="chat-pane">
      <header className="mb-3">
        <h2 className="text-heading font-semibold text-neutral-fg">Chat</h2>
        <p className="text-micro text-neutral-muted">ACP event stream</p>
      </header>

      {activeErrorBanner !== null ? (
        <aside className="mb-3 rounded border border-accent/40 bg-accent/10 p-2 text-micro text-accent" data-testid="chat-error-banner">
          {activeErrorBanner}
        </aside>
      ) : null}

      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto" data-testid="chat-transcript">
        {transcript.map((entry) =>
          entry.type === "user" ? (
            <UserTurn key={entry.id} text={entry.text} />
          ) : (
            <div key={entry.id}>{renderAcpEvent(entry.event)}</div>
          ),
        )}
      </div>

      <form className="mt-3 flex gap-2" onSubmit={submitTurn}>
        <input
          className="min-w-0 flex-1 rounded border border-neutral-border-strong bg-neutral-surface px-3 py-2 text-body text-neutral-fg outline-none transition-colors duration-200 ease-[cubic-bezier(0.2,0,0,1)] focus:border-brand"
          data-testid="chat-input"
          onChange={(changeEvent) => {
            setDraft(changeEvent.target.value);
          }}
          placeholder="Ask Copilot"
          value={draft}
        />
        <button
          className="rounded border border-brand/50 px-3 py-2 text-micro text-brand transition-colors duration-200 ease-[cubic-bezier(0.2,0,0,1)] disabled:cursor-not-allowed disabled:opacity-60"
          data-testid="chat-submit"
          disabled={isStreaming}
          type="submit"
        >
          Send
        </button>
        <button
          className="rounded border border-neutral-border-strong px-3 py-2 text-micro text-neutral-soft transition-colors duration-200 ease-[cubic-bezier(0.2,0,0,1)] disabled:cursor-not-allowed disabled:opacity-60"
          data-testid="chat-cancel"
          disabled={!isStreaming}
          onClick={cancelTurn}
          type="button"
        >
          Cancel
        </button>
      </form>
    </section>
  );
}
