// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { AcpClient, AcpEvent, AdditionalMcpConfig } from "../../lib/acp-client.js";
import type { McpSidecar, McpToolResultEvent } from "../../lib/mcp-sidecar.js";
import { ProjectView } from "./ProjectView.js";

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
  }
}

class FakeSidecar implements McpSidecar {
  private readonly listeners = new Set<(event: McpToolResultEvent) => void>();

  constructor(
    private readonly startupError: Error | null = null,
    private readonly config: AdditionalMcpConfig = {
      mcpServers: {
        kerrigan: { command: "node", args: ["tools/kerrigan-mcp/dist/server.js"] },
      },
    },
  ) {}

  async start(): Promise<void> {
    if (this.startupError !== null) throw this.startupError;
  }

  async stop(): Promise<void> {}

  getAdditionalMcpConfig(): AdditionalMcpConfig {
    return this.config;
  }

  onToolResult(listener: (event: McpToolResultEvent) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  emitToolResult(event: McpToolResultEvent): void {
    for (const listener of this.listeners) listener(event);
  }
}

class FakeAcpClient implements AcpClient {
  constructor(private readonly streamFactory: (message: string) => AsyncIterable<AcpEvent>) {}

  sendUserTurn(text: string): AsyncIterable<AcpEvent> {
    return this.streamFactory(text);
  }

  async dispose(): Promise<void> {}
}

function streamEvents(events: AcpEvent[]): AsyncIterable<AcpEvent> {
  return {
    async *[Symbol.asyncIterator](): AsyncIterator<AcpEvent> {
      for (const event of events) yield event;
    },
  };
}

function renderProjectView(props: {
  planReader?: (workingCopyPath: string) => Promise<string | null>;
  createSidecar?: () => McpSidecar;
  createChatClient?: (additionalMcpConfig: AdditionalMcpConfig) => AcpClient;
} = {}): void {
  render(
    <MemoryRouter initialEntries={["/project/kerrigan-dashboard"]}>
      <Routes>
        <Route path="/project/:projectId" element={<ProjectView {...props} blocksReader={async () => []} />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  delete window.__KERRIGAN_PROJECTS_FIXTURE__;
});

describe("ProjectView chat cockpit wiring", () => {
  it("mounts chat pane and streams one response", async () => {
    window.__KERRIGAN_PROJECTS_FIXTURE__ = [
      {
        id: "kerrigan-dashboard",
        name: "Kerrigan Dashboard",
        repos: [{ owner: "Kixantrix", repo: "kerrigan" }],
        workingCopyPaths: ["/workspace/kerrigan-dashboard"],
      },
    ];

    const sidecar = new FakeSidecar();
    const createChatClient = vi.fn(() => {
      return new FakeAcpClient(() =>
        streamEvents([
          { type: "message_chunk", text: "Hi from Copilot" },
          { type: "turn_end", reason: "done" },
        ]),
      );
    });

    renderProjectView({
      planReader: async () => "## M1\n### M1.1",
      createSidecar: () => sidecar,
      createChatClient,
    });

    await screen.findByTestId("chat-pane");
    fireEvent.change(screen.getByTestId("chat-input"), { target: { value: "hello" } });
    fireEvent.click(screen.getByTestId("chat-submit"));

    expect(await screen.findByTestId("chat-event-message-chunk")).toHaveTextContent("Hi from Copilot");
    expect(createChatClient).toHaveBeenCalledTimes(1);
  });

  it("refreshes project status when the sidecar emits tool-result events", async () => {
    window.__KERRIGAN_PROJECTS_FIXTURE__ = [
      {
        id: "kerrigan-dashboard",
        name: "Kerrigan Dashboard",
        repos: [{ owner: "Kixantrix", repo: "kerrigan" }],
        workingCopyPaths: ["/workspace/kerrigan-dashboard"],
      },
    ];

    const sidecar = new FakeSidecar();
    const planReader = vi.fn(async () => "## M2\n### M2.1");

    renderProjectView({
      planReader,
      createSidecar: () => sidecar,
      createChatClient: () => new FakeAcpClient(() => streamEvents([{ type: "turn_end", reason: "done" }])),
    });

    await screen.findByTestId("project-dag");
    expect(planReader).toHaveBeenCalledTimes(1);

    sidecar.emitToolResult({
      tool: "kerrigan.plan-update",
      result: { ok: true },
      affectedProjectId: "kerrigan-dashboard",
    });

    await waitFor(() => {
      expect(planReader).toHaveBeenCalledTimes(2);
    });
  });

  it("shows sidecar startup failures in chat while keeping the project view usable", async () => {
    window.__KERRIGAN_PROJECTS_FIXTURE__ = [
      {
        id: "kerrigan-dashboard",
        name: "Kerrigan Dashboard",
        repos: [{ owner: "Kixantrix", repo: "kerrigan" }],
        workingCopyPaths: ["/workspace/kerrigan-dashboard"],
      },
    ];

    renderProjectView({
      planReader: async () => "## M3\n### M3.1",
      createSidecar: () => new FakeSidecar(new Error("Kerrigan MCP server failed to start.")),
      createChatClient: () => new FakeAcpClient(() => streamEvents([{ type: "turn_end", reason: "done" }])),
    });

    await screen.findByTestId("project-dag");
    expect(screen.getByTestId("project-plan-editor")).toBeVisible();
    expect(await screen.findByTestId("chat-error-banner")).toHaveTextContent(
      "Kerrigan MCP server failed to start.",
    );
  });
});
