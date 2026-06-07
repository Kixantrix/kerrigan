const path = {
  join: (...parts: string[]): string => parts.filter(Boolean).join("/"),
};

export default path;
