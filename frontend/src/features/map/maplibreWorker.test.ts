describe("maplibreWorker", () => {
  it("points MapLibre at the worker file the bundler emits, as soon as it is imported", async () => {
    vi.resetModules();
    const maplibre = await import("maplibre-gl");
    const { workerUrl } = await import("./maplibreWorker");
    expect(workerUrl).toMatch(/maplibre-gl-worker\.mjs/);
    expect(maplibre.setWorkerUrl).toHaveBeenCalledWith(workerUrl);
  });
});
