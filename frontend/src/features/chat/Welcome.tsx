import { BrandLogo } from "../../components/ui/BrandLogo";

/** The empty conversation: who the assistant is and what it can assess today. */
export function Welcome() {
  return (
    <header className="flex flex-col items-center gap-3 text-center">
      <BrandLogo size={48} compartments />
      <p className="max-w-sm text-sm text-fg2">
        Screening-level air exposure and risk: EPA release inventories (TRI, NEI, FRS), Gaussian plume
        dispersion, Census receptor demographics and read-across surrogates (MolDeBERTa and ECFP4), in a
        framework built to grow to water and soil.
      </p>
      <p className="text-sm text-fg2">Ask about a chemical, its releases or its exposure.</p>
    </header>
  );
}
