import { render, screen } from "@testing-library/react";

import type { ChatMessage } from "../../hooks/chatState";
import { MessageStream } from "./MessageStream";

const assistant = (text: string, extra: Partial<ChatMessage> = {}): ChatMessage => ({
  id: "a",
  role: "assistant",
  text,
  error: null,
  streaming: false,
  tools: [],
  ...extra,
});

describe("MessageStream", () => {
  it("renders Markdown as formatted text", () => {
    render(<MessageStream messages={[assistant("**bold** and a list:\n\n- one\n- two")]} />);
    expect(screen.getByText("bold").tagName).toBe("STRONG");
    expect(screen.getAllByRole("listitem")).toHaveLength(3); // the message and its two items
  });

  it("never renders raw HTML from the assistant", () => {
    const { container } = render(
      <MessageStream messages={[assistant("<script>window.hacked = 1</script><img src=x onerror=alert(1)>")]} />,
    );
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(container).toHaveTextContent("<script>");
  });

  it("opens links in a new tab without leaking the opener", () => {
    render(<MessageStream messages={[assistant("[EPA](https://www.epa.gov)")]} />);
    const link = screen.getByRole("link", { name: "EPA" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("shows an inline alert for an error and a waiting hint while streaming", () => {
    render(
      <MessageStream
        messages={[
          assistant("", { streaming: true }),
          assistant("", { id: "b", error: "Add your OpenAI API key in Settings." }),
        ]}
      />,
    );
    expect(screen.getByText("Thinking…")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Add your OpenAI API key");
  });

  describe("tables", () => {
    const TABLE = "| CAS | Rate (g/s) | HQ |\n| --- | --- | --- |\n| 110-54-3 | 1.5 | 0.2 |\n| 71-43-2 | 2 | 1.1 |";

    it("renders a pipe table as a real table with header and body rows", () => {
      render(<MessageStream messages={[assistant(TABLE)]} />);
      expect(screen.getAllByRole("columnheader").map((cell) => cell.textContent)).toEqual([
        "CAS",
        "Rate (g/s)",
        "HQ",
      ]);
      expect(screen.getAllByRole("row")).toHaveLength(3); // header + two body rows
      expect(screen.getByRole("cell", { name: "110-54-3" })).toBeInTheDocument();
    });

    it("keeps each table in its own horizontal scroll area, with tabular numerals", () => {
      render(<MessageStream messages={[assistant(TABLE)]} />);
      const table = screen.getByRole("table");
      const wrapper = table.parentElement;
      expect(wrapper).toHaveClass("overflow-x-auto", "max-w-full");
      expect(table).toHaveClass("tabular-nums");
      expect(screen.getByRole("cell", { name: "1.5" })).toHaveClass("whitespace-nowrap");
    });

    it("lets the message shrink so a wide table scrolls instead of widening the chat", () => {
      const { container } = render(<MessageStream messages={[assistant(TABLE)]} />);
      expect(container.querySelector("li")).toHaveClass("min-w-0");
      expect(screen.getByRole("table").closest(".min-w-0")).not.toBeNull();
    });

    it("still shows raw HTML inside a table cell as text", () => {
      const { container } = render(
        <MessageStream messages={[assistant("| a |\n| - |\n| <script>x</script> |")]} />,
      );
      expect(container.querySelector("script")).toBeNull();
      expect(screen.getByRole("table")).toHaveTextContent("<script>x</script>");
    });
  });
});
