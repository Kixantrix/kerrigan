const unavailable = async (): Promise<never> => {
  throw new Error("Node fs is unavailable in browser preview builds");
};

export const promises = {
  readFile: unavailable,
};

const fs = { promises };

export default fs;
