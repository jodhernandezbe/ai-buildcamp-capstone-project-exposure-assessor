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
});
