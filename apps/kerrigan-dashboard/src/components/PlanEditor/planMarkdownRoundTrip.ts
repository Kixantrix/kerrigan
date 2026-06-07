import MarkdownIt from "markdown-it";

export interface ProseMirrorMark {
  type: string;
  attrs?: Record<string, string | number | boolean | null | undefined>;
}

export interface ProseMirrorNode {
  type: string;
  attrs?: Record<string, string | number | boolean | null | undefined>;
  marks?: ProseMirrorMark[];
  text?: string;
  content?: ProseMirrorNode[];
}

export interface ProseMirrorDocument {
  type: "doc";
  content: ProseMirrorNode[];
}

interface MarkdownBlock {
  startOffset: number;
  endOffset: number;
}

const markdownRenderer = new MarkdownIt({
  html: false,
  linkify: true,
});

export function toProseMirrorDocument(document: unknown): ProseMirrorDocument {
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

  for (let index = 0; index < sourceBlocks.length; index += 1) {
    const sourceBlock = sourceBlocks[index];
    const sourceNode = sourceNodes[index];
    const currentNode = currentNodes[index];
    if (sourceBlock === undefined || sourceNode === undefined || currentNode === undefined) {
      return serializeDocument(currentDocument);
    }

    const sourceBlockMarkdown = sourceMarkdown.slice(sourceBlock.startOffset, sourceBlock.endOffset);
    output += sourceMarkdown.slice(cursor, sourceBlock.startOffset);
    if (nodesAreEqual(sourceNode, currentNode)) {
      output += sourceBlockMarkdown;
    } else {
      let serializedNode = serializeNode(currentNode);
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
  const firstChild = renderedChildren[0] ?? "";
  const restChildren = renderedChildren.slice(1);
  const lines = firstChild.split("\n");
  const firstLine = `${marker} ${lines[0] ?? ""}`;
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
      case "code": {
        value = `\`${escapeInlineCodeContent(value)}\``;
        break;
      }
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

function escapeInlineCodeContent(value: string): string {
  let escaped = "";
  for (const character of value) {
    if (character === "\\") {
      escaped += "\\\\";
      continue;
    }

    if (character === "`") {
      escaped += "\\`";
      continue;
    }

    escaped += character;
  }

  return escaped;
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
