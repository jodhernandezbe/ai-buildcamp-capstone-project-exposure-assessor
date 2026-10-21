import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { KeysStatusResponse } from "../../types/workspace";
import { ApiKeyVaultModal } from "./ApiKeyVaultModal";

const KEY = "sk-test-0123456789abcdef"; // pragma: allowlist secret
const NONE = { configured: false };
const NO_KEYS: KeysStatusResponse = { openai: NONE, census: NONE, comptox: NONE };

function setup(overrides: Partial<Parameters<typeof ApiKeyVaultModal>[0]> = {}) {
  const props = {
    open: true,
    statuses: NO_KEYS,
    busy: null,
    error: null,
    onSave: vi.fn().mockResolvedValue(true),
    onClear: vi.fn().mockResolvedValue(true),
    onClose: vi.fn(),
    ...overrides,
  };
  render(<ApiKeyVaultModal {...props} />);
  return props;
}

const section = (label: string) => screen.getByRole("region", { name: `${label} API key` });

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

describe("ApiKeyVaultModal", () => {
  it("has a section per key, each saying what it is for, with a masked password input", () => {
    setup();
    for (const [label, purpose] of [
      ["OpenAI", "Runs the assistant"],
      ["Census", "Counts the people living around a facility"],
      ["CompTox", "Looks up chemical properties"],
    ] as const) {
      expect(section(label)).toHaveTextContent(purpose);
      expect(within(section(label)).getByLabelText(`${label} API key`)).toHaveAttribute(
        "type",
        "password",
      );
      expect(within(section(label)).getByRole("status")).toHaveTextContent("No key configured");
    }
  });

  it("shows the keychain badge, with no part of the key, for a stored key only", () => {
    setup({ statuses: { ...NO_KEYS, census: { configured: true } } });
    expect(within(section("Census")).getByRole("status")).toHaveTextContent(
      "Key stored securely in OS Keychain",
    );
    expect(within(section("OpenAI")).getByRole("status")).toHaveTextContent("No key configured");
  });

  it("saves a key under its own name, clears the input and never touches browser storage", async () => {
    const user = userEvent.setup();
    const props = setup();
    const input = within(section("OpenAI")).getByLabelText("OpenAI API key");
    await user.type(input, KEY);
    await user.click(within(section("OpenAI")).getByRole("button", { name: "Save OpenAI key" }));
    expect(props.onSave).toHaveBeenCalledWith("openai", KEY);
    expect(input).toHaveValue("");
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(KEY);
  });

  it("saves one key without touching what is typed for the others", async () => {
    const user = userEvent.setup();
    const props = setup();
    await user.type(within(section("Census")).getByLabelText("Census API key"), "census-key-1");
    await user.type(within(section("CompTox")).getByLabelText("CompTox API key"), "comptox-key-2");
    await user.click(within(section("Census")).getByRole("button", { name: "Save Census key" }));
    expect(props.onSave).toHaveBeenCalledOnce();
    expect(props.onSave).toHaveBeenCalledWith("census", "census-key-1");
    expect(within(section("CompTox")).getByLabelText("CompTox API key")).toHaveValue("comptox-key-2");
  });

  it("cannot save an empty key", () => {
    setup();
    for (const label of ["OpenAI", "Census", "CompTox"]) {
      expect(screen.getByRole("button", { name: `Save ${label} key` })).toBeDisabled();
    }
  });

  it("clears only the chosen key", async () => {
    const user = userEvent.setup();
    const stored = { configured: true };
    const props = setup({ statuses: { openai: stored, census: stored, comptox: NONE } });
    await user.click(screen.getByRole("button", { name: "Clear Census key" }));
    expect(props.onClear).toHaveBeenCalledExactlyOnceWith("census");
    expect(screen.getByRole("button", { name: "Clear CompTox key" })).toBeDisabled();
  });

  it("says which lookups are unavailable while an optional key is missing", () => {
    setup({ statuses: { ...NO_KEYS, comptox: { configured: true } } });
    expect(section("Census")).toHaveTextContent("fall back to a generic screening default");
    expect(section("CompTox")).not.toHaveTextContent("cannot be looked up");
    expect(section("OpenAI")).not.toHaveTextContent("Without it");
  });

  it("disables the actions while a key is being saved or cleared", () => {
    setup({ busy: "census", statuses: { ...NO_KEYS, openai: { configured: true } } });
    expect(screen.getByRole("button", { name: "Clear OpenAI key" })).toBeDisabled();
  });

  it("shows an error from the server", () => {
    setup({ error: "The OS keychain is unavailable." });
    expect(screen.getByRole("alert")).toHaveTextContent("keychain is unavailable");
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const props = setup();
    await user.type(within(section("OpenAI")).getByLabelText("OpenAI API key"), "sk-partial");
    await user.keyboard("{Escape}");
    expect(props.onClose).toHaveBeenCalledOnce();
  });
});
