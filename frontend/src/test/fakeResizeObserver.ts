// jsdom has no ResizeObserver: observers are recorded so a test can report a size change.
export const resizeObservers = new Set<StubResizeObserver>();

export class StubResizeObserver {
  callback: ResizeObserverCallback;
  targets = new Set<Element>();

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
    resizeObservers.add(this);
  }

  observe(target: Element): void {
    this.targets.add(target);
  }

  unobserve(target: Element): void {
    this.targets.delete(target);
  }

  disconnect(): void {
    this.targets.clear();
    resizeObservers.delete(this);
  }

  /** Report that every observed element changed size. */
  fire(): void {
    this.callback([], this as unknown as ResizeObserver);
  }
}
