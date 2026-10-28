// Names the features use, re-exported from the generated contract (src/types/api.ts).
export type {
  AssistantMessage,
  ChatRequest,
  ConfirmationAnswers,
  ConfirmationPrompt,
  ConfirmationRequested,
  EntryAnswer,
  MissingValue,
  ClientConfig,
  Chemical,
  Dose,
  ErrorEvent,
  Extreme,
  Extremum,
  Facility,
  GuardrailPivotResponse,
  LayoutConfig,
  KeysStatusResponse,
  KeyStatusResponse,
  KeyUpdatePayload,
  Meteorology,
  ReadAcross,
  Receptors,
  RiskSummary,
  ScopeDecision,
  Screening,
  SessionDetailResponse,
  SessionStep,
  SessionsResponse,
  SessionSummary,
  SessionTurn,
  StreamEventSchema as StreamEvent,
  ThreadMessage,
  ThreadSnapshot,
  Token,
  Stack,
  ToolStatus,
  TurnFinished,
  TurnStarted,
  Usage,
  UsageTotals,
  WorkspaceState,
  WorkspaceUpdate,
} from "./api";

import type { Extremum, KeysStatusResponse } from "./api";

/** The keys the interface stores: the model key and the two service keys the tools use. */
export type KeyName = keyof KeysStatusResponse;

/** Risk position against the thresholds of concern. */
export type Status = Extremum["status"];
