// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PlanEditor } from "./PlanEditor.js";
import {
  type ProseMirrorDocument,
  serializePlanMarkdownPreservingUnchangedRegions,
} from "./planMarkdownRoundTrip.js";

afterEach(() => {
  cleanup();
});

describe("PlanEditor", () => {
  it("renders markdown headings with stable stage anchors", async () => {
    render(<PlanEditor markdown={"## Build API\n\n### Compile"} selectedStageId={null} />);

    expect(await screen.findByTestId("plan-heading-build-api")).toHaveTextContent("Build API");
    expect(await screen.findByTestId("plan-heading-compile")).toHaveTextContent("Compile");
  });

  it("scrolls to the selected stage heading", async () => {
    const scrolledStageIds: string[] = [];
    const scrollIntoViewMock = vi.fn(function thisBound(this: HTMLElement) {
      scrolledStageIds.push(this.dataset.stageId ?? "");
    });

    const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
    try {
      const { rerender } = render(
        <PlanEditor markdown={"## Build\n\n## Ship"} selectedStageId={null} />,
      );
      rerender(<PlanEditor markdown={"## Build\n\n## Ship"} selectedStageId="ship" />);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
      expect(scrolledStageIds).toContain("ship");
    } finally {
      HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
    }
  });

  it("saves markdown on Ctrl+S and blur in editable mode", async () => {
    const onSave = vi.fn();
    const markdown = "## Build API\n\nKeep this block.";
    render(<PlanEditor editable markdown={markdown} onSave={onSave} selectedStageId={null} />);

    const editorRoot = screen.getByTestId("project-plan-editor");
    const editableSurface = editorRoot.querySelector("[contenteditable='true']");
    expect(editableSurface).not.toBeNull();

    fireEvent.keyDown(editableSurface as HTMLElement, { ctrlKey: true, key: "s" });
    fireEvent.blur(editableSurface as HTMLElement);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(2);
    });
    expect(onSave).toHaveBeenNthCalledWith(1, markdown);
    expect(onSave).toHaveBeenNthCalledWith(2, markdown);
  });

  it("round-trips unedited markdown byte-for-byte across a corpus", async () => {
    const corpus = [
      "## Build\n\n### Compile\n\nParagraph with *emphasis*.",
      "---\ndependencies:\n  ship: [build]\n---\n\n## Build\n\n- Compile\n- Package\n",
      "## Déploy / 🚀\n\nText with `code` and [link](https://example.com).",
    ];

    for (const markdown of corpus) {
      const onSave = vi.fn();
      const { unmount } = render(
        <PlanEditor editable markdown={markdown} onSave={onSave} selectedStageId={null} />,
      );
      const editorRoot = screen.getByTestId("project-plan-editor");
      const editableSurface = editorRoot.querySelector("[contenteditable='true']");
      fireEvent.keyDown(editableSurface as HTMLElement, { metaKey: true, key: "s" });

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledTimes(1);
      });
      expect(onSave).toHaveBeenCalledWith(markdown);
      unmount();
    }
  });

  it("preserves unchanged regions when serializing an edited block", () => {
    const sourceMarkdown = "## Build\n\nAlpha    spacing\n\n## Test\n\nBeta\n";
    const sourceDocument: ProseMirrorDocument = {
      type: "doc",
      content: [
        { type: "heading", attrs: { level: 2 }, content: [{ type: "text", text: "Build" }] },
        { type: "paragraph", content: [{ type: "text", text: "Alpha spacing" }] },
        { type: "heading", attrs: { level: 2 }, content: [{ type: "text", text: "Test" }] },
        { type: "paragraph", content: [{ type: "text", text: "Beta" }] },
      ],
    };

    const editedDocument = {
      ...sourceDocument,
      content: sourceDocument.content.map((node, index) =>
        index === 1 ? { type: "paragraph", content: [{ type: "text", text: "Gamma" }] } : node,
      ),
    };

    const result = serializePlanMarkdownPreservingUnchangedRegions(
      sourceMarkdown,
      sourceDocument,
      editedDocument,
    );

    expect(result).toBe("## Build\n\nGamma\n\n## Test\n\nBeta\n");
  });

  it("still scrolls to selected stage in editable mode", async () => {
    const scrollIntoViewMock = vi.fn();
    const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
    try {
      const onSave = vi.fn();
      const { rerender } = render(
        <PlanEditor editable markdown={"## Build\n\n## Ship"} onSave={onSave} selectedStageId={null} />,
      );
      rerender(<PlanEditor editable markdown={"## Build\n\n## Ship"} onSave={onSave} selectedStageId="ship" />);

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled();
      });
    } finally {
      HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
    }
  });
});
