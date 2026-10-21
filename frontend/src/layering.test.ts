// Imports flow one way: components -> features -> App. Shared primitives never import features.
const sources = import.meta.glob<string>("./components/**/*.{ts,tsx}", {
  query: "?raw",
  import: "default",
  eager: true,
});

describe("frontend layering", () => {
  it("finds the shared components", () => {
    expect(Object.keys(sources).length).toBeGreaterThan(0);
  });

  it.each(Object.entries(sources))("%s does not import features", (_path, source) => {
    expect(source).not.toMatch(/from\s+["'][^"']*features\//);
  });
});
