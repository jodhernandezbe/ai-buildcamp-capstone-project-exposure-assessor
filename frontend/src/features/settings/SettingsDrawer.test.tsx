import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { KeyOutcomes } from "../../hooks/useKeyStatus";
import type { KeysStatusResponse } from "../../types/workspace";
import { SettingsDrawer } from "./SettingsDrawer";

const KEY = "sk-test-0123456789abcdef"; // pragma: allowlist secret
const NONE = { configured: false };
const NO_KEYS: KeysStatusResponse = { openai: NONE, census: NONE, comptox: NONE };

function setup(overrides: Partial<Parameters<typeof SettingsDrawer>[0]> = {}) {
  const props = {
    open: true,
    statuses: NO_KEYS as KeysStatusResponse | null,
    busy: null,
    outcomes: {} as KeyOutcomes,
    loadError: null,
    onSave: vi.fn().mockResolvedValue(true),
    onClear: vi.fn().mockResolvedValue(true),
    onClose: vi.fn(),
    ...overrides,
  };
  render(<SettingsDrawer {...props} />);
  return props;
}

const section = (label: string) => screen.getByRole("region", { name: `${label} API key`, hidden: true });
const open = async (title: string) => {
  const button = screen.getByRole("button", { name: title });
  if (button.getAttribute("aria-expanded") === "false") await userEvent.click(button);
};

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe("SettingsDrawer", () => {
  it("renders nothing while closed", () => {
    setup({ open: false });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("groups the keys into Assistant and Data services sections", async () => {
    setup();
    await open("Data services");
    const assistant = screen.getByRole("region", { name: "Assistant" });
    const data = screen.getByRole("region", { name: "Data services" });
    expect(within(assistant).getByRole("region", { name: "OpenAI API key" })).toBeInTheDocument();
    expect(within(data).getByRole("region", { name: "Census API key" })).toBeInTheDocument();
    expect(within(data).getByRole("region", { name: "CompTox API key" })).toBeInTheDocument();
  });

  it("opens the Assistant section by itself while the OpenAI key is missing, and not otherwise", () => {
    setup();
    expect(screen.getByRole("button", { name: "Assistant" })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("button", { name: "Data services" })).toHaveAttribute("aria-expanded", "false");
  });

  it("starts collapsed when the OpenAI key is stored", () => {
    setup({ statuses: { ...NO_KEYS, openai: { configured: true } } });
    expect(screen.getByRole("button", { name: "Assistant" })).toHaveAttribute("aria-expanded", "false");
  });

  it("explains each key with a tooltip and masks the input", async () => {
    setup();
    await open("Data services");
    expect(screen.getByRole("button", { name: "About the Census key" })).toHaveAccessibleDescription(
      "Counts the people living around a facility.",
    );
    expect(within(section("Census")).getByLabelText("Census API key")).toHaveAttribute("type", "password");
  });

  it("shows the keychain status, with no part of the key, for a stored key only", async () => {
    setup({ statuses: { ...NO_KEYS, census: { configured: true } } });
    await open("Data services");
    expect(within(section("Census")).getByRole("status")).toHaveTextContent("Key stored securely in OS Keychain");
    expect(within(section("CompTox")).getByRole("status")).toHaveTextContent("No key configured");
  });

  it("says which lookups are unavailable while an optional key is missing", async () => {
    setup({ statuses: { ...NO_KEYS, openai: { configured: true } } });
    await open("Data services");
    expect(section("Census")).toHaveTextContent("population counts fall back");
    expect(section("CompTox")).toHaveTextContent("cannot be looked up");
  });

  it("saves under the key's own name, empties the input and never uses browser storage", async () => {
    const user = userEvent.setup();
    const props = setup();
    const input = within(section("OpenAI")).getByLabelText("OpenAI API key");
    expect(within(section("OpenAI")).getByRole("button", { name: "Save OpenAI key" })).toBeDisabled();
    await user.type(input, KEY);
    await user.click(within(section("OpenAI")).getByRole("button", { name: "Save OpenAI key" }));
    expect(props.onSave).toHaveBeenCalledWith("openai", KEY);
    expect(input).toHaveValue("");
    expect(localStorage.length + sessionStorage.length).toBe(0);
  });

  it("Reset and the input's clear control empty the draft without saving", async () => {
    const user = userEvent.setup();
    const props = setup();
    const input = within(section("OpenAI")).getByLabelText("OpenAI API key");
    await user.type(input, KEY);
    await user.click(within(section("OpenAI")).getByRole("button", { name: "Reset OpenAI key input" }));
    expect(input).toHaveValue("");
    await user.type(input, KEY);
    await user.click(within(section("OpenAI")).getByRole("button", { name: "Clear OpenAI key input" }));
    expect(input).toHaveValue("");
    expect(props.onSave).not.toHaveBeenCalled();
  });

  it("clears a stored key through the clear action only", async () => {
    const user = userEvent.setup();
    const props = setup({ statuses: { ...NO_KEYS, openai: { configured: true } } });
    await open("Assistant");
    await user.click(within(section("OpenAI")).getByRole("button", { name: "Clear OpenAI key" }));
    expect(props.onClear).toHaveBeenCalledWith("openai");
  });

  it("shows each key's own outcome: a success for one and an error for another", async () => {
    setup({
      outcomes: {
        openai: { kind: "success", message: "Key saved." },
        census: { kind: "error", message: "The key was not accepted." },
      },
    });
    await open("Data services");
    expect(within(section("OpenAI")).getByText("Key saved.")).toBeInTheDocument();
    expect(within(section("Census")).getByRole("alert")).toHaveTextContent("The key was not accepted.");
    expect(within(section("CompTox")).queryByRole("alert")).toBeNull();
  });

  it("disables the actions while a request runs", () => {
    setup({ busy: "openai" });
    expect(within(section("OpenAI")).getByRole("button", { name: "Save OpenAI key" })).toBeDisabled();
  });

  it("shows a load error and closes with Escape", async () => {
    const user = userEvent.setup();
    const props = setup({ loadError: "Could not reach the server." });
    expect(screen.getByRole("alert")).toHaveTextContent("Could not reach the server.");
    await user.keyboard("{Escape}");
    expect(props.onClose).toHaveBeenCalled();
  });
});
