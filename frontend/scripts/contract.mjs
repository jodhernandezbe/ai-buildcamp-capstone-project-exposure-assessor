// Generate src/types/api.ts from src/types/schema.json (the export of api/schemas/), or
// check that the committed file matches (`--check`, used by `npm run check`).
import { readFileSync, writeFileSync } from "node:fs";
import { compileFromFile } from "json-schema-to-typescript";

const SCHEMA = new URL("../src/types/schema.json", import.meta.url).pathname;
const TARGET = new URL("../src/types/api.ts", import.meta.url).pathname;
const BANNER = "/* Generated from api/schemas/ by npm run gen:types. Do not edit. */";

const generated = await compileFromFile(SCHEMA, {
  bannerComment: BANNER,
  unreachableDefinitions: true,
  additionalProperties: false,
  cwd: new URL("../src/types/", import.meta.url).pathname,
});

if (process.argv.includes("--check")) {
  let current = "";
  try {
    current = readFileSync(TARGET, "utf8");
  } catch {
    // missing file counts as out of date
  }
  if (current !== generated) {
    console.error("src/types/api.ts is out of date. Run: npm run gen:types");
    process.exit(1);
  }
  console.log("contract types are current");
} else {
  writeFileSync(TARGET, generated);
  console.log("wrote src/types/api.ts");
}
