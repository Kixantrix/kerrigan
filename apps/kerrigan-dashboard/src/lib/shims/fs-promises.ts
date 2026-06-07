export const readFile = async (): Promise<never> => {
  throw new Error("Node fs is unavailable in browser preview builds");
};

export const readdir = async (): Promise<never> => {
  throw new Error("Node fs is unavailable in browser preview builds");
};
