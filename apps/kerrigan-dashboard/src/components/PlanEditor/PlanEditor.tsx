import Heading from "@tiptap/extension-heading";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import MarkdownIt from "markdown-it";
import { useCallback, useEffect, useMemo, useRef, type KeyboardEvent as ReactKeyboardEvent } from "react";

interface PlanEditorProps {
  markdown: string;
  selectedStageId: string | null;
  editable?: boolean;
  onSave?: (markdown: string) => void;
}

interface ProseMirrorMark {
  type: string;
  attrs?: Record<string, string | number | boolean | null | undefined>;
}

interface ProseMirrorNode {
  type: string;
  attrs?: Record<string, string | number | boolean | null | undefined>;
  marks?: ProseMirrorMark[];
  text?: string;
  content?: ProseMirrorNode[];
}

interface ProseMirrorDocument {
  type: "doc";
  content: ProseMirrorNode[];
}

interface MarkdownBlock {
  startOffset: number;
  endOffset: number;
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
  }, [editor, htmlContent]);

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

function toProseMirrorDocument(document: unknown): ProseMirrorDocument {
  if (
    typeof document !== "object" ||
    document === null ||
    !("type" in document) ||
    document.type !== "doc" ||
    !("content" in document) ||
    !Array.isArray(document.content)
  ) {
    return { type: "doc", content: [] };
  }

  return document as ProseMirrorDocument;
}

export function serializePlanMarkdownPreservingUnchangedRegions(
  sourceMarkdown: string,
  sourceDocument: ProseMirrorDocument,
  currentDocument: ProseMirrorDocument,
): string {
  if (JSON.stringify(sourceDocument) === JSON.stringify(currentDocument)) {
    return sourceMarkdown;
  }

  const sourceBlocks = extractTopLevelBlocks(sourceMarkdown);
  const sourceNodes = sourceDocument.content;
  const currentNodes = currentDocument.content;

  if (
    sourceBlocks.length === 0 ||
    sourceNodes.length !== currentNodes.length ||
    sourceBlocks.length !== sourceNodes.length
  ) {
    return serializeDocument(currentDocument);
  }

  let output = "";
  let cursor = 0;

  for (const [index, sourceBlock] of sourceBlocks.entries()) {
    const sourceBlockMarkdown = sourceMarkdown.slice(sourceBlock.startOffset, sourceBlock.endOffset);
    output += sourceMarkdown.slice(cursor, sourceBlock.startOffset);
    if (nodesAreEqual(sourceNodes[index], currentNodes[index])) {
      output += sourceBlockMarkdown;
    } else {
      let serializedNode = serializeNode(currentNodes[index]);
      if (sourceBlockMarkdown.endsWith("\n") && !serializedNode.endsWith("\n")) {
        serializedNode += "\n";
      }
      output += serializedNode;
    }
    cursor = sourceBlock.endOffset;
  }

  output += sourceMarkdown.slice(cursor);
  return output;
}

function extractTopLevelBlocks(markdown: string): MarkdownBlock[] {
  const lineOffsets = buildLineOffsets(markdown);
  const tokens = markdownRenderer.parse(markdown, {});
  const blocks: MarkdownBlock[] = [];

  for (const token of tokens) {
    if (token.level !== 0 || token.map === null || token.map === undefined) {
      continue;
    }

    if (token.nesting !== 1 && token.nesting !== 0) {
      continue;
    }

    const [startLine, endLine] = token.map;
    blocks.push({
      startOffset: lineOffsets[startLine] ?? 0,
      endOffset: lineOffsets[endLine] ?? markdown.length,
    });
  }

  const deduped: MarkdownBlock[] = [];
  let lastEndOffset = -1;
  for (const block of blocks) {
    if (block.startOffset < lastEndOffset) {
      continue;
    }

    deduped.push(block);
    lastEndOffset = block.endOffset;
  }

  return deduped;
}

function buildLineOffsets(markdown: string): number[] {
  const offsets: number[] = [0];
  for (let index = 0; index < markdown.length; index += 1) {
    if (markdown[index] === "\n") {
      offsets.push(index + 1);
    }
  }

  offsets.push(markdown.length);
  return offsets;
}

function nodesAreEqual(left: ProseMirrorNode, right: ProseMirrorNode): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function serializeDocument(document: ProseMirrorDocument): string {
  return document.content.map((node) => serializeNode(node)).join("\n\n");
}

function serializeNode(node: ProseMirrorNode): string {
  switch (node.type) {
    case "heading": {
      const headingLevel = Number(node.attrs?.level ?? 1);
      return `${"#".repeat(Math.max(1, headingLevel))} ${serializeInlineContent(node).trim()}`;
    }
    case "paragraph":
      return serializeInlineContent(node);
    case "bulletList":
      return serializeList(node, 0);
    case "orderedList":
      return serializeList(node, Number(node.attrs?.start ?? 1));
    case "blockquote":
      return serializeInlineContent(node)
        .split("\n")
        .map((line) => `> ${line}`)
        .join("\n");
    case "codeBlock": {
      const language = typeof node.attrs?.language === "string" ? node.attrs.language : "";
      const content = serializeInlineContent(node);
      return `\`\`\`${language}\n${content}\n\`\`\``;
    }
    case "horizontalRule":
      return "---";
    default:
      return serializeInlineContent(node);
  }
}

function serializeList(node: ProseMirrorNode, start: number): string {
  const items = (node.content ?? []).filter((child) => child.type === "listItem");
  return items
    .map((item, index) => serializeListItem(item, node.type === "orderedList" ? `${start + index}.` : "-"))
    .join("\n");
}

function serializeListItem(item: ProseMirrorNode, marker: string): string {
  const itemContent = item.content ?? [];
  if (itemContent.length === 0) {
    return `${marker} `;
  }

  const renderedChildren = itemContent.map((child) => serializeNode(child));
  const [firstChild, ...restChildren] = renderedChildren;
  const lines = firstChild.split("\n");
  const firstLine = `${marker} ${lines[0]}`;
  const remainingFirstChildLines = lines.slice(1).map((line) => `  ${line}`);
  const restLines = restChildren.flatMap((child) => child.split("\n").map((line) => `  ${line}`));

  return [firstLine, ...remainingFirstChildLines, ...restLines].join("\n");
}

function serializeInlineContent(node: ProseMirrorNode): string {
  return (node.content ?? [])
    .map((child) => {
      if (child.type === "hardBreak") {
        return "  \n";
      }

      if (child.type === "text") {
        return applyMarks(child.text ?? "", child.marks ?? []);
      }

      return serializeInlineContent(child);
    })
    .join("");
}

function applyMarks(text: string, marks: ProseMirrorMark[]): string {
  const sortedMarks = [...marks].sort((left, right) => markOrder(left.type) - markOrder(right.type));
  let value = text;

  for (const mark of sortedMarks) {
    switch (mark.type) {
      case "code":
        value = `\`${value.replace(/`/g, "\\`")}\``;
        break;
      case "bold":
        value = `**${value}**`;
        break;
      case "italic":
        value = `*${value}*`;
        break;
      case "strike":
        value = `~~${value}~~`;
        break;
      case "link": {
        const href = typeof mark.attrs?.href === "string" ? mark.attrs.href : "";
        value = `[${value}](${href})`;
        break;
      }
      default:
        break;
    }
  }

  return value;
}

function markOrder(markType: string): number {
  switch (markType) {
    case "code":
      return 1;
    case "bold":
      return 2;
    case "italic":
      return 3;
    case "strike":
      return 4;
    case "link":
      return 5;
    default:
      return 6;
  }
}
