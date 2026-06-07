import Heading from "@tiptap/extension-heading";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import MarkdownIt from "markdown-it";
import { useCallback, useEffect, useMemo, useRef, type KeyboardEvent as ReactKeyboardEvent } from "react";
import {
  type ProseMirrorDocument,
  serializePlanMarkdownPreservingUnchangedRegions,
  toProseMirrorDocument,
} from "./planMarkdownRoundTrip.js";

interface PlanEditorProps {
  markdown: string;
  selectedStageId: string | null;
  editable?: boolean;
  onSave?: (markdown: string) => void;
}

const AnchoredHeading = Heading.extend({
  addAttributes() {
    return {
      id: {
        default: null,
      },
      "data-stage-id": {
        default: null,
      },
      "data-testid": {
        default: null,
      },
    };
  },
});

export function PlanEditor({ markdown, selectedStageId, editable = false, onSave }: PlanEditorProps) {
  const htmlContent = useMemo(() => renderPlanMarkdown(markdown), [markdown]);
  const sourceMarkdownRef = useRef(markdown);
  const sourceDocumentRef = useRef<ProseMirrorDocument | null>(null);
  const triggerSave = useCallback(
    (editorDocument: unknown) => {
      if (!editable || onSave === undefined || editorDocument === null) {
        return;
      }

      const currentDocument = toProseMirrorDocument(editorDocument);
      const sourceDocument = sourceDocumentRef.current ?? currentDocument;
      const savedMarkdown = serializePlanMarkdownPreservingUnchangedRegions(
        sourceMarkdownRef.current,
        sourceDocument,
        currentDocument,
      );

      sourceMarkdownRef.current = savedMarkdown;
      sourceDocumentRef.current = currentDocument;
      onSave(savedMarkdown);
    },
    [editable, onSave],
  );

  const editor = useEditor({
    editable,
    extensions: [
      StarterKit.configure({
        heading: false,
      }),
      AnchoredHeading,
    ],
    content: htmlContent,
    editorProps: {
      attributes: {
        class:
          "h-full overflow-auto px-4 py-3 text-micro text-neutral-fg outline-none [&_h1]:mb-3 [&_h1]:text-heading [&_h1]:font-semibold [&_h2]:mb-3 [&_h2]:mt-5 [&_h2]:text-body [&_h2]:font-semibold [&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-micro [&_h3]:font-semibold [&_p]:my-2 [&_ul]:my-2 [&_ul]:pl-5",
      },
    },
  });

  useEffect(() => {
    if (editor === null) {
      return;
    }

    editor.commands.setContent(htmlContent, { emitUpdate: false });
    sourceMarkdownRef.current = markdown;
    sourceDocumentRef.current = toProseMirrorDocument(editor.getJSON());
  }, [editor, htmlContent, markdown]);

  useEffect(() => {
    if (editor === null) {
      return;
    }

    editor.setEditable(editable);
  }, [editor, editable]);

  useEffect(() => {
    if (editor === null || selectedStageId === null) {
      return;
    }

    const stageHeading = editor.view.dom.querySelector(`[data-stage-id="${selectedStageId}"]`);
    if (stageHeading instanceof HTMLElement) {
      stageHeading.scrollIntoView({ block: "start", inline: "nearest" });
    }
  }, [editor, selectedStageId]);

  const handleKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLDivElement>) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        triggerSave(editor?.getJSON() ?? null);
      }
    },
    [editor, triggerSave],
  );

  const handleBlur = useCallback(() => {
    triggerSave(editor?.getJSON() ?? null);
  }, [editor, triggerSave]);

  return (
    <div
      className="h-full overflow-hidden rounded-lg border border-[#1E2530] bg-[#101724]"
      data-testid="project-plan-editor"
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
    >
      <EditorContent className="h-full" editor={editor} />
    </div>
  );
}

const markdownRenderer = new MarkdownIt({
  html: false,
  linkify: true,
});

function renderPlanMarkdown(markdown: string): string {
  const tokens = markdownRenderer.parse(markdown, {});
  const slugCounts = new Map<string, number>();

  for (const [index, token] of tokens.entries()) {
    if (token.type !== "heading_open") {
      continue;
    }

    const level = Number(token.tag.slice(1));
    if (level !== 2 && level !== 3) {
      continue;
    }

    const headingContentToken = tokens[index + 1];
    if (headingContentToken?.type !== "inline") {
      continue;
    }

    const headingText = headingContentToken.content.trim();
    if (headingText.length === 0) {
      continue;
    }

    const stageId = uniqueSlug(headingText, slugCounts);
    token.attrSet("id", stageId);
    token.attrSet("data-stage-id", stageId);
    token.attrSet("data-testid", `plan-heading-${stageId}`);
  }

  return markdownRenderer.renderer.render(tokens, markdownRenderer.options, {});
}

function uniqueSlug(label: string, counts: Map<string, number>): string {
  const base = slugify(label);
  const count = counts.get(base) ?? 0;
  const nextCount = count + 1;
  counts.set(base, nextCount);
  return nextCount === 1 ? base : `${base}-${nextCount}`;
}

function slugify(label: string): string {
  const normalized = label
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  const slug = normalized
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return slug.length > 0 ? slug : "stage";
}
